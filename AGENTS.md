# Repository Guidelines

## Project Structure & Module Organization

This repository currently contains no application code, tests, assets, or build configuration. Keep this guide aligned with the implementation as it develops.

When adding the initial implementation, organize production code under `src/`, automated tests under `tests/`, and synthetic PDF fixtures under `tests/fixtures/`. Place developer utilities in `scripts/` and usage documentation in `README.md`. Prefer small modules with a single responsibility.

## Build, Test, and Development Commands

No build system, dependency manager, or runnable entry point is configured yet. There are currently no supported build, test, lint, or local-run commands.

When introducing tooling, document exact setup and execution commands in `README.md` and update this section. Run commands from the repository root, pin dependencies using the selected ecosystem's lockfile, and avoid undocumented machine-specific setup.

## Coding Style & Naming Conventions

Follow the conventions of the language selected for the implementation. Use consistent indentation within each file, descriptive names, and short functions. Keep formatting-only changes separate from behavioral changes.

Add formatter and linter configuration alongside the first source files. Document naming rules and executable checks here once those tools exist.

## Testing Guidelines

No testing framework or coverage threshold is established. Add automated tests alongside new behavior and document how to run them. Name tests after the behavior they verify.

For PDF processing, cover malformed inputs, output readability, and verification that targeted content cannot be recovered through text extraction. Use synthetic fixtures without personal or confidential information.

## Commit & Pull Request Guidelines

No Git history is available to establish existing conventions. Use concise, imperative commit subjects, such as `Add PDF input validation`, and keep commits focused.

Pull requests should explain the change, link relevant issues, and report validation commands and results. Include before-and-after examples for output changes, using sanitized documents.
