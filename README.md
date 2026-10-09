# AI Development Skills

AI 主导开发全流程，人工只在关键节点审核。

本项目以 **AI 主导开发** 为核心，旨在将从需求分析、方案设计到开发落地的关键环节沉淀为可复用技能。AI 持续推进各阶段工作，人工主要审核关键成果，仅在存在重要歧义或需要纠偏时介入，形成高效、可追踪的开发流程。

目前为 **Codex** 和 **Hermes** 提供需求分析与技术设计两个技能，通过统一的场景编号关联需求与设计文档，逐步完善从需求到落地的开发流程。

[快速开始](#快速开始) · [使用](#使用) · [安装与管理](#安装与管理) · [开发](#开发) · [常见问题](#常见问题)

## 特点

- **需求先行**：澄清关键业务规则，明确正常流程、异常边界与验收标准。
- **场景可追踪**：使用稳定的 `S-001` 等编号，将需求场景与详细设计、接口、数据结构关联起来。
- **贴合现有项目**：沿用已有代码、接口、数据结构与项目规范，不凭空建立另一套设计。
- **轻量安装**：技能和模板随 CLI 分发，仅支持 Codex、Hermes，每次完整安装两个技能。

| 技能 | 负责什么 | 输出文档 |
| --- | --- | --- |
| `ai-devlop-spec` | 需求澄清、业务场景、验收标准 | `需求分析.md` |
| `ai-devlop-plan` | 场景实现方案、接口与数据结构设计 | `详细设计.md`、`接口设计.md`、`数据结构设计.md` |

当前版本仅覆盖需求分析与技术设计，不自动生成任务清单、编写业务代码或执行部署。场景编号用于文档追踪，不代表相应代码已经实现。

## 快速开始

### 1. 准备环境

- 已安装 **Codex** 或 **Hermes**。
- 已安装 **[uv](https://docs.astral.sh/uv/getting-started/installation/)**。
- CLI 使用 **Python 3.10+**；uv 可以按需获取 Python。

> [!NOTE]
> CLI 从 GitHub 仓库获取，尚未发布到 PyPI。以下命令需要能够访问 GitHub。

### 2. 安装技能

根据使用的 Agent，选择一条命令：

```bash
# Codex
uvx --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@main" ai-devlop install --agent codex
```

```bash
# Hermes
uvx --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@main" ai-devlop install --agent hermes
```

两种模式均安装 `ai-devlop-spec` 和 `ai-devlop-plan`。首次获取或构建工具可能需要联网；技能与模板从安装包读取，不另外下载。

### 3. 开始使用

开启新的 Agent 会话，先调用需求分析技能，确认需求后再调用设计技能。若 Codex 未显示新技能，可尝试重启。

## 使用

下面的内容输入到 **Agent 对话中**，不是终端命令。

### Codex

```text
$ai-devlop-spec 支持用户取消未发货订单。请澄清取消条件、退款规则和异常场景，输出到 docs/requirements/订单取消/。

$ai-devlop-plan 根据 docs/requirements/订单取消/需求分析.md 和当前项目生成技术设计。
```

### Hermes

```text
/ai-devlop-spec 支持用户取消未发货订单。请澄清取消条件、退款规则和异常场景，输出到 docs/requirements/订单取消/。

/ai-devlop-plan 根据 docs/requirements/订单取消/需求分析.md 和当前项目生成技术设计。
```

需求分析负责明确“做什么”，技术设计负责说明“如何做”。设计阶段沿用需求中的场景编号；需求仍有关键歧义时，应先澄清。

默认输出结构：

```text
docs/requirements/订单取消/
├── 需求分析.md
├── 详细设计.md
├── 接口设计.md
└── 数据结构设计.md
```

用户指定路径与现有项目约定优先。已有文档会先读取，再按本次需求修订。

## 安装与管理

### 安装命令工具

经常给不同项目安装技能时，可以长期安装 CLI：

```bash
uv tool install ai-devlop-cli --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@main"
```

之后可以在任意目录使用 `ai-devlop`。以下示例使用已安装的 CLI；不长期安装时，继续用上面的 `uvx --from ... ai-devlop ...` 形式执行。在本地源码目录开发时，也可以使用 `uvx --from . ai-devlop ...`。

### 用户级与项目级安装

```bash
# 用户级：对当前用户的项目可用
ai-devlop install --agent codex

# 项目级：仅写入当前已有项目
ai-devlop init --agent codex --here

# 显式指定已有项目
ai-devlop init --agent codex --project "./my-project"
```

将 `codex` 替换为 `hermes` 即选择 Hermes 模式。不自动创建项目或初始化 Git。

| Agent | 用户级技能目录 | 项目级技能目录 |
| --- | --- | --- |
| Codex | `~/.agents/skills/` | `<项目>/.agents/skills/` |
| Hermes | `$HERMES_HOME/skills/`；未设置时见下方说明 | `<项目>/.hermes/skills/` |

Hermes 未设置 `HERMES_HOME` 时，Windows 默认使用 `%LOCALAPPDATA%/hermes/skills/`，其他平台使用 `~/.hermes/skills/`。命名 profile 应显式设置 `HERMES_HOME` 指向相应 profile；安装器不自动推断桌面当前 profile。

> [!IMPORTANT]
> Hermes 项目级安装必须指定包含 `.git` 目录或 worktree 文件的 Git 根目录。安装后由用户在项目内执行 `hermes skills trust`，再开启新会话。安装器不会自动修改信任配置；较旧 Hermes 版本若不支持项目技能，请使用用户级安装。

### 检查与更新

```bash
# 查看用户级安装状态
ai-devlop status --agent codex

# 预览并更新用户级技能
ai-devlop update --agent codex --dry-run
ai-devlop update --agent codex

# 检查或更新当前项目
ai-devlop status --agent codex --here
ai-devlop update --agent codex --here
```

更新工具与更新技能是两个步骤。本地源码更新后，在源码根目录执行：

```bash
uv tool install --force .
ai-devlop update --agent codex
```

`update` 只使用当前 CLI 携带的资源，不联网选择最新版本。使用 `uvx` 运行本地新版时，必要时添加 uv 的 `--refresh` 选项。

### 覆盖与恢复

相同内容会跳过；不同内容在首次安装时默认阻止覆盖。更新需要两个技能已完整安装，并通过上次安装记录确认没有本地修改。

确认需要覆盖本地修改时，先预览，再执行：

```bash
ai-devlop update --agent codex --force --dry-run
ai-devlop update --agent codex --force
```

旧资源会先备份，两个技能提交失败时会尝试整体回滚。安装记录与备份位于技能目录旁的 `ai-devlop/install.json`、`ai-devlop/backups/`。不修改其他技能、Agent 配置、`AGENTS.md` 或业务文档，也不自动清理备份。

## 开发

```bash
# 构建源码包和 wheel
uv build

# 运行测试，使用隔离临时目录
uv run --no-project --with . python -m unittest discover -s tests -v
```

```text
.
├── .agents/skills/       # 技能定义与模板，唯一维护源
│   ├── ai-devlop-spec/
│   └── ai-devlop-plan/
├── src/ai_devlop/        # CLI 实现
├── tests/               # 安装逻辑与安装包验证
├── pyproject.toml
└── README.md
```

模板保存在各技能的 `assets/` 中，构建时收入安装包。修改技能或模板后，应重新构建并验证资源完整性；不要维护第二份模板。

## 常见问题

### 能否只安装一个技能，或安装到其他 Agent？

不能。目前仅支持 Codex、Hermes，两个技能作为一个完整组合安装和更新。

### 能否直接从 GitHub 或 PyPI 一行安装？

可以按“快速开始”中的命令直接从 GitHub 安装；当前尚未发布到 PyPI，因此不能使用 `uvx --from ai-devlop-cli`。需要稳定复现时，应在命令中使用已发布的版本标签或提交哈希代替 `@main`。

### 检查状态正常，为什么 Agent 没有显示技能？

`status` 只检查文件与安装记录，不验证 Agent 是否启用或实际加载。请确认 Agent 的目录、当前 profile 和会话；Hermes 项目技能还需要用户信任。

### 安装被强制中断后怎么办？

断电或强制结束进程可能留下 `.lock`、备份或暂存目录。先确认没有安装进程运行，再检查错误提示中的恢复文件，最后清理锁并重试。损坏的安装记录、链接和 junction 路径不会被 `--force` 绕过；不保证跨进程崩溃自动恢复。

## 参考

本项目借鉴 [Spec Kit](https://github.com/github/spec-kit) 的需求先行与命令式安装思路，保留需求分析、技术设计两个阶段。

- [Codex 技能说明](https://developers.openai.com/codex/skills)
- [Hermes 技能说明](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)
- [uv 文档](https://docs.astral.sh/uv/)
