# Security Policy

## Reporting Security Issues

If you discover a potential vulnerability in Muybridge CAD (such as code execution outside the compiler sandbox or unexpected file access), please report it responsibly rather than opening a public issue.

Send details to: **arnav.pdy2024@gmail.com**

Please include:
- A description of the issue and potential impact
- A minimal reproducible example (e.g. sample CAD snippet or API call)
- Any proposed remediation

You can expect an initial response acknowledging your report within 48 hours.

## Security Considerations

Muybridge CAD compiles build123d Python scripts in subprocesses with resource limits (`RLIMIT_CPU`, `RLIMIT_FSIZE`, `RLIMIT_NOFILE`) and `python3 -I` (isolated environment). However, when hosting this service for untrusted public traffic, run the backend inside an isolated container (Docker / gVisor) or VM with egress restrictions.
