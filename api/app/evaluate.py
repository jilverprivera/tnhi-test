"""Evaluation: compares the system's proposals with the expected results, field by field.

    uv run python -m app.evaluate --data-dir /tmp/docket-eval --ai off|on|compare [--set blind] [--json out.json]

--ai off      rules only (the figures in the deliverables).
--ai on       rules + the assisted classifier (needs TAC_LLM_ENABLED, TAC_ANTHROPIC_API_KEY, TAC_LLM_MODEL).
--ai compare  both runs on the same mailbox, side by side, plus every document whose outcome changed.

Two references: the client's partial file (material/4-para-medirte/esperado-parcial.csv, 8 documents)
and the full table decided for the remaining documents (tests/golden/esperado-completo.csv, 17).
A document sent to human review counts as "routed to a person", not as an error, only when the
expected result could not be reached automatically (e.g. a scan without OCR).
"""

import argparse
import csv
import json
import shutil
from datetime import date
from pathlib import Path

from app.container import Container
from app.shared.config import MATERIAL, Settings
from app.shared.infrastructure.client_vocabulary import (
    CLIENT_CODE_TO_DEPARTMENT,
    CLIENT_LABEL_TO_DOCUMENT_TYPE,
)

PARTIAL = MATERIAL / "4-para-medirte" / "esperado-parcial.csv"
FULL = Path(__file__).resolve().parents[1] / "tests" / "golden" / "esperado-completo.csv"
BLIND_DIR = Path(__file__).resolve().parents[1] / "tests" / "blind"
BLIND = BLIND_DIR / "esperado-ciego.csv"
CLIENT_ACTIONS = {"Radicar": "FILE", "Devolver": "RETURN_TO_SENDER", "No radicar": "DO_NOT_FILE"}
FIELDS = ("document_type", "department", "action", "due_date")


def _rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _normalize(row: dict, client_vocabulary: bool) -> dict:
    if client_vocabulary:
        return {
            "document_type": CLIENT_LABEL_TO_DOCUMENT_TYPE[row["tipo"]].value,
            "department": CLIENT_CODE_TO_DEPARTMENT[row["dependencia"]].value,
            "action": CLIENT_ACTIONS[row["accion"]],
            "due_date": row["vence"] or None,
        }
    return {
        "document_type": row["tipo"],
        "department": row["dependencia"],
        "action": row["accion"],
        "due_date": row["vence"] or None,
    }


def _find(items, email_file: str, document: str):
    for item in items:
        doc = item.proposal.document
        if doc.email_file == email_file and (
            doc.name == document or document.startswith("(cuerpo")
        ):
            return item
    return None


def evaluate(container: Container, references=None) -> dict:
    items = container.list_inbox()
    report = {"references": {}}
    references = references or (("client_partial", PARTIAL, True), ("full_table", FULL, False))
    for name, path, client in references:
        results = []
        for row in _rows(path):
            item = _find(items, row["correo"], row["documento"])
            if item is None:
                results.append(
                    {
                        "email": row["correo"],
                        "document": row["documento"],
                        "outcome": "MISSING",
                        "needs_review": False,
                        "matches": dict.fromkeys(FIELDS, False),
                        "expected": _normalize(row, client),
                        "actual": None,
                        "reasons": [],
                    }
                )
                continue
            expected = _normalize(row, client)
            d = item.decision
            actual = {
                "document_type": d.document_type.value,
                "department": d.department.value,
                "action": d.action.value,
                "due_date": d.due_date.isoformat() if d.due_date else None,
            }
            matches = {f: actual[f] == expected[f] for f in FIELDS}
            outcome = (
                "CORRECT"
                if all(matches.values())
                else ("ROUTED_TO_PERSON" if d.needs_review else "WRONG")
            )
            results.append(
                {
                    "email": row["correo"],
                    "document": row["documento"],
                    "outcome": outcome,
                    "needs_review": d.needs_review,
                    "matches": matches,
                    "expected": expected,
                    "actual": actual,
                    "reasons": d.reason_codes(),
                }
            )
        per_field = {f: sum(r["matches"][f] for r in results) for f in FIELDS}
        report["references"][name] = {
            "documents": len(results),
            "correct": sum(r["outcome"] == "CORRECT" for r in results),
            "routed_to_person": sum(r["outcome"] == "ROUTED_TO_PERSON" for r in results),
            "wrong": sum(r["outcome"] in ("WRONG", "MISSING") for r in results),
            "per_field": per_field,
            "results": results,
        }
    report["ocr_available"] = shutil.which("tesseract") is not None
    report["needs_review_total"] = sum(1 for i in items if i.decision.needs_review)
    report["documents_total"] = len(items)
    report["date"] = date.today().isoformat()
    return report


class RecordingClassifier:
    """Counts what the assisted classifier was asked and answered. Only the suggested type is kept:
    the text it saw may hold personal data (it was masked before leaving, but stays out of reports)."""

    def __init__(self, inner):
        self._inner = inner
        self.enabled = inner.enabled
        self.answers: list[str | None] = []

    def suggest_type(self, text: str, subject: str):
        suggestion = self._inner.suggest_type(text, subject)
        self.answers.append(suggestion.value if suggestion else None)
        return suggestion


