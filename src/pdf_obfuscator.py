"""Create an image-only, permanently redacted copy of an MBH statement."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from io import BytesIO
import math
import os
from pathlib import Path
import re
import sys
import tempfile

import pdfplumber
import pypdfium2 as pdfium
from PIL import Image, ImageDraw
from pypdf import PdfReader
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


class StatementError(ValueError):
    """The input cannot be safely processed with the supported layout."""


@dataclass(frozen=True)
class Region:
    left: float
    top: float
    right: float
    bottom: float


@dataclass(frozen=True)
class Transaction:
    page: int
    region: Region
    text: str


@dataclass
class Plan:
    regions: dict[int, list[Region]]
    matches: list[Transaction]


DATE = re.compile(r"\d{4}\.\d{2}\.\d{2}")


def one_word(words: list[dict], text: str) -> dict:
    found = [word for word in words if word["text"] == text]
    if len(found) != 1:
        raise StatementError(f"Expected exactly one {text!r} heading on page 1.")
    return found[0]


def first_page_regions(page) -> list[Region]:
    """Recognize the approved MBH A4 header and transaction heading regions."""
    words = page.extract_words()
    title = one_word(words, "SZÁMLAKIVONAT")
    account = one_word(words, "ADATOK")
    summary = one_word(words, "GYORS")
    transactions = one_word(words, "TRANZAKCIÓK")
    value_date = one_word(words, "Értéknap")
    day = [w for w in words if w["text"] == "nap"
           and value_date["top"] < w["top"] < value_date["top"] + 15]
    # This profile intentionally fails closed on a different statement template.
    expected = [(title, 14, 3), (account, 114, 3), (summary, 271, 3),
                (transactions, 407.5, 3), (value_date, 425.5, 3)]
    if any(abs(w["top"] - top) > tolerance for w, top, tolerance in expected):
        raise StatementError("Page 1 does not match the supported MBH layout.")
    if len(day) != 1:
        raise StatementError("Cannot identify the transaction column header.")
    return [Region(0, 8.8, page.width, 265),
            Region(29, transactions["top"] - 2, 567, day[0]["bottom"] + 1)]


def page_transactions(page, page_index: int) -> list[Transaction]:
    """Use the two date columns and full-width row rules to delimit entries.

    Continuations across pages are rejected if selected; unrecognized matching
    text is also rejected by build_plan instead of retaining an ambiguous area.
    """
    words = page.extract_words()
    if not any(w["text"] == "TRANZAKCIÓK" for w in words):
        return []
    rules = sorted({line["top"] for line in page.lines
                    if abs(line["top"] - line["bottom"]) < 0.2
                    and abs(line["x0"] - 38.24) < 1
                    and abs(line["x1"] - 558.4) < 1})
    starts = []
    for word in words:
        if not DATE.fullmatch(word["text"]) or abs(word["x0"] - 38.64) > 2:
            continue
        paired = [w for w in words if DATE.fullmatch(w["text"])
                  and abs(w["x0"] - 81.8) <= 2
                  and abs(w["top"] - word["top"]) < 1]
        if len(paired) == 1:
            starts.append(word["top"])
    starts.sort()
    entries = []
    for index, top in enumerate(starts):
        next_top = starts[index + 1] if index + 1 < len(starts) else page.height
        bottom_rules = [y for y in rules if top < y < next_top]
        if not bottom_rules:
            continue  # No safe ending: an ID here will fail the coverage check.
        bottom = min(bottom_rules)
        contents = [w for w in words if top - 0.5 <= w["top"] < bottom]
        if any(w["bottom"] > bottom or w["x0"] < 29 or w["x1"] > 567
               for w in contents):
            raise StatementError(f"Ambiguous transaction boundary on page {page_index + 1}.")
        entries.append(Transaction(page_index, Region(29, top - 2, 567, bottom + 0.2),
                                   " ".join(w["text"] for w in contents)))
    return entries


def build_plan(pdf, transaction_id: str) -> Plan:
    if not re.fullmatch(r"[A-Za-z0-9]+", transaction_id):
        raise StatementError("Transaction ID must contain only ASCII letters and digits.")
    if not pdf.pages:
        raise StatementError("The input PDF has no pages.")
    for page in pdf.pages:
        if abs(page.width - 595) > 0.5 or abs(page.height - 842) > 0.5 or page.rotation:
            raise StatementError("Only unrotated 595 x 842 pt MBH statements are supported.")
    regions = {0: first_page_regions(pdf.pages[0])}
    pattern = re.compile(r"(?<![A-Za-z0-9])" + re.escape(transaction_id) + r"(?![A-Za-z0-9])")
    matches = []
    for page_index, page in enumerate(pdf.pages):
        full_count = len(pattern.findall(page.extract_text() or ""))
        entries = page_transactions(page, page_index)
        selected = [entry for entry in entries if pattern.search(entry.text)]
        covered_count = sum(len(pattern.findall(entry.text)) for entry in selected)
        if full_count != covered_count:
            raise StatementError(
                f"An ID occurrence on page {page_index + 1} has no complete, unambiguous row."
            )
        matches.extend(selected)
        for entry in selected:
            regions.setdefault(page_index, []).append(entry.region)
    if len(matches) != 3:
        raise StatementError(f"Expected exactly 3 matching transactions; found {len(matches)}.")
    return Plan(regions, matches)


def masked_image(page, regions: list[Region], dpi: int, text_page) -> Image.Image:
    source = page.to_image(resolution=dpi, antialias=True, force_mediabox=True).original.convert("RGB")
    result = source.copy()
    draw = ImageDraw.Draw(result)
    sx, sy = source.width / page.width, source.height / page.height
    words = page.extract_words()
    # Oracle PDFs can report font advances that differ from rendered glyphs.
    # Cover BOTH extraction bounds and the renderer's actual text rectangles.
    for index in range(text_page.count_rects()):
        left, bottom, right, top = text_page.get_rect(index)
        words.append({"x0": left, "top": page.height - top,
                      "x1": right, "bottom": page.height - bottom})
    for word in words:
        if any(region.left <= word["x0"] and word["x1"] <= region.right
               and region.top <= word["top"] and word["bottom"] <= region.bottom
               for region in regions):
            continue
        # Expand around glyphs and round outward to cover antialiased edges.
        padding = 0.8
        box = (max(0, math.floor((word["x0"] - padding) * sx)),
               max(0, math.floor((word["top"] - padding) * sy)),
               min(source.width, math.ceil((word["x1"] + padding) * sx)),
               min(source.height, math.ceil((word["bottom"] + padding) * sy)))
        draw.rectangle((box[0], box[1], box[2] - 1, box[3] - 1), fill="black")
    source.close()
    return result


def verify_output(path: Path, expected_pages: int) -> None:
    reader = PdfReader(path)
    if len(reader.pages) != expected_pages:
        raise StatementError("Output verification failed: incorrect page count.")
    if any(key in reader.root_object for key in ("/AcroForm", "/Names", "/OpenAction", "/Outlines")):
        raise StatementError("Output verification failed: unexpected document objects.")
    for page in reader.pages:
        if page.extract_text().strip() or page.get("/Annots"):
            raise StatementError("Output verification failed: unexpected text or annotations.")
        objects = page["/Resources"].get("/XObject", {})
        if len(objects) != 1 or any(obj.get_object().get("/Subtype") != "/Image"
                                    for obj in objects.values()):
            raise StatementError("Output verification failed: expected one flattened image per page.")


def redact(input_path: Path, output_path: Path, transaction_id: str, dpi: int = 300) -> list[int]:
    input_path, output_path = input_path.resolve(), output_path.resolve()
    if input_path == output_path or (output_path.exists() and os.path.samefile(input_path, output_path)):
        raise StatementError("Input and output must be different files.")
    if output_path.exists():
        raise StatementError("Output already exists; choose a new filename.")
    if not 150 <= dpi <= 600:
        raise StatementError("DPI must be between 150 and 600.")
    original = input_path.read_bytes()
    digest = hashlib.sha256(original).digest()
    temporary = None
    try:
        with pdfplumber.open(BytesIO(original)) as pdf, pdfium.PdfDocument(original) as rendered:
            plan = build_plan(pdf, transaction_id)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fd, name = tempfile.mkstemp(prefix=".redacted-", suffix=".pdf", dir=output_path.parent)
            os.close(fd)
            temporary = Path(name)
            document = canvas.Canvas(str(temporary), pageCompression=1, invariant=1)
            document.setTitle("Redacted statement")
            document.setAuthor("")
            document.setSubject("")
            document.setCreator("PDFObfuscator")
            for index, regions in sorted(plan.regions.items()):
                page = pdf.pages[index]
                rendered_page = rendered[index]
                text_page = rendered_page.get_textpage()
                try:
                    image = masked_image(page, regions, dpi, text_page)
                finally:
                    text_page.close()
                    rendered_page.close()
                document.setPageSize((page.width, page.height))
                document.drawImage(ImageReader(image), 0, 0, width=page.width, height=page.height)
                document.showPage()
                image.close()
            document.save()
        verify_output(temporary, len(plan.regions))
        if hashlib.sha256(input_path.read_bytes()).digest() != digest:
            raise StatementError("The source changed during processing; output was not published.")
        # Atomic publication without replacing an existing file, including races.
        os.link(temporary, output_path)
        return [index + 1 for index in sorted(plan.regions)]
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Original text-based MBH statement")
    parser.add_argument("output", type=Path, help="New output path (must not exist)")
    parser.add_argument("--transaction-id", required=True, help="Exact ID to keep in exactly three entries")
    parser.add_argument("--dpi", type=int, default=300, help="Output resolution, 150-600 (default: 300)")
    args = parser.parse_args()
    try:
        pages = redact(args.input, args.output, args.transaction_id, args.dpi)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Created {args.output}; retained original pages {', '.join(map(str, pages))}; 3 matching transactions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
