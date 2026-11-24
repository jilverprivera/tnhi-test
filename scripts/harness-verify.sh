#!/usr/bin/env bash
# Docket verification harness: lint + tests in small, serialized batches with a RAM guard.
#
# Usage:
#   ./scripts/harness-verify.sh [--backend|--frontend|--e2e|--all] [--changed | --full | <test paths...>] [--batch N]
#
#   --backend / --frontend / --e2e / --all   target (default: --all = backend + frontend,
#                                            plus e2e specs only when they changed)
#   --changed   (default) tests mapped from files changed vs HEAD (+ untracked)
#   --full      whole suite, still chunked; only when the user explicitly asks
#   <paths>     explicit test files/dirs (repo-relative, e.g. backend/tests/shared/test_x.py)
#   --batch N   test files per batch (default 3)
#
# Environment:
#   DOCKET_MIN_FREE_MEM_PCT   minimum free memory % before each batch (default 15)
#   DOCKET_RAM_RETRIES        waits before aborting when memory is low (default 6)
#   DOCKET_RAM_WAIT_SEC       seconds per wait (default 10)
#   DOCKET_LOCK_TIMEOUT_SEC   max wait for a runner lock (default 600)
#   DOCKET_CHANGED_MINUTES    outside git, files modified in the last N minutes count as changed (default 120)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKEND_DIR="${REPO_ROOT}/backend"
FRONTEND_DIR="${REPO_ROOT}/frontend"

MIN_FREE_PCT="${DOCKET_MIN_FREE_MEM_PCT:-15}"
RAM_RETRIES="${DOCKET_RAM_RETRIES:-6}"
RAM_WAIT_SEC="${DOCKET_RAM_WAIT_SEC:-10}"
LOCK_TIMEOUT_SEC="${DOCKET_LOCK_TIMEOUT_SEC:-600}"
CHANGED_MINUTES="${DOCKET_CHANGED_MINUTES:-120}"
LOCK_ROOT="${TMPDIR:-/tmp}"
LOCK_ROOT="${LOCK_ROOT%/}/docket-locks"

TARGET="all"
MODE="changed"
BATCH_SIZE=3
EXPLICIT_PATHS=()

HELD_LOCKS=()
SUMMARY=()
FAILED=0

log() { printf '[harness-verify] %s\n' "$*"; }
die() { printf '[harness-verify] ERROR: %s\n' "$*" >&2; exit 2; }

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend) TARGET="backend" ;;
    --frontend) TARGET="frontend" ;;
    --e2e) TARGET="e2e" ;;
    --all) TARGET="all" ;;
    --changed) MODE="changed" ;;
    --full) MODE="full" ;;
    --batch)
      [[ $# -ge 2 ]] || die "--batch needs a number"
      BATCH_SIZE="$2"
      shift
      ;;
    -h|--help) usage; exit 0 ;;
    -*) die "unknown option: $1" ;;
    *) EXPLICIT_PATHS+=("$1"); MODE="explicit" ;;
  esac
  shift
done

[[ "${BATCH_SIZE}" =~ ^[1-9][0-9]*$ ]] || die "--batch must be a positive integer"

release_locks() {
  local lock
  for lock in "${HELD_LOCKS[@]+"${HELD_LOCKS[@]}"}"; do
    rm -rf "${lock}" 2>/dev/null || true
  done
  HELD_LOCKS=()
}
trap release_locks EXIT
trap 'release_locks; exit 130' INT TERM

acquire_lock() {
  local runner="$1"
  local lockdir="${LOCK_ROOT}/${runner}.lock"
  local waited=0
  mkdir -p "${LOCK_ROOT}"
  while ! mkdir "${lockdir}" 2>/dev/null; do
    local owner=""
    owner="$(cat "${lockdir}/pid" 2>/dev/null || true)"
    if [[ -n "${owner}" ]] && ! kill -0 "${owner}" 2>/dev/null; then
      log "removing stale ${runner} lock (pid ${owner} is gone)"
      rm -rf "${lockdir}"
      continue
    fi
    if (( waited >= LOCK_TIMEOUT_SEC )); then
      die "timed out after ${LOCK_TIMEOUT_SEC}s waiting for the ${runner} lock (${lockdir}, pid ${owner:-unknown})"
    fi
    if (( waited % 30 == 0 )); then
      log "waiting for the ${runner} lock held by pid ${owner:-unknown}..."
    fi
    sleep 5
    waited=$(( waited + 5 ))
  done
  echo "$$" > "${lockdir}/pid"
  HELD_LOCKS+=("${lockdir}")
}

