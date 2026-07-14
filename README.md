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

Clone this repository directly into Hermes' user model-provider directory:

```sh
export HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
mkdir -p "$HERMES_HOME/plugins/model-providers"
git clone https://github.com/apertis-ai/hermes-apertis-provider.git \
  "$HERMES_HOME/plugins/model-providers/apertis"
```

The final directory must contain `__init__.py` and `plugin.yaml` directly; do
not add an extra nested repository directory.

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
  default: gpt-5.5
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
generic transport and discovery system. It does not modify Hermes Agent, add a
custom transport or authentication flow, publish a pip package, or guarantee
model access for any Apertis plan.

## License

[MIT](LICENSE)
