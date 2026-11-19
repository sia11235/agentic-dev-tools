# agentic-dev-tools

Small, composable agentic tools for everyday dev workflow — run locally first,
wire into CI/CD once you trust them.

## Tools

### `review` — PR first-pass review agent

Reviews your local diff (uncommitted changes or a branch vs. a base ref) with
Claude before you open a PR, and prints findings grouped by file and severity.
It's meant to catch the obvious stuff — bugs, missing error handling, unclear
naming, missing tests — so human review starts from a cleaner diff.

```bash
# review uncommitted changes (staged + unstaged) against HEAD
agentic-tools review

# review a feature branch against main
agentic-tools review --base main

# only staged changes
agentic-tools review --staged

# machine-readable output, e.g. for piping into CI annotations
agentic-tools review --format json
```

Requires `ANTHROPIC_API_KEY`, either exported in the environment or in a
`.env` file (see `.env.example`). `.env` is loaded automatically from the
current directory or any parent directory, so you can drop one in whichever
repo you're running `agentic-tools` from — the key only loads for that
invocation, not globally into every shell.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env   # then edit .env with your real key
```

## Roadmap

- `review`: a first-pass reviewer you run locally before opening a PR. (done)
- CI integration: run `review` as a GitHub Action / Bitbucket Pipeline step and
  post findings as PR comments, so a human reviewer starts from an
  agent-reviewed diff.
- An overnight loop that scans a repo for small, mechanical fixes (lint
  violations, dead code, minor refactors) and opens small, readable PRs.
  Deliberately last: it writes code, so it only gets built once `review`'s
  judgment has been trusted in practice.

## License

MIT — see [LICENSE](LICENSE).
