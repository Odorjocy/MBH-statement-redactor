# Contributing

Start with the [README](README.md) for installation, the supported statement
profile, and CLI examples. The project is currently unlicensed; opening the
repository to public viewing does not change its licensing status.

## Discuss and reproduce

Describe the behavior you want to change and the expected result. For a bug,
include the Python version, operating system, command with synthetic filenames
and IDs, and sanitized error output. Use a synthetic reproduction created in
code. Never attach a real statement, account reference, extracted financial text,
or screenshot containing personal information to an issue or pull request.

Redaction leaks should follow [SECURITY.md](SECURITY.md).

## Make a change

1. Create a focused branch from `main`, such as `fix/row-boundary-validation`
   or `docs/cli-examples`.
2. Follow PEP 8 with four-space indentation, `snake_case` functions, and
   `PascalCase` classes. No formatter or linter is configured.
3. Add synthetic regression cases in `tests/test_redaction.py` for changes to
   parsing, rendering, or document handling. Generate fixtures in temporary
   directories instead of committing PDFs.
4. Update the README when the CLI, supported profile, or dependencies change.
5. Run `python -m unittest discover -s tests -v` in your virtual environment and
   `git diff --check` before submitting.

Changes to keep regions or masking must verify both preserved pixels and removal
of unwanted text. Preserve source and destination overwrite protection. Reject
ambiguous selected rows rather than expand the visible region to guess at them.

## Pull requests

Use imperative, focused commit subjects, such as `Fix transaction boundary check`.
Explain the problem, resulting behavior, and validation results. Link an issue
when one exists. Mention layout assumptions and any remaining limitations.
Synthetic before-and-after examples are useful for rendering changes.

Review `git diff --cached` before committing. PDF files, local inputs and outputs,
screenshots, secrets, and virtual environments belong outside Git. Ignore rules
help with accidental additions but can be bypassed with `git add -f`.
