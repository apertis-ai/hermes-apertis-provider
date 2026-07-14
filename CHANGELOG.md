# Changelog

All notable changes to the Hermes Apertis Provider are documented here. This
project follows [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-07-14

### Added

- Native `hermes plugins install` lifecycle support on compatible Hermes versions.
- Python wheel and source distribution with dedicated model-provider discovery.
- OIDC-based PyPI Trusted Publishing workflow and package artifact checks.

### Changed

- Shared one profile definition between directory and Python-package installs.
- Release-pinned installation examples now target v1.1.0.

## [1.0.0] - 2026-07-14

### Added

- Apertis AI provider metadata for Hermes' OpenAI-compatible transport.
- Canonical `apertis` provider name with `apertis-ai` and `apertis-api` aliases.
- Safe, idempotent installation and fast-forward update script.
- Offline contract tests and latest-Hermes discovery coverage.
- Configuration guidance using `gpt-5.6-sol` as the default model example.

[1.0.0]: https://github.com/apertis-ai/hermes-apertis-provider/releases/tag/v1.0.0
[1.1.0]: https://github.com/apertis-ai/hermes-apertis-provider/compare/v1.0.0...v1.1.0
