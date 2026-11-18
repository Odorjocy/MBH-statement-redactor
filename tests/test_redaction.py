"""Synthetic documents only: never add real bank statements to fixtures."""

from io import BytesIO
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pdfplumber
from PIL import ImageChops
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pdf_obfuscator import Region, StatementError, masked_image, redact  # noqa: E402
import pypdfium2 as pdfium


TARGET = "TEST123"


def fixture(path: Path, identifiers=None, unterminated=False):
    if identifiers is None:
        identifiers = [TARGET, TARGET, "PRIVATE999", TARGET, "PRIVATE888"]
    buffer = BytesIO()
    doc = canvas.Canvas(buffer, pagesize=(595, 842))

    def text(x, top, value, size=8):
        doc.setFont("Helvetica", size)
        doc.drawString(x, 842 - top - size * 0.793, value)

    text(408, 14, "SZÁMLAKIVONAT", 20)
    text(35, 114, "ADATOK", 14)
    text(35, 160, "APPROVED ACCOUNT DETAILS")
    text(35, 271, "GYORS", 14)
    text(35, 300, "SECRET SUMMARY")
    text(35, 407.5, "TRANZAKCIÓK", 14)
    text(38.64, 425.5, "Értéknap")
    text(81.8, 433.68, "nap")
    text(360, 414, "OPENING BALANCE 123")
    text(125, 500, "SECRET FIRST PAGE TRANSACTION")
    doc.showPage()
    text(35, 80, "TRANZAKCIÓK", 14)
    text(35, 20, "SECRET REPEATED HEADER")
    for index, identifier in enumerate(identifiers):
        top = 120 + 40 * index
        text(38.64, top, "2026.10.12")
        text(81.8, top, "2026.10.12")
        text(125.63, top, f"Transaction {index}")
        text(500, top, f"{index + 1} 000(-)")
        text(125.63, top + 9, f"Reference: {identifier}")
        if not unterminated:
            doc.line(38.24, 842 - top - 21, 558.4, 842 - top - 21)
    doc.showPage()
    text(35, 50, "SECRET DROPPED PAGE")
    doc.save()
    # Include document-level secrets to exercise the fresh-document boundary.
    writer = PdfWriter()
    writer.append(PdfReader(BytesIO(buffer.getvalue())))
    writer.add_metadata({"/Title": "SECRET METADATA"})
    writer.add_attachment("secret.txt", b"SECRET ATTACHMENT")
    with path.open("wb") as stream:
        writer.write(stream)


class RedactionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.source = Path(self.directory.name) / "source.pdf"
        self.output = Path(self.directory.name) / "redacted.pdf"
        fixture(self.source)

    def test_preserves_allowed_pixels_and_removes_all_other_content(self):
        before = self.source.read_bytes()
        self.assertEqual(redact(self.source, self.output, TARGET, 150), [1, 2])
        self.assertEqual(self.source.read_bytes(), before)
        reader = PdfReader(self.output)
        self.assertEqual(len(reader.pages), 2)
        self.assertNotIn("/Names", reader.root_object)
        self.assertNotIn("SECRET", str(reader.metadata))
        self.assertEqual([p.extract_text() for p in reader.pages], ["", ""])
        with pdfplumber.open(self.source) as original:
            # Inspect the actual embedded output bitmap, not extracted text only.
            for index in range(2):
                embedded = reader.pages[index].images[0].image.convert("RGB")
                source = original.pages[index].to_image(
                    resolution=150, antialias=True, force_mediabox=True
                ).original.convert("RGB")
                sx, sy = source.width / 595, source.height / 842

                def crop(image, box):
                    x0, y0, x1, y1 = box
                    return image.crop((int(x0 * sx), int(y0 * sy),
                                       int(x1 * sx), int(y1 * sy)))

                allowed = [(30, 20, 560, 250), (30, 408, 560, 441)] if index == 0 else [
                    (30, 120, 560, 138), (30, 160, 560, 178), (30, 240, 560, 258)
                ]
                for box in allowed:
                    self.assertIsNone(ImageChops.difference(crop(embedded, box), crop(source, box)).getbbox())
                # Every unwanted word is solid black, including edge pixels.
                forbidden_words = [w for w in original.pages[index].extract_words()
                                   if (index == 0 and 270 <= w["top"] <= 510)
                                   or (index == 1 and (w["top"] < 110
                                       or 199 <= w["top"] <= 220
                                       or 279 <= w["top"] <= 300))]
                if index == 0:
                    forbidden_words = [w for w in forbidden_words
                                       if not 405 <= w["top"] <= 442]
                self.assertTrue(forbidden_words)
                for word in forbidden_words:
                    box = (word["x0"], word["top"], word["x1"], word["bottom"])
                    self.assertIsNone(crop(embedded, box).getbbox(), word["text"])
                # Background and row separators must survive outside keep regions.
                preserved = [(30, 330, 560, 390), (30, 550, 560, 800)] if index == 0 else [
                    (30, 225, 560, 235), (30, 219, 560, 223), (0, 350, 595, 800)
                ]
                for box in preserved:
                    self.assertIsNone(ImageChops.difference(crop(embedded, box), crop(source, box)).getbbox())

    def test_wrong_counts_and_partial_ids_create_no_output(self):
        for identifiers in ([TARGET] * 2, [TARGET] * 4,
                            [TARGET, TARGET, TARGET + "9"], ["OTHER"] * 3):
            with self.subTest(identifiers=identifiers):
                fixture(self.source, identifiers)
                with self.assertRaisesRegex(StatementError, "exactly 3"):
                    redact(self.source, self.output, TARGET, 150)
                self.assertFalse(self.output.exists())

    def test_renderer_bounds_cover_incorrect_extracted_font_widths(self):
        with pdfplumber.open(self.source) as pdf, pdfium.PdfDocument(self.source) as rendered:
            page = pdf.pages[0]
            words = page.extract_words()
            summary = next(w for w in words if w["text"] == "SUMMARY")
            # Simulate the understated word widths in the Oracle statement.
            inaccurate = [dict(w, x1=w["x0"] + 1) for w in words]
            with patch.object(page, "extract_words", return_value=inaccurate):
                rendered_page = rendered[0]
                text_page = rendered_page.get_textpage()
                try:
                    image = masked_image(page, [Region(0, 0, 595, 265)], 150, text_page)
                finally:
                    text_page.close()
                    rendered_page.close()
            sx, sy = image.width / 595, image.height / 842
            # The word's far end must still be fully black despite bad metrics.
            box = (int((summary["x1"] - 3) * sx), int((summary["top"] + 2) * sy),
                   int((summary["x1"] - 1) * sx), int((summary["bottom"] - 2) * sy))
            self.assertIsNone(image.crop(box).getbbox())

    def test_repeated_id_in_one_transaction_counts_as_one_entry(self):
        fixture(self.source, [TARGET + " " + TARGET, TARGET])
        with self.assertRaisesRegex(StatementError, "found 2"):
            redact(self.source, self.output, TARGET, 150)

    def test_incomplete_rows_fail_closed(self):
        fixture(self.source, [TARGET] * 3, unterminated=True)
        with self.assertRaisesRegex(StatementError, "unambiguous row"):
            redact(self.source, self.output, TARGET, 150)
        self.assertFalse(self.output.exists())

    def test_never_overwrites_source_or_existing_destination(self):
        before = self.source.read_bytes()
        with self.assertRaisesRegex(StatementError, "different files"):
            redact(self.source, self.source, TARGET)
        self.output.write_bytes(b"existing output")
        with self.assertRaisesRegex(StatementError, "already exists"):
            redact(self.source, self.output, TARGET)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(self.output.read_bytes(), b"existing output")

    def test_invalid_pdf_and_layout_create_no_output(self):
        self.source.write_bytes(b"not a PDF")
        with self.assertRaises(Exception):
            redact(self.source, self.output, TARGET)
        self.assertFalse(self.output.exists())
        doc = canvas.Canvas(str(self.source), pagesize=(612, 792))
        doc.drawString(20, 20, "Unsupported template")
        doc.save()
        with self.assertRaisesRegex(StatementError, "MBH statements"):
            redact(self.source, self.output, TARGET)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
