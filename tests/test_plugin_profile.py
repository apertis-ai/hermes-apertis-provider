"""Offline contract tests for the Apertis Hermes provider profile."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import types
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = REPOSITORY_ROOT / "__init__.py"
PACKAGE_PATH = REPOSITORY_ROOT / "hermes_apertis_provider" / "__init__.py"
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"
README_PATH = REPOSITORY_ROOT / "README.md"
INSTALLER_PATH = REPOSITORY_ROOT / "scripts" / "install.sh"
MANIFEST_PATH = REPOSITORY_ROOT / "plugin.yaml"
CHANGELOG_PATH = REPOSITORY_ROOT / "CHANGELOG.md"
PUBLISH_WORKFLOW_PATH = REPOSITORY_ROOT / ".github" / "workflows" / "publish-pypi.yml"


class ProviderProfile:
    """Minimal stand-in for Hermes' ProviderProfile at the import boundary."""

    def __init__(self, **attributes: object) -> None:
        self.__dict__.update(attributes)


def load_profile() -> ProviderProfile:
    """Import the directory plugin with only its Hermes boundary stubbed."""

    registered: list[ProviderProfile] = []
    providers_module = types.ModuleType("providers")
    providers_module.register_provider = registered.append
    base_module = types.ModuleType("providers.base")
    base_module.ProviderProfile = ProviderProfile

    module_name = "apertis_profile_under_test"
    module_names = ("providers", "providers.base", module_name)
    previous_modules = {name: sys.modules.get(name) for name in module_names}
    try:
        sys.modules["providers"] = providers_module
        sys.modules["providers.base"] = base_module
        spec = importlib.util.spec_from_file_location(
            module_name,
            PLUGIN_PATH,
            submodule_search_locations=[str(REPOSITORY_ROOT)],
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
        for name in tuple(sys.modules):
            if name.startswith(f"{module_name}."):
                sys.modules.pop(name, None)

    if len(registered) != 1:
        raise AssertionError(f"expected one registered profile, got {len(registered)}")
    return registered[0]


def load_packaged_profile() -> tuple[ProviderProfile, types.ModuleType]:
    """Load and invoke the pip entry-point module against a stub Hermes host."""

    registered: list[ProviderProfile] = []
    providers_module = types.ModuleType("providers")
    providers_module.register_provider = registered.append
    base_module = types.ModuleType("providers.base")
    base_module.ProviderProfile = ProviderProfile

    module_name = "hermes_apertis_provider_under_test"
    module_names = ("providers", "providers.base", module_name)
    previous_modules = {name: sys.modules.get(name) for name in module_names}
    try:
        sys.modules["providers"] = providers_module
        sys.modules["providers.base"] = base_module
        spec = importlib.util.spec_from_file_location(
            module_name,
            PACKAGE_PATH,
            submodule_search_locations=[str(PACKAGE_PATH.parent)],
        )
        assert spec is not None and spec.loader is not None
        package_module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = package_module
        spec.loader.exec_module(package_module)
        self_register = getattr(package_module, "register")
        self_register()
    finally:
        for name, module in previous_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    if len(registered) != 1:
        raise AssertionError(f"expected one registered profile, got {len(registered)}")
    return registered[0], package_module


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
                "gpt-5.6-sol",
                "gpt-5.5",
                "gpt-5.4-mini",
                "claude-opus-4-8",
                "claude-sonnet-4-6",
                "gemini-3.1-pro-preview",
            ),
        )

    def test_packaged_entry_point_matches_directory_profile(self) -> None:
        packaged, package_module = load_packaged_profile()
        self.assertEqual(packaged.__dict__, self.profile.__dict__)
        self.assertEqual(package_module.__version__, "1.1.0")

    def test_python_package_metadata(self) -> None:
        metadata = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
        self.assertEqual(metadata["project"]["name"], "hermes-apertis-provider")
        self.assertEqual(metadata["project"]["version"], "1.1.0")
        self.assertEqual(metadata["project"].get("dependencies", []), [])
        self.assertEqual(
            metadata["project"]["entry-points"]["hermes_agent.model_providers"],
            {"apertis": "hermes_apertis_provider:register"},
        )

    def test_readme_uses_canonical_default_model_key(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("  default: gpt-5.6-sol", readme)
        self.assertNotIn("  model: gpt-5.6-sol", readme)
        self.assertNotIn("  default: gpt-5.5", readme)

    def test_readme_pins_the_release_installer(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "raw.githubusercontent.com/apertis-ai/hermes-apertis-provider/"
            "v1.1.0/scripts/install.sh",
            readme,
        )
        self.assertIn("APERTIS_PLUGIN_REF=v1.1.0", readme)
        self.assertIn("mktemp", readme)
        self.assertIn("( set -eu; installer=$(mktemp", readme)
        self.assertIn("Review the tagged script", readme)
        self.assertIn(
            "git clone https://github.com/apertis-ai/hermes-apertis-provider.git",
            readme,
        )
        self.assertNotIn("/tmp/hermes-apertis-install.sh", readme)
        self.assertNotIn("| APERTIS_PLUGIN_REF", readme)

    def test_readme_bootstraps_existing_manual_clones(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn("If `scripts/install.sh` is missing", readme)
        self.assertIn("Then run the `APERTIS_PLUGIN_REF=main` update below", readme)
        self.assertIn("never use the pinned command to downgrade", readme)
        self.assertIn(
            'git -C "${HERMES_HOME:-$HOME/.hermes}/plugins/model-providers/apertis" '
            "\\\n  pull --ff-only origin main",
            readme,
        )

    def test_release_version_is_consistent(self) -> None:
        manifest = MANIFEST_PATH.read_text(encoding="utf-8")
        readme = README_PATH.read_text(encoding="utf-8")
        changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
        metadata = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
        self.assertIn("version: 1.1.0", manifest)
        self.assertEqual(metadata["project"]["version"], "1.1.0")
        self.assertIn("v1.1.0", readme)
        self.assertIn("## [1.1.0] - 2026-07-14", changelog)

    def test_readme_documents_native_and_pip_installs(self) -> None:
        readme = README_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "hermes plugins install apertis-ai/hermes-apertis-provider", readme
        )
        self.assertIn("pip install hermes-apertis-provider==1.1.0", readme)
        self.assertIn("hermes_agent.model_providers", readme)

    def test_publish_workflow_uses_oidc_and_pinned_actions(self) -> None:
        workflow = PUBLISH_WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("id-token: write", workflow)
        self.assertIn("environment: pypi", workflow)
        self.assertIn("release:", workflow)
        self.assertIn("types: [published]", workflow)
        self.assertNotIn("password:", workflow)
        for line in workflow.splitlines():
            if "uses:" not in line:
                continue
            reference = line.split("uses:", 1)[1].split("#", 1)[0].strip()
            revision = reference.rsplit("@", 1)[-1]
            self.assertRegex(revision, r"^[0-9a-f]{40}$")


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.source = self.root / "source"
        self.hermes_home = self.root / "hermes-home"
        self.source.mkdir()
        self.run_git("init", "-b", "main", cwd=self.source)
        self.run_git("config", "user.name", "Apertis Test", cwd=self.source)
        self.run_git(
            "config", "user.email", "apertis-test@example.invalid", cwd=self.source
        )
        self.commit_source("v1")
        self.run_git("tag", "v1.0.0", cwd=self.source)
        self.commit_source("v2")

    def run_git(self, *args: str, cwd: Path) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def commit_source(self, content: str) -> None:
        (self.source / "payload.txt").write_text(content, encoding="utf-8")
        self.run_git("add", "payload.txt", cwd=self.source)
        self.run_git("commit", "-m", content, cwd=self.source)

    def run_installer(
        self, *, ref: str | None = None, env_updates: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = self.installer_environment(ref=ref, env_updates=env_updates)
        return subprocess.run(
            ["sh", str(INSTALLER_PATH)],
            cwd=REPOSITORY_ROOT,
            env=env,
            capture_output=True,
            text=True,
        )

    def installer_environment(
        self, *, ref: str | None = None, env_updates: dict[str, str] | None = None
    ) -> dict[str, str]:
        env = os.environ.copy()
        env["HERMES_HOME"] = str(self.hermes_home)
        env["APERTIS_PLUGIN_REPOSITORY"] = str(self.source)
        env.pop("APERTIS_PLUGIN_REF", None)
        if ref is not None:
            env["APERTIS_PLUGIN_REF"] = ref
        if env_updates is not None:
            env.update(env_updates)
        return env

    @property
    def target(self) -> Path:
        return self.hermes_home / "plugins" / "model-providers" / "apertis"

    def assert_ignored_collision_is_rejected(
        self, relative_path: str, ignore_pattern: str
    ) -> None:
        (self.source / ".gitignore").write_text(ignore_pattern, encoding="utf-8")
        self.run_git("add", ".gitignore", cwd=self.source)
        self.run_git("commit", "-m", "add ignore pattern", cwd=self.source)
        self.assertEqual(self.run_installer().returncode, 0)
        local_file = self.target / relative_path
        local_file.parent.mkdir(parents=True, exist_ok=True)
        local_file.write_text("keep me", encoding="utf-8")
        remote_file = self.source / relative_path
        remote_file.parent.mkdir(parents=True, exist_ok=True)
        remote_file.write_text("remote", encoding="utf-8")
        self.run_git("add", "-f", relative_path, cwd=self.source)
        self.run_git("commit", "-m", "track ignored path", cwd=self.source)

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me")

    def test_fresh_install_uses_selected_hermes_home(self) -> None:
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.run_git("rev-parse", "HEAD", cwd=self.target),
            self.run_git("rev-parse", "HEAD", cwd=self.source),
        )

    def test_fresh_install_can_pin_release_ref(self) -> None:
        result = self.run_installer(ref="v1.0.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = self.run_git("rev-list", "-n", "1", "v1.0.0", cwd=self.source)
        self.assertEqual(self.run_git("rev-parse", "HEAD", cwd=self.target), expected)

        repeated = self.run_installer(ref="v1.0.0")
        self.assertEqual(repeated.returncode, 0, repeated.stderr)
        self.assertEqual(self.run_git("rev-parse", "HEAD", cwd=self.target), expected)

    def test_release_ref_prefers_tag_over_same_named_branch(self) -> None:
        self.run_git("branch", "v1.0.0", "HEAD", cwd=self.source)

        result = self.run_installer(ref="v1.0.0")

        expected = self.run_git("rev-list", "-n", "1", "refs/tags/v1.0.0", cwd=self.source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_git("rev-parse", "HEAD", cwd=self.target), expected)

    def test_dirty_checkout_is_preserved_and_rejected(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        local_file = self.target / "local-change.txt"
        local_file.write_text("keep me", encoding="utf-8")

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me")

    def test_hidden_untracked_files_are_preserved_and_rejected(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        self.run_git(
            "config", "status.showUntrackedFiles", "no", cwd=self.target
        )
        local_file = self.target / "hidden-untracked.txt"
        local_file.write_text("keep me", encoding="utf-8")

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me")

    def test_ignored_file_collision_is_preserved_and_rejected(self) -> None:
        self.assert_ignored_collision_is_rejected("custom.conf", "custom.conf\n")

    def test_ignored_newline_path_is_preserved_and_rejected(self) -> None:
        self.assert_ignored_collision_is_rejected("line\nbreak.conf", "*.conf\n")

    def test_ignored_glob_path_is_preserved_and_rejected(self) -> None:
        self.assert_ignored_collision_is_rejected("tests/*", "tests/*\n")

    def test_ignored_ancestor_file_is_preserved_and_rejected(self) -> None:
        (self.source / ".gitignore").write_text("custom\n", encoding="utf-8")
        self.run_git("add", ".gitignore", cwd=self.source)
        self.run_git("commit", "-m", "ignore custom path", cwd=self.source)
        self.assertEqual(self.run_installer().returncode, 0)
        local_file = self.target / "custom"
        local_file.write_text("keep me", encoding="utf-8")
        remote_file = self.source / "custom" / "created.txt"
        remote_file.parent.mkdir()
        remote_file.write_text("remote", encoding="utf-8")
        self.run_git("add", "-f", "custom/created.txt", cwd=self.source)
        self.run_git("commit", "-m", "track nested custom path", cwd=self.source)

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me")

    def test_literal_ignored_ancestor_is_not_confused_with_pathspec(self) -> None:
        (self.source / ".gitignore").write_text("a\\[bc\\]\n", encoding="utf-8")
        (self.source / "ab").write_text("tracked\n", encoding="utf-8")
        self.run_git("add", ".gitignore", "ab", cwd=self.source)
        self.run_git("commit", "-m", "add pathspec collision fixture", cwd=self.source)
        self.assertEqual(self.run_installer().returncode, 0)
        local_file = self.target / "a[bc]"
        local_file.write_text("keep me", encoding="utf-8")
        self.assertEqual(
            self.run_git("status", "--porcelain", "--untracked-files=all", cwd=self.target),
            "",
        )
        remote_file = self.source / "a[bc]" / "created.txt"
        remote_file.parent.mkdir()
        remote_file.write_text("remote\n", encoding="utf-8")
        self.run_git(
            "--literal-pathspecs",
            "add",
            "-f",
            "--",
            "a[bc]/created.txt",
            cwd=self.source,
        )
        self.run_git("commit", "-m", "track literal pathspec ancestor", cwd=self.source)

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me")

    def test_unrelated_ignored_file_does_not_block_update(self) -> None:
        (self.source / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        self.run_git("add", ".gitignore", cwd=self.source)
        self.run_git("commit", "-m", "ignore Python cache", cwd=self.source)
        self.assertEqual(self.run_installer().returncode, 0)
        cache_file = self.target / "__pycache__" / "plugin.pyc"
        cache_file.parent.mkdir()
        cache_file.write_bytes(b"cache")
        self.commit_source("v3")

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(cache_file.read_bytes(), b"cache")

    def test_status_failure_is_rejected(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper_dir = self.root / "git-wrapper"
        wrapper_dir.mkdir()
        wrapper = wrapper_dir / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "-C" ] && [ "$3" = "status" ]; then\n'
            "    exit 70\n"
            "fi\n"
            'exec "$APERTIS_TEST_REAL_GIT" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        result = self.run_installer(
            env_updates={
                "APERTIS_TEST_REAL_GIT": real_git or "git",
                "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("could not inspect", result.stderr)

    def test_clone_failure_does_not_delete_foreign_temporary_directory(self) -> None:
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper_dir = self.root / "git-wrapper"
        wrapper_dir.mkdir()
        marker = self.root / "collision-path"
        wrapper = wrapper_dir / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "clone" ]; then\n'
            '    claimed="$APERTIS_TEST_PARENT/.apertis-install-$PPID"\n'
            '    mkdir "$claimed"\n'
            '    printf "%s" "$claimed" > "$APERTIS_TEST_MARKER"\n'
            '    printf "preserve" > "$claimed/preserve"\n'
            "    exit 70\n"
            "fi\n"
            'exec "$APERTIS_TEST_REAL_GIT" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        result = self.run_installer(
            env_updates={
                "APERTIS_TEST_MARKER": str(marker),
                "APERTIS_TEST_PARENT": str(
                    self.hermes_home / "plugins" / "model-providers"
                ),
                "APERTIS_TEST_REAL_GIT": real_git or "git",
                "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        claimed = Path(marker.read_text(encoding="utf-8"))
        self.assertEqual((claimed / "preserve").read_text(encoding="utf-8"), "preserve")

    def test_concurrent_fresh_install_has_one_winner(self) -> None:
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper_dir = self.root / "git-wrapper"
        wrapper_dir.mkdir()
        started = self.root / "clone-started"
        continue_marker = self.root / "continue-clone"
        gate_lock = self.root / "clone-gate"
        wrapper = wrapper_dir / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "clone" ] && mkdir "$APERTIS_TEST_GATE_LOCK" 2>/dev/null; then\n'
            '    : > "$APERTIS_TEST_STARTED"\n'
            '    while [ ! -e "$APERTIS_TEST_CONTINUE" ]; do sleep 0.01; done\n'
            "fi\n"
            'exec "$APERTIS_TEST_REAL_GIT" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        env_updates = {
            "APERTIS_TEST_CONTINUE": str(continue_marker),
            "APERTIS_TEST_GATE_LOCK": str(gate_lock),
            "APERTIS_TEST_REAL_GIT": real_git or "git",
            "APERTIS_TEST_STARTED": str(started),
            "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        first = subprocess.Popen(
            ["sh", str(INSTALLER_PATH)],
            cwd=REPOSITORY_ROOT,
            env=self.installer_environment(env_updates=env_updates),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while not started.exists():
                if first.poll() is not None:
                    self.fail("first installer exited before reaching clone gate")
                if time.monotonic() >= deadline:
                    self.fail("timed out waiting for first installer clone")
                time.sleep(0.01)

            second = self.run_installer(env_updates=env_updates)
            continue_marker.touch()
            first_stdout, first_stderr = first.communicate(timeout=5)
        finally:
            continue_marker.touch(exist_ok=True)
            if first.poll() is None:
                first.kill()
                first.communicate()

        self.assertEqual(first.returncode, 0, first_stderr or first_stdout)
        self.assertNotEqual(second.returncode, 0)
        self.assertFalse(
            any(path.name.startswith(".apertis-install") for path in self.target.iterdir())
        )

    def test_legacy_stale_install_lock_does_not_block_install(self) -> None:
        lock = self.hermes_home / "plugins" / "model-providers" / ".apertis-install.lock"
        lock.mkdir(parents=True)
        (lock / "owner").write_text("99999999\n", encoding="utf-8")

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.target.is_dir())
        self.assertTrue(lock.is_dir())

    def test_stale_recovery_marker_does_not_block_install(self) -> None:
        lock = self.hermes_home / "plugins" / "model-providers" / ".apertis-install.lock"
        (lock / ".recovery").mkdir(parents=True)
        (lock / "owner").write_text("99999999\n", encoding="utf-8")

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.target.is_dir())

    def test_interrupted_lock_acquisition_does_not_block_later_install(self) -> None:
        real_git = shutil.which("git")
        real_mv = shutil.which("mv")
        self.assertIsNotNone(real_git)
        self.assertIsNotNone(real_mv)

        wrapper_dir = self.root / "interrupted-lock-wrappers"
        wrapper_dir.mkdir()
        gate_ready = self.root / "lock-gate-ready"
        release_gate = self.root / "release-lock-gate"
        legacy_owner = (
            self.hermes_home
            / "plugins"
            / "model-providers"
            / ".apertis-install.lock"
            / "owner"
        )
        (wrapper_dir / "mv").write_text(
            "#!/bin/sh\n"
            'if [ "$2" = "$APERTIS_TEST_LEGACY_OWNER" ] '
            '&& [ ! -e "$APERTIS_TEST_GATE_READY" ]; then\n'
            '    : > "$APERTIS_TEST_GATE_READY"\n'
            '    while [ ! -e "$APERTIS_TEST_RELEASE_GATE" ]; do sleep 0.01; done\n'
            "fi\n"
            'exec "$APERTIS_TEST_REAL_MV" "$@"\n',
            encoding="utf-8",
        )
        (wrapper_dir / "git").write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "clone" ] && [ ! -e "$APERTIS_TEST_GATE_READY" ]; then\n'
            '    : > "$APERTIS_TEST_GATE_READY"\n'
            '    while [ ! -e "$APERTIS_TEST_RELEASE_GATE" ]; do sleep 0.01; done\n'
            "fi\n"
            'exec "$APERTIS_TEST_REAL_GIT" "$@"\n',
            encoding="utf-8",
        )
        for wrapper_name in ("git", "mv"):
            (wrapper_dir / wrapper_name).chmod(0o755)

        env_updates = {
            "APERTIS_TEST_GATE_READY": str(gate_ready),
            "APERTIS_TEST_LEGACY_OWNER": str(legacy_owner),
            "APERTIS_TEST_REAL_GIT": real_git or "git",
            "APERTIS_TEST_REAL_MV": real_mv or "mv",
            "APERTIS_TEST_RELEASE_GATE": str(release_gate),
            "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        first = subprocess.Popen(
            ["sh", str(INSTALLER_PATH)],
            cwd=REPOSITORY_ROOT,
            env=self.installer_environment(env_updates=env_updates),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        try:
            deadline = time.monotonic() + 5
            while not gate_ready.exists():
                if first.poll() is not None:
                    self.fail("installer exited before interrupted-lock gate")
                if time.monotonic() >= deadline:
                    self.fail("timed out waiting for interrupted-lock gate")
                time.sleep(0.01)

            os.killpg(first.pid, signal.SIGKILL)
            first.communicate(timeout=5)

            result = self.run_installer(env_updates=env_updates)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(self.target.is_dir())
        finally:
            release_gate.touch(exist_ok=True)
            if first.poll() is None:
                os.killpg(first.pid, signal.SIGKILL)
                first.communicate()

    def test_concurrent_updates_do_not_cross_contaminate_selected_refs(self) -> None:
        self.assertEqual(self.run_installer(ref="v1.0.0").returncode, 0)
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper_dir = self.root / "git-wrapper"
        wrapper_dir.mkdir()
        first_ready = self.root / "first-update-ready"
        release_first = self.root / "release-first-update"
        wrapper = wrapper_dir / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "-C" ] && [ "$3" = "merge-base" ] '
            '&& [ "${APERTIS_PLUGIN_REF:-}" = "v1.0.0" ]; then\n'
            '    : > "$APERTIS_TEST_FIRST_READY"\n'
            '    while [ ! -e "$APERTIS_TEST_RELEASE_FIRST" ]; do sleep 0.01; done\n'
            "fi\n"
            'exec "$APERTIS_TEST_REAL_GIT" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)
        env_updates = {
            "APERTIS_TEST_FIRST_READY": str(first_ready),
            "APERTIS_TEST_REAL_GIT": real_git or "git",
            "APERTIS_TEST_RELEASE_FIRST": str(release_first),
            "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
        }
        first = subprocess.Popen(
            ["sh", str(INSTALLER_PATH)],
            cwd=REPOSITORY_ROOT,
            env=self.installer_environment(ref="v1.0.0", env_updates=env_updates),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while not first_ready.exists():
                if first.poll() is not None:
                    self.fail("first updater exited before reaching merge-base gate")
                if time.monotonic() >= deadline:
                    self.fail("timed out waiting for first updater")
                time.sleep(0.01)

            second = self.run_installer(ref="main", env_updates=env_updates)
            release_first.touch()
            first_stdout, first_stderr = first.communicate(timeout=5)
        finally:
            release_first.touch(exist_ok=True)
            if first.poll() is None:
                first.kill()
                first.communicate()

        expected = self.run_git("rev-list", "-n", "1", "v1.0.0", cwd=self.source)
        self.assertEqual(first.returncode, 0, first_stderr or first_stdout)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(self.run_git("rev-parse", "HEAD", cwd=self.target), expected)

    def test_manual_fetch_cannot_change_selected_update_ref(self) -> None:
        self.assertEqual(self.run_installer(ref="v1.0.0").returncode, 0)
        real_git = shutil.which("git")
        self.assertIsNotNone(real_git)
        wrapper_dir = self.root / "git-wrapper"
        wrapper_dir.mkdir()
        wrapper = wrapper_dir / "git"
        wrapper.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = "-C" ] && [ "$3" = "rev-parse" ] '
            '&& [ "$4" = "FETCH_HEAD" ] '
            '&& [ "${APERTIS_PLUGIN_REF:-}" = "v1.0.0" ]; then\n'
            '    "$APERTIS_TEST_REAL_GIT" -C "$2" fetch --quiet origin main\n'
            "fi\n"
            'exec "$APERTIS_TEST_REAL_GIT" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        result = self.run_installer(
            ref="v1.0.0",
            env_updates={
                "APERTIS_TEST_REAL_GIT": real_git or "git",
                "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            },
        )

        expected = self.run_git("rev-list", "-n", "1", "v1.0.0", cwd=self.source)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.run_git("rev-parse", "HEAD", cwd=self.target), expected)

    def test_target_creation_race_is_rejected_without_nested_install(self) -> None:
        real_mv = shutil.which("mv")
        self.assertIsNotNone(real_mv)
        wrapper_dir = self.root / "mv-wrapper"
        wrapper_dir.mkdir()
        wrapper = wrapper_dir / "mv"
        wrapper.write_text(
            "#!/bin/sh\n"
            'if [ "$2" = "$APERTIS_TEST_TARGET" ]; then\n'
            '    mkdir -p "$APERTIS_TEST_TARGET"\n'
            '    printf preserve > "$APERTIS_TEST_TARGET/foreign-file"\n'
            "fi\n"
            'exec "$APERTIS_TEST_REAL_MV" "$@"\n',
            encoding="utf-8",
        )
        wrapper.chmod(0o755)

        result = self.run_installer(
            env_updates={
                "APERTIS_TEST_REAL_MV": real_mv or "mv",
                "APERTIS_TEST_TARGET": str(self.target),
                "PATH": f"{wrapper_dir}{os.pathsep}{os.environ.get('PATH', '')}",
            }
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            (self.target / "foreign-file").read_text(encoding="utf-8"), "preserve"
        )
        self.assertFalse(
            any(path.name.startswith(".apertis-install") for path in self.target.iterdir())
        )

    def test_checkout_with_wrong_origin_is_rejected(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        self.run_git(
            "remote", "set-url", "origin", str(self.root / "not-apertis"), cwd=self.target
        )

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)

    def test_checkout_with_multiple_origin_urls_is_rejected(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        attacker = self.root / "attacker"
        self.run_git("clone", str(self.source), str(attacker), cwd=self.root)
        self.run_git("config", "user.name", "Apertis Test", cwd=attacker)
        self.run_git(
            "config", "user.email", "apertis-test@example.invalid", cwd=attacker
        )
        (attacker / "payload.txt").write_text("attacker", encoding="utf-8")
        self.run_git("add", "payload.txt", cwd=attacker)
        self.run_git("commit", "-m", "attacker", cwd=attacker)
        self.run_git("config", "--unset-all", "remote.origin.url", cwd=self.target)
        self.run_git(
            "config", "--add", "remote.origin.url", str(attacker), cwd=self.target
        )
        self.run_git(
            "config", "--add", "remote.origin.url", str(self.source), cwd=self.target
        )

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            (self.target / "payload.txt").read_text(encoding="utf-8"), "v2"
        )

    def test_origin_check_uses_url_before_git_rewrite(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        root_prefix = f"{self.root}{os.sep}"
        self.run_git(
            "config",
            f"url.file://{root_prefix}.insteadOf",
            root_prefix,
            cwd=self.target,
        )
        self.commit_source("v3")

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.run_git("rev-parse", "HEAD", cwd=self.target),
            self.run_git("rev-parse", "HEAD", cwd=self.source),
        )

    def test_non_git_target_is_preserved_and_rejected(self) -> None:
        self.target.mkdir(parents=True)
        local_file = self.target / "local-file.txt"
        local_file.write_text("keep me", encoding="utf-8")

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me")

    def test_target_nested_inside_checkout_is_rejected(self) -> None:
        (self.source / ".gitignore").write_text("profile/\n", encoding="utf-8")
        self.run_git("add", ".gitignore", cwd=self.source)
        self.run_git("commit", "-m", "ignore nested profile", cwd=self.source)
        checkout = self.root / "checkout"
        self.run_git("clone", str(self.source), str(checkout), cwd=self.root)
        self.hermes_home = checkout / "profile"
        self.target.mkdir(parents=True)

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.target / "__init__.py").exists())

    def test_broken_symlink_target_is_preserved_and_rejected(self) -> None:
        self.target.parent.mkdir(parents=True)
        missing_target = self.root / "missing-provider"
        self.target.symlink_to(missing_target, target_is_directory=True)

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(self.target.readlink(), missing_target)

    def test_git_worktree_target_is_supported(self) -> None:
        self.run_git("remote", "add", "origin", str(self.source), cwd=self.source)
        self.target.parent.mkdir(parents=True)
        self.run_git(
            "worktree",
            "add",
            "-b",
            "installed",
            str(self.target),
            "HEAD",
            cwd=self.source,
        )

        result = self.run_installer(ref="main")

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_empty_ref_uses_remote_default_for_nondefault_worktree(self) -> None:
        self.run_git("remote", "add", "origin", str(self.source), cwd=self.source)
        self.target.parent.mkdir(parents=True)
        self.run_git(
            "worktree",
            "add",
            "-b",
            "installed",
            str(self.target),
            "HEAD",
            cwd=self.source,
        )
        self.commit_source("v3")

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.run_git("rev-parse", "HEAD", cwd=self.target),
            self.run_git("rev-parse", "HEAD", cwd=self.source),
        )

    def test_clean_checkout_fast_forwards(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        self.commit_source("v3")

        result = self.run_installer()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.run_git("rev-parse", "HEAD", cwd=self.target),
            self.run_git("rev-parse", "HEAD", cwd=self.source),
        )

    def test_tracked_file_can_transition_to_directory(self) -> None:
        switch = self.source / "switch"
        switch.write_text("file\n", encoding="utf-8")
        self.run_git("add", "switch", cwd=self.source)
        self.run_git("commit", "-m", "file layout", cwd=self.source)
        self.run_git("tag", "file-layout", cwd=self.source)

        first = self.run_installer(ref="refs/tags/file-layout")
        self.assertEqual(first.returncode, 0, first.stderr)

        switch.unlink()
        switch.mkdir()
        (switch / "child").write_text("directory\n", encoding="utf-8")
        self.run_git("add", "-A", cwd=self.source)
        self.run_git("commit", "-m", "directory layout", cwd=self.source)

        update = self.run_installer(ref="main")

        self.assertEqual(update.returncode, 0, update.stderr)
        self.assertEqual(
            (self.target / "switch" / "child").read_text(encoding="utf-8"),
            "directory\n",
        )

    def test_tracked_directory_can_transition_to_file(self) -> None:
        switch = self.source / "switch"
        switch.mkdir()
        (switch / "child").write_text("directory\n", encoding="utf-8")
        self.run_git("add", "switch/child", cwd=self.source)
        self.run_git("commit", "-m", "directory layout", cwd=self.source)
        self.run_git("tag", "directory-layout", cwd=self.source)

        first = self.run_installer(ref="refs/tags/directory-layout")
        self.assertEqual(first.returncode, 0, first.stderr)

        (switch / "child").unlink()
        switch.rmdir()
        switch.write_text("file\n", encoding="utf-8")
        self.run_git("add", "-A", cwd=self.source)
        self.run_git("commit", "-m", "file layout", cwd=self.source)

        update = self.run_installer(ref="main")

        self.assertEqual(update.returncode, 0, update.stderr)
        self.assertEqual((self.target / "switch").read_text(encoding="utf-8"), "file\n")

    def test_diverged_checkout_is_rejected(self) -> None:
        self.assertEqual(self.run_installer().returncode, 0)
        self.run_git("config", "user.name", "Apertis Test", cwd=self.target)
        self.run_git(
            "config", "user.email", "apertis-test@example.invalid", cwd=self.target
        )
        (self.target / "local-commit.txt").write_text("local", encoding="utf-8")
        self.run_git("add", "local-commit.txt", cwd=self.target)
        self.run_git("commit", "-m", "local", cwd=self.target)
        self.commit_source("v3")

        result = self.run_installer()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.target / "local-commit.txt").is_file())


if __name__ == "__main__":
    unittest.main()
