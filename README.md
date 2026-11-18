# PDFObfuscator

Redact unwanted text from an MBH monthly bank statement while keeping the
account details and three selected transactions readable. Processing runs locally
and creates a separate PDF; the original file is never modified.

This tool supports one specific MBH statement layout. It is an independent project
and is not affiliated with MBH Bank or PRÉMIUM Egészségpénztár.

## AI-generated code

All code in this repository was generated entirely with AI, guided by human
requirements and review.

## Purpose: Családi Kassza repayment evidence

MBH Bank is a Hungarian bank, and this project's main purpose is to prepare
redacted repayment evidence for PRÉMIUM Egészségpénztár's **Családi Kassza /
Otthonkassza–Hitelkönnyítő program**.
The service lets eligible borrowers or co-borrowers use their health-fund balance
to cover all or part of their monthly housing mortgage repayment, within the
program's limits.
After a claim is accepted, monthly repayment evidence must identify the member,
repayment date, paying bank account, amount paid, and loan contract reference;
see the [official service description](https://premiumegeszsegpenztar.hu/csaladi-kassza-szolgaltatasok).
This tool prepares that supporting evidence while hiding unrelated text;
acceptance of a redacted document is determined by PRÉMIUM.

## What the output contains

- The first page, with its bank details, account details, postal address, and
  transaction column headings (including the opening balance) left visible.
- Every page containing one of exactly three transactions with your chosen
  reference ID, with the complete matching entries left visible.
- Permanent black boxes over other text on the retained pages. White backgrounds,
  logos, and table lines remain visible, and content stays in its original position.

Pages without matching transactions are removed, except for the first page.
The output is a new, image-only PDF: text cannot be selected or searched without
OCR. Original page dimensions are preserved; visible page numbers are not renumbered.

## Requirements

- Python **3.11 or newer**; CI is configured for Python 3.11 and 3.12 on Windows
  and Linux.
- A text-based MBH statement matching the [supported layout](#supported-layout).
- An output directory on a filesystem supporting hard links, such as NTFS or
  ext4. The tool uses a hard link to publish the completed file without overwriting
  an existing destination.

Dependencies are pinned in [requirements.txt](requirements.txt). Rendering uses
PDFium; no external Poppler installation is required. Dependency installation
needs internet access; statement processing makes no network requests.

## Quick start

Download or clone this repository, then open a terminal in its root directory.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src/pdf_obfuscator.py statement.pdf output/pdf/redacted.pdf --transaction-id EXAMPLE123
```

### Linux or macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python src/pdf_obfuscator.py statement.pdf output/pdf/redacted.pdf --transaction-id EXAMPLE123
```

Replace `statement.pdf` and `EXAMPLE123` with your local file and reference ID.
The example ID is synthetic. Quote paths that contain spaces. You do not need to
activate the virtual environment when using its Python executable directly.

The destination must not already exist. On success, the command prints the
retained original page numbers and exits with status `0`; failures return `1`.
Argument syntax errors return `2`. Run with `--help` to see the CLI usage.

## Command options

```text
python src/pdf_obfuscator.py INPUT OUTPUT --transaction-id ID [--dpi DPI]
```

| Argument | Meaning |
| --- | --- |
| `INPUT` | Path to the original statement. Opened for reading only. |
| `OUTPUT` | New PDF path. Parent directories are created after layout and match validation. |
| `--transaction-id ID` | Required ASCII alphanumeric reference found in exactly three distinct transactions. |
| `--dpi DPI` | Image resolution from 150 to 600; default 300. Lower values reduce size and detail. |

Matching requires a complete ID, so `EXAMPLE1234` does not match `EXAMPLE123`.
Repeated occurrences within one transaction count as one matching transaction.
The count is fixed at three; it is not currently configurable.

## Supported layout

The parser expects unrotated, text-based **595 x 842 pt** pages with the specific
MBH first-page headings, two transaction date columns, and horizontal row rules
used by this profile. Coordinates are defined in
[src/pdf_obfuscator.py](src/pdf_obfuscator.py).

Scanned PDFs, other banks or templates, and selected entries without a complete
row boundary (including transactions continuing across pages) are unsupported.
Recognized layout or count mismatches stop processing rather than produce a
partial result. Other template changes may evade these checks: review every
output page before sharing it.

## How redaction works

1. Read the source into memory, validate the layout, and find the three entries.
2. Render the retained pages and burn black boxes into their pixels over unwanted
   text, combining extracted word bounds with PDFium glyph bounds.
3. Embed only the completed images in a fresh PDF using lossless compression.
4. Check the page count and absence of extractable text, annotations, and selected
   interactive document objects; confirm the source SHA-256 is unchanged.
5. Publish the completed output without replacing an existing file.

No source text layer, attachments, metadata, or original PDF object streams are
copied. Output metadata is generic. Temporary PDFs contain the redacted output
and are removed on normal completion or handled failure; abrupt termination may
leave a `.redacted-*.pdf` file in the destination directory.

**Only text is redacted.** Graphics, logos, and images remain visible. Private
information embedded in a picture, QR code, or vector drawing is outside this
profile. The first-page account details, address, and opening balance are
intentionally retained, so the output is not anonymous.

## Troubleshooting

| Message or symptom | Action |
| --- | --- |
| `Expected exactly 3 matching transactions` | Check the complete reference ID and number of distinct entries. No output is published. |
| `no complete, unambiguous row` | A matching entry has unsupported boundaries or crosses pages. Use a supported layout. |
| `does not match the supported MBH layout` | The first-page template differs from this profile. |
| `Output already exists` | Choose a new destination filename. |
| Hard-link or filesystem error | Use a local output folder on a filesystem supporting hard links; check write permissions. |
| Missing module | Install `requirements.txt` using the same Python executable used to run the tool. |

## Development

```powershell
.venv\Scripts\python.exe -m unittest discover -s tests -v
```

On Linux or macOS, use `.venv/bin/python` instead. Tests generate synthetic PDFs
in temporary directories; no bank statement is needed. They cover page selection,
preserved pixels, blacked-out text, font-metric differences, attachments, match
counts, unsupported inputs, and source/overwrite protection.

See [CONTRIBUTING.md](CONTRIBUTING.md) for changes and bug reports,
[SECURITY.md](SECURITY.md) for redaction concerns, and
[docs/PUBLISHING.md](docs/PUBLISHING.md) for GitHub publication preparation.

## License

No license is granted for this project's code or documentation. The repository
is intentionally unlicensed; public visibility does not grant general permission
to use, modify, or redistribute it. Third-party dependencies retain their own
licenses. An open-source license may be added only by the copyright holder.
