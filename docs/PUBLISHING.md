# Preparing a public GitHub repository

## Review the publication tree

1. Run the synthetic suite with `python -m unittest discover -s tests -v` in the
   virtual environment, and run `git diff --check`.
2. Review all proposed files with `git status --short`, `git diff`, and
   `git diff --cached`. Check examples, error logs, filenames, and commit metadata
   for private information.
3. Confirm `git ls-files -- '*.pdf' '*.PDF'` returns nothing. The ignore pattern
   also covers mixed-case extensions. Keep real statements and rendered previews
   local; do not add them to issues, releases, or workflow artifacts.
4. Retain the explicit unlicensed status unless the copyright holder chooses
   a license. No `LICENSE` file is currently supplied.

## Publish a clean snapshot

Earlier local commits contain a real transaction reference in a README example.
The public documentation uses synthetic examples, but editing a file does not
remove its old content from Git history. Do not push the existing history as-is.

After reviewing and committing the sanitized publication files, export **that
commit** and initialize a separate repository. This preserves the local working
repository and keeps its old history out of the public repository.

The following PowerShell example uses a new staging directory. Run it from the
reviewed repository after the publication changes have been committed:

```powershell
# Choose a new, empty location outside the working repository.
$publishRoot = Join-Path $env:TEMP ('PDFObfuscator-public-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $publishRoot | Out-Null
$archivePath = Join-Path $publishRoot 'source.zip'
$sourcePath = Join-Path $publishRoot 'source'
git archive --format=zip --output=$archivePath HEAD
if ($LASTEXITCODE -ne 0) { throw 'Export failed' }
Expand-Archive -LiteralPath $archivePath -DestinationPath $sourcePath
Set-Location -LiteralPath $sourcePath
git init -b main
if ($LASTEXITCODE -ne 0) { throw 'Initialization failed' }
git add -- .
git diff --cached --stat
git ls-files -- '*.pdf' '*.PDF'
# Review the staged snapshot before creating the public initial commit.
git commit -m "Add PDFObfuscator"
```

`git archive` exports tracked files from the committed tree only; it does not
copy ignored files, uncommitted edits, `.git`, or earlier commits. Check the
exported snapshot and the chosen Git author identity before uploading it.
History rewriting is an alternative, but requires a separate, reviewed operation.

## Configure GitHub

Create an empty repository under the intended owner. Use `main` as its default
branch. From the clean snapshot repository, add the GitHub URL as `origin` and
push `main` after the final review. Do not use a mirror push from the local
development repository.

Suggested description: "Local CLI for text redaction of a specific MBH bank
statement layout, preserving account details and three matching transactions."

The repository includes a test workflow for push and pull-request events, a bug
report template, and a pull-request template. After the first push:

- Confirm Actions can install the pinned dependencies and all matrix jobs pass.
- Enable private vulnerability reporting if available; update `SECURITY.md`
  when a private contact channel is established.
- Configure branch protection for `main` and require successful tests before
  merging, if that fits the project's maintenance workflow.
- Review GitHub's repository visibility and author identity before making it public.

Publication itself is a separate action. No remote URL or repository owner is
hard-coded into the project.
