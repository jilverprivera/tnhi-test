"""Text extraction adapters, one per file format.

OCR runs locally (Tesseract): no document leaves TAC's infrastructure.
"""

import io
import shutil

import pdfplumber
import pypdfium2
from docx import Document as DocxDocument
from openpyxl import load_workbook
from PIL import Image

from app.features.ingestion.domain.email_message import ExtractedText
from app.features.ingestion.infrastructure.eml_reader import html_to_text

# A PDF with less text per page than this is treated as scanned
_MIN_CHARS_PER_PAGE = 40
_OCR_DPI = 300


def _extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


class TesseractOcr:
    def __init__(self, language: str = "spa"):
        self.language = language

    @property
    def available(self) -> bool:
        return shutil.which("tesseract") is not None

    def _read_image(self, image: Image.Image) -> tuple[str, float]:
        import pytesseract

        data = pytesseract.image_to_data(
            image, lang=self.language, output_type=pytesseract.Output.DICT
        )
        scores = [
            float(c) for c, t in zip(data["conf"], data["text"]) if t.strip() and float(c) >= 0
        ]
        text = pytesseract.image_to_string(image, lang=self.language)
        return text, (sum(scores) / len(scores) if scores else 0.0)

    def read(self, images: list[Image.Image]) -> ExtractedText:
        if not self.available or not images:
            return ExtractedText(text="", method="OCR_UNAVAILABLE", ocr_confidence=0.0)
        texts, scores = zip(*(self._read_image(im) for im in images))
        return ExtractedText(
            text="\n".join(texts), method="OCR", ocr_confidence=round(sum(scores) / len(scores), 1)
        )


class PdfExtractor:
    def __init__(self, ocr: TesseractOcr):
        self.ocr = ocr

    def supports(self, mime_type: str, filename: str) -> bool:
        return mime_type == "application/pdf" or _extension(filename) == "pdf"

    def extract(self, content: bytes) -> ExtractedText:
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            pages = len(pdf.pages)
            text = "\n".join((p.extract_text() or "") for p in pdf.pages).strip()
        if len(text) >= _MIN_CHARS_PER_PAGE * max(pages, 1):
            return ExtractedText(text=text, method="PDF_TEXT")
        # Scanned PDF: render every page and run OCR
        pdf_doc = pypdfium2.PdfDocument(content)
        images = [pdf_doc[i].render(scale=_OCR_DPI / 72).to_pil() for i in range(len(pdf_doc))]
        return self.ocr.read(images)


class ImageExtractor:
    def __init__(self, ocr: TesseractOcr):
        self.ocr = ocr

    def supports(self, mime_type: str, filename: str) -> bool:
        return mime_type.startswith("image/") or _extension(filename) in (
            "png",
            "jpg",
            "jpeg",
            "tif",
            "tiff",
        )

    def extract(self, content: bytes) -> ExtractedText:
        return self.ocr.read([Image.open(io.BytesIO(content))])


class DocxExtractor:
    def supports(self, mime_type: str, filename: str) -> bool:
        return _extension(filename) == "docx" or "wordprocessingml" in mime_type

    def extract(self, content: bytes) -> ExtractedText:
        doc = DocxDocument(io.BytesIO(content))
        parts = [p.text for p in doc.paragraphs]
        for table in doc.tables:
            parts += [" ".join(cell.text for cell in row.cells) for row in table.rows]
        return ExtractedText(text="\n".join(parts).strip(), method="DOCX")


class XlsxExtractor:
    def supports(self, mime_type: str, filename: str) -> bool:
        return _extension(filename) == "xlsx" or "spreadsheetml" in mime_type

    def extract(self, content: bytes) -> ExtractedText:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
        rows = [
            " ".join(str(v) for v in row if v is not None)
            for sheet in workbook.worksheets
            for row in sheet.iter_rows(values_only=True)
        ]
        return ExtractedText(text="\n".join(r for r in rows if r), method="XLSX")


class HtmlExtractor:
    def supports(self, mime_type: str, filename: str) -> bool:
        return mime_type == "text/html" or _extension(filename) in ("html", "htm")

    def extract(self, content: bytes) -> ExtractedText:
        return ExtractedText(text=html_to_text(content.decode("utf-8", "replace")), method="HTML")


class PlainTextExtractor:
    def supports(self, mime_type: str, filename: str) -> bool:
        return mime_type.startswith("text/") or _extension(filename) in ("txt", "csv")

    def extract(self, content: bytes) -> ExtractedText:
        return ExtractedText(text=content.decode("utf-8", "replace").strip(), method="PLAIN_TEXT")


def default_extractors() -> list:
    ocr = TesseractOcr()
    return [
        PdfExtractor(ocr),
        ImageExtractor(ocr),
        DocxExtractor(),
        XlsxExtractor(),
        HtmlExtractor(),
        PlainTextExtractor(),
    ]
