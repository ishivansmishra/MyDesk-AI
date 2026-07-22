# Security Policy

Thank you for caring about security. This policy describes how to report a vulnerability and how we handle security issues.

## Reporting a Vulnerability

If you discover a security issue in MyDesk AI, please follow these steps:

1. Do NOT open a public issue. Instead, send an email to the security contact:

   `security@mydesk.example` (replace this address with the project's private security contact)

2. Provide the following information:
   - A clear description of the issue
   - Steps to reproduce the vulnerability
   - Expected and actual behavior
   - The severity and potential impact
   - Any proof-of-concept code or exploit details (if safe to provide)

3. Optionally encrypt sensitive disclosure using our PGP key (if published in repository). If not available, please be mindful and avoid sending secrets over insecure channels.

## Response Timeline

We treat security reports with priority and will acknowledge receipt within 48 hours. We aim to provide a remediation timeline and coordinate disclosure with the reporter.

## Supported Versions

We support the latest release and the previous minor release. If you find an issue in an unsupported version, we will still investigate but may not provide a backport.

## Disclosure Policy

We will coordinate a responsible disclosure timeline with the reporter. Public disclosure will be delayed until a fix or mitigation is released.

## Security Best Practices

- Keep `GOOGLE_OAUTH_CLIENT_SECRET` and `OPENAI_API_KEY` in a secret manager.
- Rotate keys if you suspect compromise.
- Use HTTPS in production and enforce HSTS.
- Limit OAuth scopes to least privilege.

If you need an alternative contact channel, please open a PR to update this file with the maintainer's security contact information.