release_lock() {
  local runner="$1"
  local lockdir="${LOCK_ROOT}/${runner}.lock"
  local kept=() lock
  rm -rf "${lockdir}" 2>/dev/null || true
  for lock in "${HELD_LOCKS[@]+"${HELD_LOCKS[@]}"}"; do
    [[ "${lock}" == "${lockdir}" ]] || kept+=("${lock}")
  done
  HELD_LOCKS=("${kept[@]+"${kept[@]}"}")
}

free_mem_pct() {
  if [[ -r /proc/meminfo ]]; then
    awk '/^MemTotal:/ {t=$2} /^MemAvailable:/ {a=$2} END { if (t > 0) printf "%d", a * 100 / t }' /proc/meminfo
    return
  fi
  if command -v memory_pressure >/dev/null 2>&1; then
    local pct
    pct="$(memory_pressure -Q 2>/dev/null | awk -F': ' '/free percentage/ {gsub("%", "", $2); print $2}' || true)"
    if [[ -n "${pct}" ]]; then
      printf '%s' "${pct}"
      return
    fi
  fi
  if command -v vm_stat >/dev/null 2>&1 && command -v sysctl >/dev/null 2>&1; then
    local page_size total_bytes
    page_size="$(sysctl -n hw.pagesize 2>/dev/null || echo 4096)"
    total_bytes="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
    vm_stat | awk -v ps="${page_size}" -v tb="${total_bytes}" '
      /Pages free/ {gsub("\\.", "", $3); f=$3}
      /Pages inactive/ {gsub("\\.", "", $3); i=$3}
      /Pages speculative/ {gsub("\\.", "", $3); s=$3}
      END { if (tb > 0) printf "%d", (f + i + s) * ps * 100 / tb }'
    return
  fi
  printf ''
}

ram_guard() {
  local attempt=0 pct
  while true; do
    pct="$(free_mem_pct)"
    if [[ -z "${pct}" ]]; then
      log "warning: could not read free memory; continuing without the RAM guard"
      return 0
    fi
    if (( pct >= MIN_FREE_PCT )); then
      return 0
    fi
    attempt=$(( attempt + 1 ))
    if (( attempt > RAM_RETRIES )); then
      die "free memory ${pct}% is below ${MIN_FREE_PCT}% after ${RAM_RETRIES} waits; close other processes or raise DOCKET_MIN_FREE_MEM_PCT consciously"
    fi
    log "free memory ${pct}% < ${MIN_FREE_PCT}%; waiting ${RAM_WAIT_SEC}s (${attempt}/${RAM_RETRIES})"
    sleep "${RAM_WAIT_SEC}"
  done
}

