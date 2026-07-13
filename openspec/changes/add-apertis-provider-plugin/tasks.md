## 1. Provider plugin 結構

- [x] 1.1 建立以 `ProviderProfile` 註冊 Apertis 的 `__init__.py`。
- [x] 1.2 建立 `plugin.yaml` 與最小 `.gitignore`，使 repo 根目錄可直接作為 provider 目錄。

## 2. 使用者介面與離線測試

- [x] 2.1 更新 README，說明 clone 安裝、環境變數、Hermes provider 設定與模型方案限制。
- [x] 2.2 新增不需 Hermes 安裝、金鑰或網路的 profile 註冊與 metadata 單元測試。

## 3. 驗證與交付檢查

- [x] 3.1 執行單元測試，確認 profile、別名、endpoint、環境變數與 fallback catalog。
- [x] 3.2 用暫存 `HERMES_HOME` 對最新 Hermes checkout 執行 discovery smoke test，確認 canonical name 與 aliases。
- [x] 3.3 驗證 OpenSpec artifacts、範圍 diff 與 README 指令，記錄可重現證據。
