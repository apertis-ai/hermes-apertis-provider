## ADDED Requirements

### Requirement: Installation documentation uses the standalone plugin path
The repository README SHALL instruct users to clone the repository directly to
`$HERMES_HOME/plugins/model-providers/apertis/` and SHALL show the required
`APERTIS_API_KEY` configuration.

#### Scenario: User installs the provider from a clean Hermes profile
- **WHEN** a user follows the README clone and configuration steps
- **THEN** the resulting directory layout matches Hermes' user provider
  discovery path without editing the Hermes source tree

### Requirement: Documentation states compatibility and boundaries
The README SHALL identify Apertis as OpenAI-compatible, show how to select the
provider in Hermes, and explain that model availability comes from the user's
live Apertis account catalog.

#### Scenario: User chooses an unsupported model for their plan
- **WHEN** a configured model is not available to the user's Apertis key or
  subscription
- **THEN** the documentation directs the user to inspect the live model list
  rather than treating the plugin fallback list as an entitlement guarantee
