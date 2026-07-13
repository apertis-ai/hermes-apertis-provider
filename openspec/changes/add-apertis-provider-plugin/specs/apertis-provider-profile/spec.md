## ADDED Requirements

### Requirement: Hermes discovers an Apertis provider profile
The standalone plugin SHALL register one `ProviderProfile` named `apertis`
when Hermes imports the plugin from a user model-provider directory. The
profile SHALL resolve `apertis-ai` and `apertis-api` as aliases.

#### Scenario: Plugin is installed in the documented discovery directory
- **WHEN** the repository root is present at
  `$HERMES_HOME/plugins/model-providers/apertis/` and Hermes initializes its
  provider registry
- **THEN** `apertis` and both aliases resolve to the registered Apertis
  provider profile

### Requirement: The profile describes Apertis' compatible API
The registered profile SHALL use the OpenAI-compatible
`https://api.apertis.ai/v1` base URL, `chat_completions` API mode,
`APERTIS_API_KEY` credential, and optional `APERTIS_BASE_URL` endpoint
override.

#### Scenario: Default configuration is used
- **WHEN** a Hermes user selects the `apertis` provider without a base URL
  override
- **THEN** Hermes receives the documented Apertis base URL and API-key
  environment-variable contract from the profile

### Requirement: The fallback catalog does not replace live entitlement data
The profile SHALL provide a small curated fallback catalog from current Apertis
documentation, and it SHALL leave live `/v1/models` discovery as the source of
truth for models accessible to a user's key and plan.

#### Scenario: Live model discovery is unavailable
- **WHEN** Hermes cannot obtain the live Apertis model catalog
- **THEN** Hermes can use the profile's fallback models without claiming that
  every listed model is enabled for the user's account
