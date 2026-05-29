[English](/README.md) | [繁體中文](/README.zh-tw.md) | [简体中文](/README.zh-cn.md) | [日本語](/README.ja.md)

# InferSpec

**從你的程式碼 + Git 歷史 + 文件反向推導出 OpenSpec 規格** —
專為沒有規格的 legacy code 設計。

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Development-Driven Spec (DDS)** — Spec-Driven Development 的反向操作。
> From Code & Context to Clear Specs.

## SDD vs DDS

[Spec-Driven Development（SDD）](https://github.com/Fission-AI/OpenSpec)是「先寫
規格，再寫程式」的開發紀律，對 greenfield 專案非常合適。

**但真實世界大多是 brownfield。** 你接手一個五萬行的 Flask 服務，沒有規格 —
只有三年沒人動的 Jira 看板、沒人更新的 Confluence wiki、跟一份 Git log。SDD
在這裡完全找不到切入點。

**InferSpec 把這個流程反過來，叫做 Development-Driven Spec（DDS）。** 程式
已經在那裡 — 把它（加上 git 歷史、ticket、docs、MCP 連到的 wiki）當作真實
來源，*反向推導*出一份結構化的 OpenSpec 規格。規格存在之後，你可以重新切回
SDD 來做新功能。

| 模式 | 起點 | 產物 |
|------|------|------|
| **SDD**（Spec-Driven Development） | 規格 | 程式 |
| **DDS**（Development-Driven Spec） | 程式 + 歷史 + 文件 | 規格 |

## 為什麼需要 InferSpec？

**InferSpec 會把這些通通讀過**，產出結構化的 OpenSpec 規格 — 每個 capability 一份 `spec.md` — 並且每條 Requirement 都會回引到 `file:line` 或 ticket ID。AI 不確定的地方會標 `[GAP]`/`[TBD]`，讓你之後可以互動式地補上。

## 運作原理

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — uvx Python 套件：installer + CLI                  │
│  （永遠不會呼叫 LLM API）                                      │
└─────────────────────────────────────────────────────────────┘
                       │ 把 skill 安裝到
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Skill 在 Claude Code / Codex / Gemini / Copilot  │
│  / OpenCode 內執行，使用 host 的 subscription AI               │
└─────────────────────────────────────────────────────────────┘
```

InferSpec 完全依賴你已經訂閱的 AI 服務。不需要 API key、不需要設定雲端 endpoint。

## 安裝

```bash
uvx inferspec init --platform claude-code
```

這會把 `/inferspec-scan` + `/inferspec-cap` 安裝到當前目錄的 `.claude/skills/`。
完整支援平台清單可用 `inferspec platforms` 查看。

### 更新

新版 `inferspec` 套件發布後，各 repo 裡 `.claude/skills/`（或等效路徑）下的
skill 檔案仍停留在當初安裝的版本。用以下方式更新：

```bash
pip install -U inferspec        # 或：uvx --refresh inferspec ...
inferspec update                # 在每個跑過 `inferspec init` 的 repo 執行
```

`inferspec update` 會讀 `.inferspec.yaml` 找出當初安裝的 platforms，然後重新
複製 skill bundle（不會再問問題）。用 `inferspec update --check` 只看版本差
異不寫檔；`inferspec doctor` 會列出每個 platform 的「已安裝版本 vs 套件版本」。

## 使用方式

在目標 repo 開啟你的 AI agent。提供兩個 skill：

**`/inferspec-scan`** — bulk 模式，一次推所有 capability 的 spec：

```
/inferspec-scan
```

執行 `graphify` 將檔案分群成 capability，對每個 cap 讀取 code + `git log` +
`docs/` + (若可用) MCP 的 Jira/Confluence + host WebFetch 的 URL，產出 OpenSpec
格式的 `openspec/specs/<cap>/spec.md`。AI 不確定的部分會標 `[GAP]` / `[TBD]`。

**`/inferspec-cap <slug>`** — 單一 cap 深推 + 互動式 Q&A：

```
/inferspec-cap user-auth
/inferspec-cap "rate limiting"       # 模糊匹配
/inferspec-cap                       # 互動式選擇
/inferspec-cap new-feature --new     # 新 cap bootstrap
```

對單一 cap，skill 會主動詢問你有沒有 Jira/Confluence/URL，然後針對每個 `[GAP]`
marker 問一個聚焦問題直到 spec 收斂。結束時會問你要不要直接 commit。

外部資料來源（Jira、Confluence、URL）會自動處理 — InferSpec 偵測你 host 環境
裡的 MCP server，不自己維護 client。

## 輸出格式

跟 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 同一套慣例：

```markdown
## Purpose

訂單入口的使用者認證 — 因為 incident-1234 而取代了舊的 SSO bridge。
參考 AUTH-456。

## Requirements

### Requirement: Rate Limiting
系統 SHALL 在 60 秒內失敗 5 次後拒絕登入請求。

**Source:** auth.py:18-21, [JIRA AUTH-456]

#### Scenario: 連續失敗後鎖定
- **GIVEN** 過去一分鐘內已有 5 次失敗
- **WHEN** 又一個 POST /auth/login 進來
- **THEN** server 回傳 429
```

## 狀態

**v0.3 alpha**。提供：
- `/inferspec-scan` — bulk 模式，加上 design-doc 自動發掘、OpenAPI/Swagger 偵測、
  `--since <rev>` 增量掃描、術語表強制（`.inferspec-glossary.txt`）、移除提案
  （寫到 `openspec/changes/` 而非靜默刪除）
- `/inferspec-cap <slug>` — 互動式單 cap 模式，也涵蓋既有 spec 的 gap-fill
- `inferspec update` — 各 repo 重新刷新已安裝的 skill bundle

## License

MIT
