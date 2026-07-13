# Apertis standalone provider plugin — 執行計畫

> **工作目錄：** `/Users/quert/Documents/GitHub/apertis-ai/hermes-apertis-provider-worktrees/20260714-initial-apertis-provider`
> **Hermes 驗證參考：** `/Users/quert/Documents/GitHub/hermes-agent-worktrees/20260714-apertis-plugin-reference`（`af250d849`）

## Global Constraints

- 只修改 `apertis-ai/hermes-apertis-provider` feature worktree；不得修改
  Hermes Agent checkout 或重開 Hermes upstream PR。
- repo 根目錄必須能直接 clone 到
  `$HERMES_HOME/plugins/model-providers/apertis/`，不新增 pip package、安裝器或
  runtime dependency。
- 使用 `ProviderProfile` 的標準 `chat_completions` 路徑；不實作 custom
  transport、auth flow 或 live model client。
- 不讀取、輸出或提交 API key；所有 automated tests 均不連線 Apertis。
- `APERTIS_API_KEY` 優先，`APERTIS_BASE_URL` 是可選 base URL override；live
  `/v1/models` 是 per-key/per-plan 模型真值，fallback list 僅供失敗時使用。
- 現有 README、LICENSE 與 OpenSpec artifacts 都屬於本 change；任何新增檔案都必須
  可追溯至 `add-apertis-provider-plugin` 的 specs。

## 任務

### 1.1 建立 declarative Apertis profile

**Files:** `__init__.py`
**Spec:** `apertis-provider-profile` — discovery、default configuration、fallback catalog
**Interface:** module import calls `register_provider(ProviderProfile(...))` exactly once.

新增 canonical `apertis`、兩個 aliases、Apertis API metadata、current documented
fallback models、`api_key` auth 與 default auxiliary model。不要 subclass profile 或
發出網路請求。

### 1.2 建立 manifest 與忽略規則

**Files:** `plugin.yaml`, `.gitignore`
**Spec:** `apertis-provider-profile` — discovery
**Interface:** manifest `kind` is `model-provider`.

以 manifest 表示 plugin metadata，並忽略 Python bytecode cache。保持 repo root
layout，不加 nested source package。

### 2.1 撰寫 clone-install README

**Files:** `README.md`
**Spec:** `apertis-provider-installation` — installation、boundaries
**Interface:** documents clone destination, environment variables, and
`model.provider: apertis`.

將 GitHub 初始 README 換成使用者文件：前置條件、正確 clone path、環境變數、Hermes
config、帳戶模型的 `/v1/models` 查詢方式、解除安裝方式與明確 non-goals。不得要求
修改 Hermes source tree。

### 2.2 新增 offline metadata test

**Files:** `tests/test_plugin_profile.py`
**Spec:** `apertis-provider-profile` — discovery、default configuration、fallback catalog
**Interface:** `python -m unittest discover -s tests -v` exits 0.

用標準函式庫 `unittest` 和 in-memory `providers` / `providers.base` modules 載入
plugin，斷言 profile registration 與所有靜態 metadata。test 不得依賴網路、key 或
本機 Hermes install。

### 3.1 執行 offline unit test

**Files:** `tests/test_plugin_profile.py`
**Spec:** `apertis-provider-profile`
**Interface:** command output records zero failures.

執行標準函式庫 test runner，檢查 profile metadata、aliases、fallback list 和 manifest
expectations。把完整命令及 EXIT 保存到 Codex ledger。

### 3.2 執行最新 Hermes discovery smoke test

**Files:** `__init__.py`, `plugin.yaml`
**Spec:** `apertis-provider-profile` — discovery
**Interface:** `get_provider_profile(name).name == "apertis"` for all three names.

把 plugin 複製到暫存的 `$HERMES_HOME/plugins/model-providers/apertis/`，用最新
Hermes reference worktree 啟動一次獨立 Python process，檢查 canonical name 和
aliases。不設定 key，不呼叫 `/v1/models`，結束後刪除 temp directory。

### 3.3 進行 OpenSpec、scope 與 README 交付驗證

**Files:** `openspec/changes/add-apertis-provider-plugin/`, `README.md`
**Spec:** both capabilities
**Interface:** `openspec validate add-apertis-provider-plugin --strict --json` reports
one passing change.

重新驗證 OpenSpec、確保 diff 只包含 locked scope、從 README 擷取 clone destination
並驗證它正確匹配 Hermes discovery path。寫入 ledger 的 review debt 與 cleanup
receipt。

## Spec → Test Mapping

| Spec scenario | Evidence |
|---|---|
| Plugin is installed in the documented discovery directory | Task 3.2 temp `HERMES_HOME` smoke test |
| Default configuration is used | Task 2.2 metadata assertions |
| Live model discovery is unavailable | Task 2.2 fallback list assertions; README warns that account catalog is authoritative |
| User installs from a clean profile | Task 2.1 documentation plus Task 3.3 path check |
| User selects a model outside their plan | README explains live `/v1/models` and plan-dependent availability |

## Completion Evidence

1. `python -m unittest discover -s tests -v` exits 0.
2. The isolated latest-Hermes discovery process resolves the three expected
   identifiers without a network call or credentials.
3. `openspec validate add-apertis-provider-plugin --strict --json` passes.
4. Scope diff contains only plugin files, docs, tests, and workflow artifacts.
