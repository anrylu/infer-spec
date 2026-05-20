[English](/README.md) | [繁體中文](/README.zh-tw.md) | [简体中文](/README.zh-cn.md) | [日本語](/README.ja.md)

# InferSpec

**コードベース + Git 履歴 + ドキュメントから OpenSpec 仕様書を逆推論** —
仕様書のない legacy code のために設計されています。

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **From Code & Context to Clear Specs**

## なぜ InferSpec？

あなたは 5 万行ある Flask サービスを引き継いだ。仕様書は存在しない。3 年放置された Jira ボード、誰も更新しない Confluence wiki、そして Git log だけがある。

**InferSpec はその全てを読み**、構造化された OpenSpec 仕様書を生成します — capability ごとに 1 つの `spec.md`、各 Requirement は `file:line` または ticket ID へ引用付き。AI が不確実な箇所は `[GAP]`/`[TBD]` でマークされ、後でインタラクティブに埋められます。

## 仕組み

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — uvx Python パッケージ: installer + CLI            │
│  （LLM API は決して呼びません）                                │
└─────────────────────────────────────────────────────────────┘
                       │ skill をインストール
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Skill は Claude Code / Codex / Gemini / Copilot  │
│  / OpenCode 内で動作し、host の subscription AI を使う          │
└─────────────────────────────────────────────────────────────┘
```

InferSpec はあなたが既に契約している AI サブスクリプションに依存します。API key も不要、クラウド endpoint の設定も不要です。

## インストール

```bash
uvx inferspec init --platform claude-code
```

これでカレントディレクトリの `.claude/skills/` に `/inferspec-scan` がインストールされます。サポート対象プラットフォームの全リストは `inferspec platforms` で確認できます。

## 使い方

対象 repo で AI agent を開く。2 つの skill が利用可能：

**`/inferspec-scan`** — bulk モード、全 capability の spec を一括推論：

```
/inferspec-scan
```

`graphify` でファイルを capability にクラスタリングし、各 cap ごとに code +
`git log` + `docs/` + (利用可能なら) MCP 経由の Jira/Confluence + host の
WebFetch 経由の URL を読み、OpenSpec 形式で `openspec/specs/<cap>/spec.md` を
生成。AI が不確実な箇所は `[GAP]` / `[TBD]` でマーク。

**`/inferspec-cap <slug>`** — 単一 cap の深掘り + インタラクティブ Q&A：

```
/inferspec-cap user-auth
/inferspec-cap "rate limiting"       # ファジーマッチ
/inferspec-cap                       # インタラクティブ選択
/inferspec-cap new-feature --new     # 新規 cap bootstrap
```

単一 cap について、skill が Jira/Confluence/URL を能動的に尋ね、各 `[GAP]`
マーカーに対し焦点を絞った質問を spec が収束するまで 1 つずつ提示。終了時に
コミット要否を確認。

外部データソース（Jira、Confluence、URL）は自動処理 — InferSpec は host 環境
の MCP server を検出するため、独自 client は持たない。

## 出力フォーマット

[OpenSpec](https://github.com/Fission-AI/OpenSpec) と同じ規約：

```markdown
## Purpose

注文ポータルのユーザー認証 — incident-1234 を受けて旧 SSO bridge を置き換え。
AUTH-456 参照。

## Requirements

### Requirement: Rate Limiting
システムは 60 秒以内に 5 回失敗したログイン試行を SHALL 拒否する。

**Source:** auth.py:18-21, [JIRA AUTH-456]

#### Scenario: 連続失敗後のロックアウト
- **GIVEN** 過去 1 分以内に 5 回失敗
- **WHEN** さらに POST /auth/login が到達
- **THEN** server が 429 を返す
```

## ステータス

**v0.2 alpha**。`/inferspec-scan`（bulk モード）+ `/inferspec-cap`
（インタラクティブ単一 cap モード）を提供。`/inferspec-refine` は v0.3 で評価。

## License

MIT
