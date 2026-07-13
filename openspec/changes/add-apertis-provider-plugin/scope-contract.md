# Scope Contract — add-apertis-provider-plugin

- **card_id / change_id:** `add-apertis-provider-plugin`
- **owns:** A standalone Apertis `ProviderProfile`, its model-provider
  manifest, clone-install documentation, and offline registration tests.
- **depends_on:** Hermes Agent's user plugin discovery contract under
  `$HERMES_HOME/plugins/model-providers/`; Apertis' documented
  OpenAI-compatible endpoint and model-list API.
- **does_not_own:** Changes to the Hermes repository; a new Hermes upstream
  pull request; API-key provisioning; live inference testing against a customer
  account; publishing a pip package; Discord promotion; or a reply on closed
  PR #33752.
- **mock_allowed:** None. The plugin is a real configuration artifact; tests
  may stub Hermes' provider modules only to assert metadata without contacting
  Apertis.
- **backend_contracts:** Hermes must import `__init__.py` from the configured
  user model-provider directory and expose `ProviderProfile` registration. The
  user's Apertis key must authorize the generic Hermes `/v1/models` probe and
  inference requests.
- **gap_map:**
  - Live API credentials and per-plan model access are owned by Apertis and the
    user account, not this plugin. Decision source: Apertis model-list API
    documents that results depend on key type and subscription plan.
  - Hermes core discovery is owned by `NousResearch/hermes-agent`; this plugin
    consumes its documented public discovery path without modifying it.
- **readiness_state:** `live` for clone-installed profile registration;
  `out_of_scope` for live account-specific API verification.
