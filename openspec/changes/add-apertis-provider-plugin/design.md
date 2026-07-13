## Context

The prior Apertis contribution was closed because it placed a third-party
provider inside the Hermes Agent repository. Hermes already discovers user
model-provider plugins from `$HERMES_HOME/plugins/model-providers/<name>/`, so
the integration can live in its own repository without core modifications.

The Apertis API documents an OpenAI-compatible base URL at
`https://api.apertis.ai/v1` and a credential-aware `/v1/models` endpoint. The
plugin therefore supplies metadata and lets Hermes' existing generic transport
and live model discovery perform requests.

## Goals / Non-Goals

**Goals:**

- Deliver a clone-installable Apertis provider profile that follows Hermes'
  user plugin discovery contract.
- Keep all credentials in the user's Hermes environment and avoid network
  access during repository tests.
- Give users exact installation and configuration instructions, including the
  boundary between static fallback models and their account's live catalog.

**Non-Goals:**

- Modify, fork, or reopen a pull request against `NousResearch/hermes-agent`.
- Add custom request transport, authentication flow, or model-list client.
- Package the plugin for pip, test customer credentials, or promise which
  models a particular Apertis plan enables.

## Decisions

### Repository root is the plugin directory

The repository root SHALL contain `__init__.py` and `plugin.yaml`, allowing a
user to clone it directly into `$HERMES_HOME/plugins/model-providers/apertis/`.
This matches the discovery directory exactly and avoids an installer or nested
package. A pip entry-point distribution was considered but deferred because it
adds packaging and release maintenance without being necessary for discovery.

### Use a declarative `ProviderProfile`

`__init__.py` SHALL instantiate and register `ProviderProfile` at module load.
The documented API is OpenAI-compatible, so no profile subclass or custom
transport is needed. The profile exposes `APERTIS_API_KEY` first and
`APERTIS_BASE_URL` as the optional endpoint override.

### Live model discovery is authoritative

The fallback catalog exists only for a failed or unavailable live `/v1/models`
request. It SHALL use current Apertis documentation examples, while README
documentation SHALL state that the actual catalog varies by API key and plan.
This avoids encoding entitlement decisions in the plugin.

### Verify configuration offline, then through Hermes discovery

Unit tests SHALL replace the `providers` modules with a minimal in-memory test
double and assert the registration metadata. A separate local verification
command SHALL place the plugin under a temporary `HERMES_HOME` and use the
latest Hermes checkout to prove discovery and aliases without an API key or
network request.

## Risks / Trade-offs

- **Apertis changes model IDs or entitlement tiers** → The live `/v1/models`
  endpoint remains authoritative; keep fallback models small and document their
  advisory role.
- **Hermes changes its user plugin import contract** → The plugin has no custom
  coupling and its discovery smoke test will identify a breaking change.
- **Users clone into an extra nested directory** → The README gives the exact
  clone destination and a Python verification command.

## Migration Plan

This is a new standalone repository. Users of the closed in-tree PR must remove
any manually copied Apertis directory from a Hermes source checkout and clone
this repository into the documented user plugin location. Removing that clone
reverts the plugin cleanly.

## Open Questions

None for the clone-install release. A pip distribution can be evaluated after
the plugin has stable usage.
