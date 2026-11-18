# PDFObfuscator

Create a separate, permanently redacted copy of an MBH monthly bank statement.
The supported profile retains the first-page bank/account/address section and
transaction heading (including its opening balance), plus exactly three complete
transactions containing a specified ID. Other pages are dropped; unwanted text
on retained pages is covered by permanent black boxes. White backgrounds, logos,
and table lines remain visible. Original page sizes and content positions remain.

## Setup and usage

Use Python 3.10 or newer. From the repository root:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src/pdf_obfuscator.py kivonat.pdf output/pdf/kivonat-redacted.pdf --transaction-id 01D62639020
```

On systems with `python` instead of the Windows `py` launcher, use
`python -m venv .venv`. No external Poppler installation is required by the tool.

The output filename must be new. The program rejects the source path as an
output, refuses to overwrite any existing output, and stops if it does not find
exactly three distinct matching transactions. Matching uses a complete ID, so a
longer ID sharing the same prefix does not match. Use `--dpi 150` to reduce file
size; the default is 300, with a supported range of 150-600.

## Redaction and supported layout

The tool renders retained pages and burns black boxes into the bitmap over every
word outside the allowed regions, with padding to cover glyph edges. It combines
extracted word bounds with the renderer's glyph bounds to handle font-metric
differences in Oracle-generated statements. It embeds
the finished bitmaps in a fresh PDF using lossless compression. It copies no
source text layer, annotations, attachments, metadata, or PDF object streams.
The output is image-only: visible text is readable but cannot be selected or
searched without OCR. The original is read only and its SHA-256 is checked again
before the verified output is published. Temporary files contain redacted output
only and are removed on normal completion or failure.

The profile is specific to the supplied MBH template: text-based, unrotated
595 x 842 pt pages, with the expected first-page headings, two transaction date
columns, and horizontal row separators. Scans, changed first-page layouts, and
selected transactions without a complete row boundary (including page-spanning
entries) are rejected. Non-text graphics remain visible; this profile assumes
private data is text, as in the supplied statement. This is not a universal
bank-statement parser. Visually
review the output when using another month's statement.

## Development and tests

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests generate synthetic PDFs in temporary directories. They check preserved
pixels, blacked-out regions, removal of text and attachments, page selection,
exact match counts, incomplete rows, invalid inputs, and overwrite protection.
No formatter or linter is configured. Follow PEP 8 with four-space indentation,
`snake_case` functions, and `PascalCase` classes.

Real PDFs and generated output are ignored by Git. Do not commit bank statements,
screenshots containing personal data, or extracted statement text.
