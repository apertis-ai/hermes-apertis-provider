# Hermes Apertis Provider

A standalone [Hermes Agent](https://github.com/NousResearch/hermes-agent)
model-provider plugin for [Apertis AI](https://apertis.ai). Apertis exposes an
OpenAI-compatible API at `https://api.apertis.ai/v1`.

This repository is intentionally separate from Hermes Agent. It is discovered
from your Hermes profile and does not require a Hermes source-tree change.

## Requirements

- A Hermes Agent installation with model-provider plugin discovery.
- An Apertis API key. Create and manage it in your Apertis account; never
  commit it to this repository or a Hermes project.

## Install

The installer places the provider in the active Hermes profile. For the first
published stable release, review the script and then run it pinned to `v1.0.0`.
These release-pinned commands become available when the `v1.0.0` tag is
published on GitHub:

```sh
(
  set -eu
  installer=$(mktemp "${TMPDIR:-/tmp}/hermes-apertis-install.XXXXXX")
  trap 'rm -f "$installer"' 0
  trap 'exit 1' HUP INT TERM
  curl --fail --silent --show-error --location \
    --output "$installer" \
    https://raw.githubusercontent.com/apertis-ai/hermes-apertis-provider/v1.0.0/scripts/install.sh
  less "$installer"
  APERTIS_PLUGIN_REF=v1.0.0 sh "$installer"
)
```

The subshell stops if the download or review step fails and always removes the
temporary file. Set `HERMES_HOME` before running it to install into a
non-default Hermes profile. The default is `~/.hermes`. The installer requires
Git and Python 3, matching Hermes' own runtime requirements.

After reviewing the tagged script, the equivalent non-interactive one-line
install keeps the same fail-fast download and cleanup behavior:

```sh
( set -eu; installer=$(mktemp "${TMPDIR:-/tmp}/hermes-apertis-install.XXXXXX"); trap 'rm -f "$installer"' 0; trap 'exit 1' HUP INT TERM; curl --fail --silent --show-error --location --output "$installer" https://raw.githubusercontent.com/apertis-ai/hermes-apertis-provider/v1.0.0/scripts/install.sh; APERTIS_PLUGIN_REF=v1.0.0 sh "$installer"; )
```

Before that tag is published, install the current development snapshot by
cloning `main` directly:

```sh
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$HERMES_HOME/plugins/model-providers"
git clone https://github.com/apertis-ai/hermes-apertis-provider.git \
  "$HERMES_HOME/plugins/model-providers/apertis"
```

### Update

If `scripts/install.sh` is missing, the provider was installed with the earlier
manual-clone instructions. Bootstrap that checkout by fast-forwarding it to
`main` once:

```sh
git -C "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers/apertis" \
  pull --ff-only origin main
```

Then run the `APERTIS_PLUGIN_REF=main` update below. The installer intentionally
rejects non-fast-forward updates, so never use the pinned command to downgrade
a checkout that has already advanced beyond `v1.0.0`; use a separate checkout
if you need to preserve an older release.

Run the installed script with the ref you want to follow:

```sh
# Follow the current main branch.
APERTIS_PLUGIN_REF=main \
  sh "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers/apertis/scripts/install.sh"

# Or remain pinned to the stable release.
APERTIS_PLUGIN_REF=v1.0.0 \
  sh "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers/apertis/scripts/install.sh"
```

Version-shaped short refs such as `v1.0.0` resolve only to release tags. Other
short refs resolve only to branches; fully qualified `refs/tags/...` and
`refs/heads/...` values are also accepted.

Updates fail closed if the target has local changes, an ignored file would be
overwritten by the selected ref, the target is not a Git checkout, it uses a
different `origin`, or it cannot fast-forward. The installer never stashes,
resets, or deletes an existing provider checkout.

For every installation method, the final directory must contain `__init__.py`
and `plugin.yaml` directly.

## Configure Hermes

Add your key to `$HERMES_HOME/.env`:

```dotenv
APERTIS_API_KEY=your_apertis_api_key

# Optional: route through a compatible proxy or a different Apertis endpoint.
# APERTIS_BASE_URL=https://api.apertis.ai/v1
```

Select Apertis in `$HERMES_HOME/config.yaml`:

```yaml
model:
  provider: apertis
  default: gpt-5.6-sol
```

The aliases `apertis-ai` and `apertis-api` resolve to the same provider.

## Models

Hermes queries Apertis' OpenAI-compatible `/v1/models` endpoint when possible.
That live result is authoritative: the models available to you depend on your
API key and subscription plan. The small fallback list in this plugin is only
used when live model discovery is unavailable; it is not an entitlement
guarantee.

To inspect the models available to your account without exposing your key in
shell history, use your Apertis account tooling or an environment variable:

```sh
curl --fail-with-body https://api.apertis.ai/v1/models \
  -H "Authorization: Bearer ${APERTIS_API_KEY:?Set APERTIS_API_KEY first}"
```

## Verify

After setting `APERTIS_API_KEY`, run:

```sh
hermes doctor
```

The Provider Connectivity section should list Apertis. A successful health
check calls the account-aware `/v1/models` endpoint.

## Development

This repository has no runtime dependencies. Run its offline metadata tests
without a Hermes installation, API key, or network access:

```sh
python3 -m unittest discover -s tests -v
```

## Scope

This plugin only declares Apertis provider metadata for Hermes' existing
generic transport and discovery system. It is distributed through this
repository and GitHub Releases. It does not modify Hermes Agent, add a custom
transport or authentication flow, publish a PyPI package, or guarantee model
access for any Apertis plan.

## License

[MIT](LICENSE)
