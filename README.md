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

# a single commit, against its parent
agentic-tools review --commit 6f59e93

# any revision range (three dots = since the merge-base, like a PR)
agentic-tools review --range origin/develop...feature/network-dashboard
```

Large diffs are split by file into requests of at most `--max-chunk-chars`
(default 60,000 characters, about 15k tokens); a file bigger than that is split
on hunk boundaries. Each part is told which other files are in the full diff, so
it doesn't flag "missing" tests or callers that live in another part. Findings
are merged and deduplicated.

Lockfiles, `__pycache__`/`.pyc`, minified and source-map files, `dist/` and
`build/`, migration metadata and image/font assets are skipped by default (the
skipped list is printed to stderr). Add your own with `--exclude 'drizzle/*'`
(repeatable), or review everything with `--no-default-excludes`.

Requires `ANTHROPIC_API_KEY` in the environment.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export ANTHROPIC_API_KEY=sk-...
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
