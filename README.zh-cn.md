[English](/README.md) | [繁體中文](/README.zh-tw.md) | [简体中文](/README.zh-cn.md) | [日本語](/README.ja.md)

# InferSpec

**从你的代码 + Git 历史 + 文档反向推导出 OpenSpec 规范** —
专为没有规范的 legacy code 设计。

[![CI](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml/badge.svg)](https://github.com/anrylu/infer-spec/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Development-Driven Spec (DDS)** — Spec-Driven Development 的反向操作。
> From Code & Context to Clear Specs.

## SDD vs DDS

[Spec-Driven Development（SDD）](https://github.com/Fission-AI/OpenSpec)是"先写
规范，再写代码"的开发纪律，对 greenfield 项目非常合适。

**但真实世界大多是 brownfield。** 你接手一个五万行的 Flask 服务，没有规范 —
只有三年没人动的 Jira 看板、没人更新的 Confluence wiki、还有一份 Git log。SDD
在这里完全找不到切入点。

**InferSpec 把这个流程反过来，叫做 Development-Driven Spec（DDS）。** 代码
已经在那里 — 把它（加上 git 历史、ticket、docs、MCP 连到的 wiki）当作真实
来源，*反向推导*出一份结构化的 OpenSpec 规范。规范存在之后，你可以切回 SDD
来做新功能。

| 模式 | 起点 | 产物 |
|------|------|------|
| **SDD**（Spec-Driven Development） | 规范 | 代码 |
| **DDS**（Development-Driven Spec） | 代码 + 历史 + 文档 | 规范 |

## 为什么需要 InferSpec？

**InferSpec 会把这些都读一遍**，产出结构化的 OpenSpec 规范 — 每个 capability 一份 `spec.md` — 并且每条 Requirement 都会回引到 `file:line` 或 ticket ID。AI 不确定的地方会标 `[GAP]`/`[TBD]`，让你之后可以互动式地补充。

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — uvx Python 包：installer + CLI                    │
│  （永远不会调用 LLM API）                                       │
└─────────────────────────────────────────────────────────────┘
                       │ 把 skill 安装到
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Skill 在 Claude Code / Codex / Gemini / Copilot  │
│  / OpenCode 内执行，使用 host 的 subscription AI               │
└─────────────────────────────────────────────────────────────┘
```

InferSpec 完全依赖你已经订阅的 AI 服务。不需要 API key、不需要配置云端 endpoint。

## 安装

```bash
uvx inferspec init --platform claude-code
```

这会把 `/inferspec-scan` + `/inferspec-cap` 安装到当前目录的 `.claude/skills/`。
完整支持平台列表可用 `inferspec platforms` 查看。

### 更新

新版 `inferspec` 套件发布后，各 repo 里 `.claude/skills/`（或等效路径）下的
skill 文件仍停留在当初安装的版本。用以下方式更新：

```bash
pip install -U inferspec        # 或：uvx --refresh inferspec ...
inferspec update                # 在每个跑过 `inferspec init` 的 repo 执行
```

`inferspec update` 会读 `.inferspec.yaml` 找出当初安装的 platforms，然后重新
复制 skill bundle（不会再问问题）。用 `inferspec update --check` 只看版本差
异不写文件；`inferspec doctor` 会列出每个 platform 的"已安装版本 vs 套件版本"。

## 使用方式

在目标 repo 打开你的 AI agent。提供两个 skill：

**`/inferspec-scan`** — bulk 模式，一次推所有 capability 的 spec：

```
/inferspec-scan
```

执行 `graphify` 将文件分组成 capability，对每个 cap 读取 code + `git log` +
`docs/` + (如果可用) MCP 的 Jira/Confluence + host WebFetch 的 URL，产出 OpenSpec
格式的 `openspec/specs/<cap>/spec.md`。AI 不确定的部分会标 `[GAP]` / `[TBD]`。

**`/inferspec-cap <slug>`** — 单一 cap 深推 + 互动式 Q&A：

```
/inferspec-cap user-auth
/inferspec-cap "rate limiting"       # 模糊匹配
/inferspec-cap                       # 互动式选择
/inferspec-cap new-feature --new     # 新 cap bootstrap
```

对单一 cap，skill 会主动询问你有没有 Jira/Confluence/URL，然后针对每个 `[GAP]`
marker 问一个聚焦问题直到 spec 收敛。结束时会问你要不要直接 commit。

外部数据源（Jira、Confluence、URL）会自动处理 — InferSpec 检测你 host 环境
里的 MCP server，不自己维护 client。

## 输出格式

跟 [OpenSpec](https://github.com/Fission-AI/OpenSpec) 同一套约定：

```markdown
## Purpose

订单入口的用户认证 — 因为 incident-1234 而取代了旧的 SSO bridge。
参考 AUTH-456。

## Requirements

### Requirement: Rate Limiting
系统 SHALL 在 60 秒内失败 5 次后拒绝登录请求。

**Source:** auth.py:18-21, [JIRA AUTH-456]

#### Scenario: 连续失败后锁定
- **GIVEN** 过去一分钟内已有 5 次失败
- **WHEN** 又一个 POST /auth/login 进来
- **THEN** server 返回 429
```

## 状态

**v0.3 alpha**。提供：
- `/inferspec-scan` — bulk 模式，加上 design-doc 自动发掘、OpenAPI/Swagger 检测、
  `--since <rev>` 增量扫描、术语表强制（`.inferspec-glossary.txt`）、移除提案
  （写到 `openspec/changes/` 而非静默删除）
- `/inferspec-cap <slug>` — 互动式单 cap 模式，也涵盖既有 spec 的 gap-fill
- `inferspec update` — 各 repo 重新刷新已安装的 skill bundle

## License

MIT
