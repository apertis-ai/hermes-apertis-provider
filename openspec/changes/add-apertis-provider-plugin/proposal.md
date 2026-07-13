## Why

Hermes Agent users can configure any OpenAI-compatible endpoint manually, but
they cannot select Apertis by name, use its standard environment variables, or
receive a curated fallback catalog without duplicating provider configuration.
The Hermes contribution policy requires third-party product integrations to be
published as standalone plugins rather than added to the Hermes repository.

## What Changes

- Publish a standalone Apertis model-provider plugin in the
  `apertis-ai/hermes-apertis-provider` repository.
- Register the OpenAI-compatible Apertis provider profile with its canonical
  name, aliases, environment variables, endpoint, and curated fallback models.
- Document clone-based installation into Hermes' user plugin discovery path and
  the minimum configuration needed to select the provider.
- Add offline tests that verify the profile's registration contract without an
  Apertis API key or network request.

## Capabilities

### New Capabilities

- `apertis-provider-profile`: Register an Apertis AI model-provider profile
  that Hermes discovers from a user plugin directory.
- `apertis-provider-installation`: Document safe installation and configuration
  of the standalone provider plugin.

### Modified Capabilities

- None.

## Impact

- Adds only files in this standalone repository; it does not alter Hermes
  Agent, its configuration examples, or its test suite.
- Depends on Hermes' existing user model-provider discovery and on Apertis'
  OpenAI-compatible API surface.
