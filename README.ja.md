[English](/README.md) | [繁體中文](/README.zh-tw.md) | [简体中文](/README.zh-cn.md) | [日本語](/README.ja.md)

# InferSpec

**コードベース + Git 履歴 + ドキュメントから OpenSpec 仕様書を逆推論** —
仕様書のない legacy code のために設計されています。

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Development-Driven Spec (DDS)** — Spec-Driven Development の逆向きの実践。
> From Code & Context to Clear Specs.

## SDD vs DDS

[Spec-Driven Development（SDD）](https://github.com/Fission-AI/OpenSpec)は、
まず仕様書を書き、それに沿って実装するという開発規律で、greenfield プロジ
ェクトには非常に有効です。

**しかし現実の多くは brownfield。** あなたは 5 万行ある Flask サービスを引き
継いだ。仕様書は存在しない — 3 年放置された Jira ボード、誰も更新しない
Confluence wiki、そして Git log だけ。SDD はここに入口がありません。

**InferSpec はこのループを反転させます — Development-Driven Spec（DDS）。**
コードはすでに存在する。これ（＋ git 履歴、チケット、ドキュメント、MCP 接続
の wiki）を真実の源として扱い、構造化された OpenSpec 仕様書を*逆推論*し
ます。仕様書が揃ったら、新機能には SDD に戻ればよい。

| モード | 起点 | 成果物 |
|--------|------|--------|
| **SDD**（Spec-Driven Development） | 仕様書 | コード |
| **DDS**（Development-Driven Spec） | コード + 履歴 + ドキュメント | 仕様書 |

## なぜ InferSpec？

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

これでカレントディレクトリの `.claude/skills/` に `/inferspec-scan` +
`/inferspec-cap` がインストールされます。サポート対象プラットフォームの全
リストは `inferspec platforms` で確認できます。

### アップデート

`inferspec` パッケージの新版がリリースされても、各 repo の `.claude/skills/`
（または同等のパス）配下にある skill ファイルはインストール時のバージョン
のままです。次の手順で更新してください：

```bash
pip install -U inferspec        # または：uvx --refresh inferspec ...
inferspec update                # `inferspec init` を実行した各 repo で
```

`inferspec update` は `.inferspec.yaml` を読み込み、以前選んだ platforms に対
して skill bundle を再コピーします（再質問なし）。`inferspec update --check`
で書き込みなしのドリフト確認、`inferspec doctor` で platform ごとの「インス
トール済み vs パッケージ」バージョン比較が可能です。

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

**v0.3 alpha**。以下を提供：
- `/inferspec-scan` — bulk モード、加えて design-doc 自動探索、OpenAPI/Swagger
  検出、`--since <rev>` 増分スキャン、用語集の強制（`.inferspec-glossary.txt`）、
  削除提案（静かに消さず `openspec/changes/` に出力）
- `/inferspec-cap <slug>` — インタラクティブ単一 cap モード、既存 spec の
  gap-fill にも対応
- `inferspec update` — 各 repo でインストール済み skill bundle を再リフレッシュ

## License

MIT
