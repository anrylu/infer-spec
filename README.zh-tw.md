[English](/README.md) | [繁體中文](/README.zh-tw.md) | [简体中文](/README.zh-cn.md) | [日本語](/README.ja.md)

# InferSpec

**從你的程式碼 + Git 歷史 + 文件反向推導出 OpenSpec 規格** —
專為沒有規格的 legacy code 設計。

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **From Code & Context to Clear Specs**

## 為什麼需要 InferSpec？

你接手一個五萬行的 Flask 服務。沒有規格文件。有一個三年沒人動的 Jira 看板、一份沒人更新的 Confluence wiki、跟一份 Git log。

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

這會把 `/inferspec-scan` 安裝到當前目錄的 `.claude/skills/`。完整支援平台清單可用 `inferspec platforms` 查看。

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

**v0.2 alpha**。提供 `/inferspec-scan`（bulk 模式）+ `/inferspec-cap`（互動式
單 cap 模式）。`/inferspec-refine` 視 v0.3 評估。

## License

MIT