changed_files() {
  if git -C "${REPO_ROOT}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    {
      git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null || git -C "${REPO_ROOT}" diff --name-only
      git -C "${REPO_ROOT}" ls-files --others --exclude-standard
    } | sort -u
  else
    log "not a git repository: treating files modified in the last ${CHANGED_MINUTES} minutes as changed" >&2
    (
      cd "${REPO_ROOT}"
      find backend frontend -type f -mmin "-${CHANGED_MINUTES}" \
        -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/__pycache__/*' \
        -not -path '*/.next/*' -not -path '*/.pytest_cache/*' -not -path '*/.ruff_cache/*' \
        2>/dev/null || true
    ) | sort -u
  fi
}

find_backend_tests_in() {
  local dir="$1"
  [[ -d "${REPO_ROOT}/${dir}" ]] || return 0
  (cd "${REPO_ROOT}" && find "${dir}" -type f -name 'test_*.py' -not -path '*/__pycache__/*' | sort)
}

find_frontend_tests_in() {
  local dir="$1"
  [[ -d "${REPO_ROOT}/${dir}" ]] || return 0
  (cd "${REPO_ROOT}" && find "${dir}" -type f \( -name '*.test.ts' -o -name '*.test.tsx' \) \
    -not -path '*/node_modules/*' | sort)
}

map_backend_file() {
  local file="$1" rest slice
  case "${file}" in
    backend/tests/*/test_*.py|backend/tests/test_*.py)
      [[ -f "${REPO_ROOT}/${file}" ]] && echo "${file}"
      ;;
    backend/app/features/*)
      rest="${file#backend/app/features/}"
      slice="${rest%%/*}"
      find_backend_tests_in "backend/tests/features/${slice}"
      find_backend_tests_in "backend/tests/golden"
      ;;
    backend/app/shared/*)
      find_backend_tests_in "backend/tests/shared"
      find_backend_tests_in "backend/tests/golden"
      ;;
    backend/app/mcp/*)
      find_backend_tests_in "backend/tests/mcp"
      ;;
    backend/app/*.py)
      (cd "${REPO_ROOT}" && find backend/tests -maxdepth 1 -type f -name 'test_*.py' 2>/dev/null | sort)
      ;;
  esac
  return 0
}

map_frontend_file() {
  local file="$1" rest feature
  case "${file}" in
    frontend/src/*.test.ts|frontend/src/*.test.tsx)
      [[ -f "${REPO_ROOT}/${file}" ]] && echo "${file}"
      ;;
    frontend/src/features/*)
      rest="${file#frontend/src/features/}"
      feature="${rest%%/*}"
      find_frontend_tests_in "frontend/src/features/${feature}"
      ;;
    frontend/src/shared/*)
      find_frontend_tests_in "frontend/src/shared"
      ;;
  esac
  return 0
}

BACKEND_TESTS=""
FRONTEND_TESTS=""
E2E_SPECS=""
BACKEND_LINT_FILES=""
BACKEND_CHANGED=0
FRONTEND_CHANGED=0

collect_changed() {
  local file
  while IFS= read -r file; do
    [[ -n "${file}" ]] || continue
    case "${file}" in
      backend/*)
        BACKEND_CHANGED=1
        if [[ "${file}" == *.py && -f "${REPO_ROOT}/${file}" ]]; then
          BACKEND_LINT_FILES+="${file#backend/}"$'\n'
        fi
        BACKEND_TESTS+="$(map_backend_file "${file}")"$'\n'
        ;;
      frontend/e2e/*)
        FRONTEND_CHANGED=1
        if [[ "${file}" == *.spec.ts && -f "${REPO_ROOT}/${file}" ]]; then
          E2E_SPECS+="${file}"$'\n'
        fi
        ;;
      frontend/*)
        FRONTEND_CHANGED=1
        FRONTEND_TESTS+="$(map_frontend_file "${file}")"$'\n'
        ;;
    esac
  done < <(changed_files)
}

collect_full() {
  BACKEND_CHANGED=1
  FRONTEND_CHANGED=1
  BACKEND_TESTS="$(find_backend_tests_in backend/tests)"
  FRONTEND_TESTS="$(find_frontend_tests_in frontend/src)"
  E2E_SPECS="ALL"
}

collect_explicit() {
  local path
  for path in "${EXPLICIT_PATHS[@]}"; do
    path="${path#./}"
    [[ -e "${REPO_ROOT}/${path}" ]] || die "path not found: ${path}"
    case "${path}" in
      backend/*) BACKEND_CHANGED=1; BACKEND_TESTS+="${path}"$'\n' ;;
      frontend/e2e*) FRONTEND_CHANGED=1; E2E_SPECS+="${path}"$'\n' ;;
      frontend/*) FRONTEND_CHANGED=1; FRONTEND_TESTS+="${path}"$'\n' ;;
      *) die "explicit paths must start with backend/ or frontend/: ${path}" ;;
    esac
  done
}

unique_lines() {
  printf '%s' "$1" | sed '/^$/d' | sort -u
}

run_batches() {
  local runner="$1" workdir="$2" strip_prefix="$3" list="$4"
  shift 4
  local cmd=("$@")
  local batch=() file total batch_no=0
  total="$(printf '%s\n' "${list}" | sed '/^$/d' | wc -l | tr -d ' ')"
  if [[ "${total}" == "0" ]]; then
    SUMMARY+=("${runner}: no tests selected")
    return 0
  fi
  log "${runner}: ${total} test file(s) in batches of ${BATCH_SIZE}"
  acquire_lock "${runner}"
  flush() {
    [[ ${#batch[@]} -gt 0 ]] || return 0
    batch_no=$(( batch_no + 1 ))
    ram_guard
    log "${runner} batch ${batch_no}: ${batch[*]}"
    if (cd "${workdir}" && "${cmd[@]}" "${batch[@]}"); then
      SUMMARY+=("${runner} batch ${batch_no}: PASS (${batch[*]})")
      batch=()
    else
      SUMMARY+=("${runner} batch ${batch_no}: FAIL (${batch[*]})")
      FAILED=1
      release_lock "${runner}"
      return 1
    fi
  }
  while IFS= read -r file; do
    [[ -n "${file}" ]] || continue
    batch+=("${file#"${strip_prefix}"}")
    if (( ${#batch[@]} >= BATCH_SIZE )); then
      flush || return 1
    fi
  done <<< "${list}"
  flush || return 1
  release_lock "${runner}"
}

frontend_ready() {
  [[ -f "${FRONTEND_DIR}/package.json" ]]
}

lint_backend() {
  local files=()
  local file
  if [[ "${MODE}" == "full" ]]; then
    files=(".")
  else
    while IFS= read -r file; do
      [[ -n "${file}" ]] && files+=("${file}")
    done < <(unique_lines "${BACKEND_LINT_FILES}")
  fi
  if [[ ${#files[@]} -eq 0 ]]; then
    SUMMARY+=("ruff: no changed Python files")
    return 0
  fi
  log "ruff check: ${files[*]}"
  if (cd "${BACKEND_DIR}" && uv run ruff check "${files[@]}"); then
    SUMMARY+=("ruff: PASS")
  else
    SUMMARY+=("ruff: FAIL")
    FAILED=1
    return 1
  fi
}

lint_frontend() {
  log "pnpm lint"
  if (cd "${FRONTEND_DIR}" && pnpm lint); then
    SUMMARY+=("pnpm lint: PASS")
  else
    SUMMARY+=("pnpm lint: FAIL")
    FAILED=1
    return 1
  fi
}

run_backend() {
  [[ -d "${BACKEND_DIR}" ]] || { SUMMARY+=("backend: directory missing, skipped"); return 0; }
  if [[ "${BACKEND_CHANGED}" -eq 0 ]]; then
    SUMMARY+=("backend: no changes, skipped")
    return 0
  fi
  if [[ "${MODE}" != "explicit" ]]; then
    lint_backend || return 1
  fi
  run_batches pytest "${BACKEND_DIR}" "backend/" "$(unique_lines "${BACKEND_TESTS}")" \
    uv run pytest -q -p no:cacheprovider
}

run_frontend() {
  if ! frontend_ready; then
    SUMMARY+=("frontend: frontend/package.json not found yet, skipped")
    return 0
  fi
  if [[ "${FRONTEND_CHANGED}" -eq 0 ]]; then
    SUMMARY+=("frontend: no changes, skipped")
    return 0
  fi
  if [[ "${MODE}" != "explicit" ]]; then
    lint_frontend || return 1
  fi
  run_batches jest "${FRONTEND_DIR}" "frontend/" "$(unique_lines "${FRONTEND_TESTS}")" \
    pnpm exec jest --maxWorkers=1
}

run_e2e() {
  if ! frontend_ready; then
    SUMMARY+=("e2e: frontend/package.json not found yet, skipped")
    return 0
  fi
  local specs
  if [[ "${E2E_SPECS}" == "ALL" ]]; then
    log "playwright: full suite, workers=1"
    acquire_lock playwright
    ram_guard
    if (cd "${FRONTEND_DIR}" && pnpm exec playwright test --workers=1); then
      SUMMARY+=("playwright (full): PASS")
    else
      SUMMARY+=("playwright (full): FAIL")
      FAILED=1
    fi
    release_lock playwright
    return 0
  fi
  specs="$(unique_lines "${E2E_SPECS}")"
  if [[ -z "${specs}" ]]; then
    SUMMARY+=("e2e: no changed specs (run --e2e --full before closing a UI flow change)")
    return 0
  fi
  run_batches playwright "${FRONTEND_DIR}" "frontend/" "${specs}" \
    pnpm exec playwright test --workers=1
}

case "${MODE}" in
  changed) collect_changed ;;
  full) collect_full ;;
  explicit) collect_explicit ;;
esac

log "target=${TARGET} mode=${MODE} batch=${BATCH_SIZE} min_free_mem=${MIN_FREE_PCT}%"

case "${TARGET}" in
  backend) run_backend || true ;;
  frontend) run_frontend || true ;;
  e2e) run_e2e || true ;;
  all)
    run_backend || true
    if [[ "${FAILED}" -eq 0 ]]; then run_frontend || true; fi
    if [[ "${FAILED}" -eq 0 ]]; then run_e2e || true; fi
    ;;
esac

echo
log "summary"
for line in "${SUMMARY[@]+"${SUMMARY[@]}"}"; do
  printf '  - %s\n' "${line}"
done

if [[ "${FAILED}" -ne 0 ]]; then
  log "FAILED"
  exit 1
fi
log "OK"
