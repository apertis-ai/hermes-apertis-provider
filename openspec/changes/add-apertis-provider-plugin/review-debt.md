# Review Debt Register

## Resolved local review items

| Source | Result | Resolution |
| --- | --- | --- |
| Simplify review | OpenSpec's generated `.codex/` helpers were out of scope; the plan contained trailing whitespace. | Added `.codex/` to `.gitignore` and removed trailing whitespace. |
| Scope/security pass | No P0--P2 issue found. The profile is declarative metadata only: credentials remain environment variables, and it adds no network, persistence, endpoint, or core-Hermes code. | No code change required. |

## Pending independent-review infrastructure

| Source | Status | Evidence | Merge implication |
| --- | --- | --- | --- |
| `codex review --uncommitted` | Blocked | The configured `gpt-5.6-terra` model requires a newer Codex CLI. A compatible override did not return a final finding report. | Do not claim this branch is independently reviewed or merge-ready. |
| Claude Code second opinion | Blocked | `claude -p --permission-mode plan ...` returned `Not logged in · Please run /login`. | Re-run after login, or obtain a GitHub-hosted review on the PR. |
