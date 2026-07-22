# Contributing to MyDesk AI

Thank you for considering contributing to MyDesk AI. We welcome contributions of all sizes — from bug reports and documentation fixes to feature additions and performance improvements.

This guide explains how to get your development environment set up, the workflow we expect for contributions, and how to write high-quality PRs that will be reviewed and merged quickly.

## Table of Contents

- Getting started
- Development workflow
- Coding standards
- Testing
- Pull request process
- Reporting bugs
- Feature requests
- Security disclosures
- Code of Conduct

## Getting started

1. Fork the repository on GitHub.
2. Clone your fork locally:

```bash
git clone https://github.com/<your-username>/mydesk-ai.git
cd mydesk-ai
```

3. Backend setup (Python 3.11+):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Frontend setup (Node 18+):

```bash
cd ../frontend
npm install
```

5. Create environment files from examples and configure dev credentials:
- `backend/.env` ← copy from `.env.example`
- `frontend/.env.local` ← set `NEXT_PUBLIC_API_URL` etc.

> Tip: Use a disposable Google test account and a test OpenAI key for local development.

## Development workflow

- Create a feature branch from `main`:

```bash
git checkout -b feat/your-feature-name
```

- Keep changes scoped to a single feature or fix.
- Rebase on `main` frequently and solve conflicts locally.

## Coding standards

- Python: follow PEP8. Use `black` for formatting, `ruff` for linting, and `isort` for imports.
- Type hints are required for new backend code.
- JavaScript/TypeScript: use Prettier and ESLint rules shipped in the repo.
- Keep functions small and tests focused.

## Testing

- Backend tests use `pytest`. Run them locally:

```bash
cd backend
.venv/bin/pytest -q
```

- Frontend unit and integration tests are run with your preferred test runner (Jest/Playwright integration can be added).

- Add tests for any bug fixes or new features.

## Pull request process

- Open a PR against `main` with a concise title and a descriptive body explaining the motivation and changes.
- Include tests and screenshots/GIFs when UI changes are involved.
- The maintainers will run CI; address any failures and respond to review comments.
- Squash or rebase commits as requested by the reviewer.

### PR checklist (maintainers may ask for):
- [ ] Tests added or updated
- [ ] README/docs updated where applicable
- [ ] Linting/formatting checks pass
- [ ] No sensitive credentials in the diff

## Reporting bugs

Please open an issue using the bug template and include:
- Steps to reproduce
- Expected behavior vs actual behavior
- Minimal reproduction if possible
- Logs, stack traces, and environment (OS, Python/Node versions)

## Feature requests

- For larger features, please open an issue to discuss the design first.
- Provide rationale, examples, and suggested implementation details.

## Security disclosures

If you discover a security vulnerability, please follow the security policy in `SECURITY.md` to report it privately.

## Code of Conduct

This project follows a Code of Conduct. By participating, you agree to abide by its terms.

---

Thanks again for helping make MyDesk AI better. We appreciate your time and contributions.