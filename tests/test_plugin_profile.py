"""Offline contract tests for the Apertis Hermes provider profile."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types
import unittest


PLUGIN_PATH = Path(__file__).resolve().parents[1] / "__init__.py"


class ProviderProfile:
    """Minimal stand-in for Hermes' ProviderProfile at the import boundary."""

    def __init__(self, **attributes: object) -> None:
        self.__dict__.update(attributes)


def load_profile() -> ProviderProfile:
    """Import the plugin with only its two Hermes import dependencies stubbed."""

    registered: list[ProviderProfile] = []
    providers_module = types.ModuleType("providers")
    providers_module.register_provider = registered.append
    base_module = types.ModuleType("providers.base")
    base_module.ProviderProfile = ProviderProfile

    module_names = ("providers", "providers.base", "apertis_profile_under_test")
    previous_modules = {name: sys.modules.get(name) for name in module_names}
    try:
        sys.modules["providers"] = providers_module
        sys.modules["providers.base"] = base_module
        spec = importlib.util.spec_from_file_location(
            "apertis_profile_under_test", PLUGIN_PATH
        )
        assert spec is not None and spec.loader is not None
        plugin_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = plugin_module
        spec.loader.exec_module(plugin_module)
    finally:
        for name, module in previous_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    if len(registered) != 1:
        raise AssertionError(f"expected one registered profile, got {len(registered)}")
    return registered[0]


class ApertisProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = load_profile()

    def test_identity_and_aliases(self) -> None:
        self.assertEqual(self.profile.name, "apertis")
        self.assertEqual(self.profile.aliases, ("apertis-ai", "apertis-api"))
        self.assertEqual(self.profile.display_name, "Apertis AI")

    def test_openai_compatible_configuration(self) -> None:
        self.assertEqual(self.profile.api_mode, "chat_completions")
        self.assertEqual(self.profile.auth_type, "api_key")
        self.assertEqual(self.profile.base_url, "https://api.apertis.ai/v1")
        self.assertEqual(
            self.profile.env_vars, ("APERTIS_API_KEY", "APERTIS_BASE_URL")
        )

    def test_curated_fallback_catalog(self) -> None:
        self.assertEqual(self.profile.default_aux_model, "gpt-5.4-mini")
        self.assertEqual(
            self.profile.fallback_models,
            (
                "gpt-5.5",
                "gpt-5.4-mini",
                "claude-opus-4-8",
                "claude-sonnet-4-6",
                "gemini-3.1-pro-preview",
            ),
        )


if __name__ == "__main__":
    unittest.main()
