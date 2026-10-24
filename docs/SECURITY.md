# Security and privacy

- Never commit API keys, access tokens, passwords, private audio, or personal datasets.
- Store credentials in an OS-appropriate secret store or user-local configuration excluded from version control.
- Cloud processing must be opt-in, with the provider, data being sent, and any known cost explained before upload.
- Do not send audio to analytics or third parties by default.
- Process copies of input media; never overwrite originals automatically.
- Validate file types and size limits, and treat media metadata and model responses as untrusted input.
- Restrict AI actions to registered tools and validated arguments; do not execute arbitrary model-generated shell commands.
- Redact secrets from logs and crash reports.
- Document third-party licenses and user responsibilities for uploaded or converted voices.

## Reporting

Please do not publish secrets or private audio in issues. If a security issue is found, contact the project maintainer privately through GitHub's available private reporting options.