def run(data_dir: Path, evaluation_set: str, with_ai: bool) -> dict:
    overrides = {"data_dir": data_dir, "database_url": f"sqlite:///{data_dir / 'tac.db'}"}
    overrides |= {"worker_enabled": False, "llm_enabled": with_ai}
    if evaluation_set == "blind":
        overrides["inbox_dir"] = BLIND_DIR / "emails"
    settings = Settings(**overrides)
    if with_ai and not settings.assisted_classification_ready():
        raise SystemExit(
            "--ai on needs TAC_LLM_ENABLED, TAC_ANTHROPIC_API_KEY and TAC_LLM_MODEL in api/.env"
        )
    data_dir.mkdir(parents=True, exist_ok=True)
    container = Container(settings)
    recorder = RecordingClassifier(container.assisted_classifier)
    container.assisted_classifier = recorder  # before the pipeline is built (cached_property)
    container.bootstrap()
    inbox = sorted(settings.require("inbox_dir").glob("*.eml"))
    container.import_emails([(p.name, p.read_bytes()) for p in inbox], actor="EVALUATION")
    references = (("blind", BLIND, False),) if evaluation_set == "blind" else None
    report = evaluate(container, references)
    report["ai"] = {
        "enabled": with_ai,
        "model": settings.llm_model if with_ai else None,
        "calls": len(recorder.answers),
        "useful_answers": sum(a is not None for a in recorder.answers),
        "suggested_types": sorted({a for a in recorder.answers if a}),
    }
    return report


def print_report(label: str, report: dict) -> None:
    ai = report["ai"]
    print(f"== {label} ==")
    for name, ref in report["references"].items():
        print(
            f"{name}: {ref['correct']}/{ref['documents']} correct, {ref['routed_to_person']} routed to a person, "
            f"{ref['wrong']} wrong · per field {ref['per_field']}"
        )
        for r in ref["results"]:
            if r["outcome"] != "CORRECT":
                print(f"  {r['email']} {r['document']}: {r['outcome']} {r['reasons']}")
    print(
        f"OCR available: {report['ocr_available']} · needs review: {report['needs_review_total']}/{report['documents_total']}"
        f" · AI calls: {ai['calls']} ({ai['useful_answers']} usable)"
    )


def compare(without_ai: dict, with_ai: dict) -> dict:
    """Per reference: the totals of both runs and every document whose outcome changed."""
    comparison = {}
    for name, base in without_ai["references"].items():
        other = with_ai["references"][name]
        before = {(r["email"], r["document"]): r for r in base["results"]}
        changed = [
            {
                "email": r["email"],
                "document": r["document"],
                "without_ai": before[(r["email"], r["document"])]["outcome"],
                "with_ai": r["outcome"],
                "actual_with_ai": r["actual"],
            }
            for r in other["results"]
            if before[(r["email"], r["document"])]["outcome"] != r["outcome"]
        ]
        comparison[name] = {
            key: {"without_ai": base[key], "with_ai": other[key]}
            for key in ("correct", "routed_to_person", "wrong")
        } | {"changed": changed}
    return comparison


def print_comparison(comparison: dict, ai_calls: int) -> None:
    print("== Rules only vs rules + AI ==")
    for name, c in comparison.items():
        totals = " · ".join(
            f"{key} {c[key]['without_ai']} -> {c[key]['with_ai']}"
            for key in ("correct", "routed_to_person", "wrong")
        )
        print(f"{name}: {totals}")
        for d in c["changed"]:
            print(f"  {d['email']} {d['document']}: {d['without_ai']} -> {d['with_ai']}")
        if not c["changed"]:
            print("  no document changed its outcome")
    print(f"AI calls: {ai_calls} (only documents the rules found ambiguous are sent)")


def main() -> None:
    parser = argparse.ArgumentParser(prog="evaluate")
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--json", type=Path)
    parser.add_argument("--set", choices=("golden", "blind"), required=True)
    parser.add_argument("--ai", choices=("off", "on", "compare"), required=True)
    args = parser.parse_args()

    if args.ai == "compare":
        without_ai = run(args.data_dir / "without-ai", args.set, with_ai=False)
        with_ai = run(args.data_dir / "with-ai", args.set, with_ai=True)
        print_report("Rules only", without_ai)
        print_report(f"Rules + AI ({with_ai['ai']['model']})", with_ai)
        comparison = compare(without_ai, with_ai)
        print_comparison(comparison, with_ai["ai"]["calls"])
        output = {"without_ai": without_ai, "with_ai": with_ai, "comparison": comparison}
    else:
        output = run(args.data_dir, args.set, with_ai=args.ai == "on")
        print_report("Rules + AI" if args.ai == "on" else "Rules only", output)
    if args.json:
        args.json.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
