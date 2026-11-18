# Repository Guidelines

## Project Structure & Module Organization

`src/pdf_obfuscator.py` contains the MBH statement parser, region selection, permanent raster redaction, and command-line entry point. `tests/test_redaction.py` generates synthetic PDF fixtures in temporary directories. `README.md` documents usage and layout limitations; `requirements.txt` pins dependencies. Generated documents belong under `output/pdf/` and inspection files under `tmp/pdfs/`; both are ignored by Git.

## Build, Test, and Development Commands

Use Python 3.11 or newer. Run commands from the repository root:

- `py -m venv .venv`: create a virtual environment.
- `.venv\Scripts\python.exe -m pip install -r requirements.txt`: install pinned dependencies.
- `.venv\Scripts\python.exe src/pdf_obfuscator.py input.pdf output/pdf/redacted.pdf --transaction-id EXAMPLE123`: retain exactly three matching entries.
- `.venv\Scripts\python.exe -m unittest discover -s tests -v`: run regression tests.

## Coding Style & Naming Conventions

Follow PEP 8, four-space indentation, `snake_case` functions, and `PascalCase` classes. Use descriptive names and short functions. No formatter or linter is configured. Keep formatting-only changes separate from behavioral changes.

## Testing Guidelines

Use standard-library `unittest`, with `test_*.py` files and behavior-oriented `test_*` methods. No numerical coverage threshold is established. Cover malformed inputs, exact transaction counts, output readability, permanent removal, and source preservation. Compare bitmap regions as well as extracted text. Use synthetic fixtures without personal or confidential information.

## Commit & Pull Request Guidelines

Follow the existing imperative commit style, such as `Add repository contributor guidelines`. Keep commits focused.

Pull requests should explain the change, link relevant issues, and report validation commands and results. Include before-and-after examples for output changes, using sanitized documents.

## Data Handling

Never commit real statements, private screenshots, or extracted account data. Never overwrite source PDFs. Changed layouts and ambiguous transaction boundaries must fail closed rather than reveal additional content.

## Public Documentation

Use synthetic IDs and filenames in examples. Follow `CONTRIBUTING.md` and `SECURITY.md`; publication steps are in `docs/PUBLISHING.md`. The project is intentionally unlicensed. CI runs synthetic tests on Windows and Linux with Python 3.11 and 3.12. Review history before publication: ignore rules do not remove previously committed private information.
