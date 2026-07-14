# Review Debt Register

## Resolved local review items

| Source | Result | Resolution |
| --- | --- | --- |
| Simplify review | OpenSpec's generated `.codex/` helpers were out of scope; the plan contained trailing whitespace. | Added `.codex/` to `.gitignore` and removed trailing whitespace. |
| Scope/security pass | No P0--P2 issue found. The profile is declarative metadata only: credentials remain environment variables, and it adds no network, persistence, endpoint, or core-Hermes code. | No code change required. |

## Independent review

| Source | Result | Evidence |
| --- | --- | --- |
| `codex review --base main` | Passed, no actionable P0--P2 findings. | Updated the standalone Codex CLI from `0.139.0` to `0.144.3`, then ran the review with the configured `gpt-5.6-terra` model. The review confirmed the user-plugin discovery contract and the offline plus temporary-`HERMES_HOME` checks. |

The review wrapper's final `zsh` exit status was non-zero only because its
diagnostic variable was named `status`, which is read-only in `zsh`; Codex had
already emitted its positive review conclusion. This is an orchestration
artifact, not a provider finding.
