# Security and privacy

PDFObfuscator handles financial documents locally. The first-page account and
address details and three selected transactions are intentionally visible in the
output. All non-text graphics remain visible. Review the supported profile and
each generated document before sharing it.

## Reporting a redaction problem

Do not post real statements, account identifiers, personal details, or leaked
text in a public issue, pull request, or Actions log.

If the GitHub repository's Security tab offers **Report a vulnerability**, use
that private channel. Otherwise, open an issue requesting a private reporting
channel without disclosing the vulnerability or any financial information.
Private reporting must be enabled by the repository owner after publication;
no private contact address is configured in this repository.

When a private channel is available, provide the affected revision, Python and
dependency versions, a description of the unexpected exposure, and a synthetic
reproducer where possible. Keep original documents local.

## Scope and maintenance

Security fixes target the current `main` branch. There is no release support
schedule or guaranteed response time. Image-embedded information, changed bank
templates, OCR, and transaction continuations across pages are outside the
current supported profile. A matching ID count alone is not a full privacy check.

The tool emits a new image-only PDF and checks that source bytes are unchanged.
It does not encrypt output, securely erase files, or validate the accuracy or
authenticity of the financial records. Install dependencies in a virtual
environment, and keep source documents in an access-controlled local folder.
