# AI Development Skills

AI 主导开发全流程，人工只在关键节点审核。

本项目以 **AI 主导开发** 为核心，旨在将从需求分析、方案设计到开发落地的关键环节沉淀为可复用技能。AI 持续推进各阶段工作，人工主要审核关键成果，仅在存在重要歧义或需要纠偏时介入，形成高效、可追踪的开发流程。

本项目为 **Codex** 和 **Hermes** 提供项目宪法、需求分析、需求澄清、技术设计、任务拆分、一致性检查、实现与实现验证八个技能，通过统一的场景编号关联需求与设计文档，逐步完善从需求到落地的开发流程。

[快速开始](#快速开始) · [使用](#使用) · [安装与管理](#安装与管理) · [开发](#开发) · [分支管理](#分支管理) · [常见问题](#常见问题)

## 特点

- **需求先行**：澄清关键业务规则，明确正常流程、异常边界与验收标准。
- **场景可追踪**：使用稳定的 `S-001` 等编号，将需求场景与详细设计、接口、数据结构关联起来。
- **贴合现有项目**：沿用已有代码、接口、数据结构与项目规范，不凭空建立另一套设计。
- **轻量安装**：技能和模板随 CLI 分发，仅支持 Codex、Hermes，每次完整安装八个技能。

| 技能 | 负责什么 | 输出文档 |
| --- | --- | --- |
| `ai-devlop-constitution` | 编写、修订两级项目宪法及专业规范 | `.ai-dev/memory/` 下的四份规范 |
| `ai-devlop-spec` | 需求整理、业务场景、验收标准 | `需求分析.md`、原始输入留存 |
| `ai-devlop-clarify` | 专项澄清并同步已有需求、设计及任务，保持上下文一致 | 修订原有文档、原始输入留存；不新增澄清报告 |
| `ai-devlop-plan` | 场景实现方案、接口与数据结构设计 | `详细设计.md`、`接口设计.md`、`数据结构设计.md` |
| `ai-devlop-task` | 将需求实现划分为一个或多个任务，明确范围、依赖与完成标准 | `任务清单.md` |
| `ai-devlop-check` | task 后检查需求、设计、任务的一致性、完整性及宪法符合性 | `一致性检查.md` |
| `ai-devlop-implement` | 按任务依赖完成全部实现、验证并同步任务状态 | 项目代码与必要测试、`实现记录.md` |
| `ai-devlop-verify` | implement 后独立核对真实实现、需求覆盖、验证证据及宪法符合性 | `实现验证.md` |

当前源码覆盖项目宪法及需求到实现验证的八技能流程。需求、澄清、设计和任务技能负责文档规划；明确调用实现技能后，按任务修改代码、执行必要验证并更新完成状态，不自动提交、发布或部署。任务勾选以真实完成标准为依据。

## 快速开始

### 1. 准备环境

- 已安装 **Codex** 或 **Hermes**。
- 已安装 **[uv](https://docs.astral.sh/uv/getting-started/installation/)**。
- CLI 使用 **Python 3.10+**；uv 可以按需获取 Python。

> [!NOTE]
> CLI 从 GitHub 版本标签获取，尚未发布到 PyPI。以下命令需要能够访问 GitHub。

### 2. 安装技能

根据使用的 Agent，选择一条命令：

```bash
# Codex
uvx --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@v0.4.1" ai-devlop install --agent codex
```

```bash
# Hermes
uvx --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@v0.4.1" ai-devlop install --agent hermes
```

两种模式均安装上表中的完整八技能组合。`v0.4.1` 新增 UI UX Pro Max 自动可选联动：涉及页面时自动尝试调用，不可用或失败时跳过，无需主动启用，不增加外部依赖。`v0.4.0` 新增两级项目宪法、实施前一致性检查和实现后验证，默认需求文档目录统一为 `ai-dev-docs/requirements/`。原 `v0.3.2` 为五技能组合，`v0.2.0` 为四技能组合，`v0.1.0` 仅包含需求分析与技术设计。首次获取或构建工具可能需要联网；技能与模板从安装包读取，不另外下载。

### 3. 开始使用

开启新的 Agent 会话，先调用需求分析技能，需要专项澄清时调用澄清技能，确认需求后再调用设计技能，设计明确后调用任务拆分技能，任务拆分后可调用一致性检查技能，审核任务后调用实现技能，实现后可调用实现验证技能。若 Codex 未显示新技能，可尝试重启。

## 使用

### constitution：项目宪法

`constitution` 是 Agent 技能命令：Codex 使用 `$ai-devlop-constitution`，Hermes 使用 `/ai-devlop-constitution`，不是终端子命令。`v0.4.0` 已包含完整八技能组合。

```text
# Codex 对话
$ai-devlop-constitution 结合当前项目编写项目宪法，L1 控制在 5～8 条核心原则，并制定工程、架构和安全规范。

# Hermes 对话
/ai-devlop-constitution 根据现有项目修订安全规范，并检查与 L1 和其他 L2 规范的内部一致性。
```

本项目使用 `.ai-dev/` 存放项目级治理资料，采用 `memory/` 子目录：

```text
.ai-dev/
└── memory/
    ├── constitution.md   # L1：长期有效、跨专业共同遵守的根本原则
    ├── engineering.md     # L2：工程实施要求
    ├── architecture.md    # L2：系统结构、职责及技术设计约束
    └── security.md        # L2：安全原则、控制及验证要求
```

L1 文件名为 `constitution.md`。L1 建议 5～8 条原则，不承载完整工程规范或详细技术实现；L2 细化但不得覆盖 L1。架构规范必须结合真实项目制定，不直接套用通用架构模式。

- **工程规范**：Coding Standards、Code Quality、Testing、Dependency Management、Error Handling、Logging、Build、CI/CD、Documentation。
- **架构规范**：Architecture Style、Layer Boundary、Module Boundary、Dependency Rules、Data Ownership、API Contract、Transaction Boundary、Integration、Extensibility、Architecture Testing。
- **安全规范**：Authentication、Authorization、Data Isolation、Sensitive Data、Input Validation、Secure Communication、Audit Logging、Dependency Security、Error Handling、Security Testing。

技能先读取已有规范和项目证据，再编写或定向修订；支持草案、批准状态、语义版本、批准与修订日期、宪法内部一致性检查。未知项明确待确认，不把模板当作已批准事实。只修改本次治理范围内的规范，不自动修改业务代码或下游文档，不自动提交。

后续七个技能在运行时读取这些规范并检查一致性。规范缺失不会自动创建文件，也不会无条件阻断旧项目；只有影响当前任务的关键缺口才需要澄清。安装和更新技能仅安装模板，不会在项目中生成或覆盖 `.ai-dev/`，实际规范由调用宪法技能时编写。需求文档继续保留在 `ai-dev-docs/requirements/`，不迁移到 `.ai-dev/`。

下面的内容输入到 **Agent 对话中**，不是终端命令。

### Codex

```text
$ai-devlop-spec 支持用户取消未发货订单。需求编号为 XQ20261009-001，请澄清取消条件、退款规则和异常场景。

$ai-devlop-clarify 检查 ai-dev-docs/requirements/XQ20261009-001/ai-devlop-spec/需求分析.md 中的关键歧义，逐项确认并同步调整已有需求、设计及任务文档。

$ai-devlop-plan 根据 ai-dev-docs/requirements/XQ20261009-001/ai-devlop-spec/需求分析.md 和当前项目生成技术设计。

$ai-devlop-task 根据 ai-dev-docs/requirements/XQ20261009-001/ 下的需求与设计，将实现划分为一个或多个任务。

$ai-devlop-check 检查 ai-dev-docs/requirements/XQ20261009-001/ 下的需求、设计和任务是否一致、完整且符合宪法。

$ai-devlop-implement 根据 ai-dev-docs/requirements/XQ20261009-001/ai-devlop-task/任务清单.md 完成全部任务并验证结果。

$ai-devlop-verify 核对 XQ20261009-001 的代码是否完整实现需求，并检查验证证据和宪法符合性。
```

### Hermes

```text
/ai-devlop-spec 支持用户取消未发货订单。需求编号为 XQ20261009-001，请澄清取消条件、退款规则和异常场景。

/ai-devlop-clarify 检查 ai-dev-docs/requirements/XQ20261009-001/ai-devlop-spec/需求分析.md 中的关键歧义，逐项确认并同步调整已有需求、设计及任务文档。

/ai-devlop-plan 根据 ai-dev-docs/requirements/XQ20261009-001/ai-devlop-spec/需求分析.md 和当前项目生成技术设计。

/ai-devlop-task 根据 ai-dev-docs/requirements/XQ20261009-001/ 下的需求与设计，将实现划分为一个或多个任务。

/ai-devlop-check 检查 ai-dev-docs/requirements/XQ20261009-001/ 下的需求、设计和任务是否一致、完整且符合宪法。

/ai-devlop-implement 根据 ai-dev-docs/requirements/XQ20261009-001/ai-devlop-task/任务清单.md 完成全部任务并验证结果。

/ai-devlop-verify 核对 XQ20261009-001 的代码是否完整实现需求，并检查验证证据和宪法符合性。
```

需求分析负责明确“做什么”，专项澄清用于检查已有需求、逐项确认关键缺口并立即同步已有需求、设计及任务的对应章节，不生成独立澄清文档；没有关键歧义时无需额外澄清。技术设计负责说明“如何做”。设计阶段沿用需求中的场景编号；任务拆分按业务交付结果划分，简单需求可只有一个任务，每个任务写清场景覆盖、实现位置、前置依赖和完成标准。需求仍有关键歧义时，应先澄清。任务清单生成后不会自动开始实施；调用实现技能后，默认按依赖顺序完成全部未完成任务，验证通过才勾选。遇到阻塞时保留真实未完成状态，继续不受影响的任务。

### UI UX Pro Max：自动可选联动

涉及页面、界面或 UI/UX 的工作，技能自动尝试调用外部 `ui-ux-pro-max`（UI UX Pro Max），无需用户主动启用或额外确认；不涉及界面的工作跳过，用户明确禁止时不调用。

- **可用时按阶段使用**：需求与澄清辅助识别体验约束，设计形成页面与交互方案，任务拆分承接既有设计，实现沿用确定方案，check / verify 辅助只读核对。不会因联动自动推进下一阶段或扩大授权。
- **不可用即跳过**：未安装、无法发现或加载、调用失败及能力不支持时，主动放弃本次调用，不反复重试、不追问、不阻塞、不自动安装或下载依赖；交付时简短说明一次即可。没有外部技能仍可独立完成原流程。
- **项目规范优先**：沿用已有技术栈、组件库和设计系统；外部建议不自动成为业务规则或项目强制要求，不擅自更换全站风格。采用的设计写进现有详细设计，后续不依赖再次调用才能理解。
- **验证依据真实证据**：调用成功不等于 UI 验收通过，构建成功也不等于视觉、响应式或交互验证通过。缺少实际页面证据时如实标明未验证。

本项目仍只安装和管理八个技能，不捆绑、安装或更新 UI UX Pro Max，不增加 CLI 开关或运行时依赖。外部技能可由用户按 [UI UX Pro Max 上游说明](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) 单独安装；以当前 Agent 实际可发现和可调用的能力为准，不保证不同 Agent 的调用方式一致。

### check 与 verify：两个独立质量检查节点

推荐顺序：`spec → clarify（按需）→ plan → task → check → implement → verify`。所有技能均由用户明确调用，不自动触发下一步；未生成 check 报告不阻止 verify 独立核对。

- **check**：只读核对本需求的原始输入、需求、已有设计与任务，检查场景覆盖、术语与契约一致性、依赖、完成标准和已批准宪法规则。不会检查实现是否完成，也不运行构建或测试。
- **verify**：对照需求及验收标准检查真实代码、入口调用链、异常边界、数据和权限、测试与任务状态证据。可执行授权范围内已有的安全本地构建与测试，不把任务勾选、实现记录、静态阅读或测试通过单独当作完整实现的证明。
- 两个技能只写各自报告，不修改源文档、代码、宪法或任务勾选；仅咨询或明确禁止写入时在会话交付。重复执行更新原报告，不为每次运行新增副本。问题严重程度与宪法规则强度分开记录。
- 报告区分通过、发现问题、未验证与不适用；缺少材料、宪法或执行环境时明确限制，不伪称通过。无法协调的规范冲突交由用户决策，不自动修宪或认定例外成立。

默认输出结构：

```text
ai-dev-docs/requirements/XQ20261009-001/
├── 原始需求/
│   ├── 原始需求.md
│   └── 输入文件/
│       └── 20261009-143025-123-业务需求.docx
├── ai-devlop-spec/
│   └── 需求分析.md
├── ai-devlop-plan/
│   ├── 详细设计.md
│   ├── 接口设计.md
│   └── 数据结构设计.md
├── ai-devlop-task/
│   └── 任务清单.md
├── ai-devlop-check/
│   └── 一致性检查.md
├── ai-devlop-implement/
│   └── 实现记录.md
└── ai-devlop-verify/
    └── 实现验证.md
```

需求编号优先使用用户输入明确指定的编号，否则读取输入文件中的编号；同一需求在不同技能间沿用编号。没有编号时，按执行当天日期自动生成 `XQYYYYMMDD-XXX`，从 `001` 开始，目录或文件已占用则自增。需求编号写入产出文档头部。

生成新文档的技能分别落地到以技能名命名的子目录；澄清技能在原位置修订已有文档，不创建独立澄清产出目录；实现代码与测试仍放在项目规定位置，任务状态在原任务清单中更新。用户指定输出根目录时仍保留 `<需求编号>/<技能名>/` 结构；明确指定完整文件路径或修订既有文件时按指定位置处理。已有文档会先读取，再按本次需求修订。

`spec` 和 `clarify` 共用同一需求下的 `原始需求/原始需求.md`，所有调用输入、补充、纠正和澄清回答按时间正序列在这一个文件中。文件头统一注明需求编号和时区，每条仅用时间、技能、输入类型标题及用户原文；必要时补充来源和简短回答的问题上下文。输入文件与附件单独保存在 `原始需求/输入文件/`，对应记录用相对链接指引，不重复嵌入文件正文；副本用时间戳加原文件名命名，重名追加序号。历史原文保留，敏感值脱敏，未取得的材料注明来源。留存不代表业务规则已确认；用户明确禁止写文件时不留存。

## 安装与管理

### 安装命令工具

经常给不同项目安装技能时，可以长期安装 CLI：

```bash
uv tool install ai-devlop-cli --from "git+https://github.com/theron-muqiu/AI-Development-Skills.git@v0.4.1"
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

更新工具与更新技能是两个步骤。新 CLI 支持将有有效安装记录、无本地修改的原两技能、三技能、四技能、五技能及六技能组合升级为八技能组合；新增技能目录存在冲突时仍需先检查，不能静默覆盖。发布新版本标签后，在上面的 `uv tool install` 命令中改用新标签并增加 `--force`，随后执行 `ai-devlop update --agent codex`（或 `hermes`）。`update` 只使用当前 CLI 携带的资源，不联网选择最新版本。

### 覆盖与恢复

相同内容会跳过；不同内容在首次安装时默认阻止覆盖。更新需要全部技能已完整安装，并通过上次安装记录确认没有本地修改。

确认需要覆盖本地修改时，先预览，再执行：

```bash
ai-devlop update --agent codex --force --dry-run
ai-devlop update --agent codex --force
```

旧资源会先备份，技能组合提交失败时会尝试整体回滚。安装记录与备份位于技能目录旁的 `ai-devlop/install.json`、`ai-devlop/backups/`。不修改其他技能、Agent 配置、`AGENTS.md` 或业务文档，也不自动清理备份。

## 开发

```bash
# 构建源码包和 wheel
uv build

# 运行测试，使用隔离临时目录
uv run --no-project --with . python -m unittest discover -s tests -v
```

```text
.
├── skills/               # 技能定义与模板，唯一维护源
│   ├── ai-devlop-constitution/
│   ├── ai-devlop-spec/
│   ├── ai-devlop-clarify/
│   ├── ai-devlop-plan/
│   ├── ai-devlop-task/
│   ├── ai-devlop-check/
│   ├── ai-devlop-implement/
│   └── ai-devlop-verify/
├── src/ai_devlop/        # CLI 实现
├── tests/               # 安装逻辑与安装包验证
├── pyproject.toml
└── README.md
```

模板保存在各技能的 `assets/` 中，构建时收入安装包。修改技能或模板后，应重新构建并验证资源完整性；不要维护第二份模板。

## 分支管理

采用适合小型项目的短期分支流程：`main` 保存可安装的稳定内容，日常修改从最新 `main` 创建工作分支，通过 Pull Request 合并。

| 分支 | 用途 |
| --- | --- |
| `main` | 稳定主线；发布标签从这里创建 |
| `feature/<主题>` | 新技能或功能 |
| `fix/<主题>` | 错误修复 |
| `docs/<主题>`、`chore/<主题>` | 文档或维护工作 |

1. 从最新 `main` 创建短期分支，保持一个分支只处理一个主题。
2. 完成后运行 `uv build` 和测试，将分支推送到 GitHub，并向 `main` 提交 Pull Request。
3. 审核通过后合并；合并后删除短期分支，不直接向 `main` 推送日常改动。
4. 准备发布时，先更新 CLI 版本并验证安装包；合并到 `main` 后创建对应的 `vX.Y.Z` 标签。标签指向固定提交，不移动已发布标签。

当前稳定版本为 [`v0.4.1`](https://github.com/theron-muqiu/AI-Development-Skills/tree/v0.4.1)。安装示例固定此标签，避免 `main` 后续更新改变已安装版本。

## 常见问题

### 能否只安装一个技能，或安装到其他 Agent？

不能。目前仅支持 Codex、Hermes，八个技能作为一个完整组合安装和更新。

### 能否直接从 GitHub 或 PyPI 一行安装？

可以按“快速开始”中的命令直接从 GitHub 标签安装；当前尚未发布到 PyPI，因此不能使用 `uvx --from ai-devlop-cli`。新版本发布后，将 Git URL 中的标签改为对应版本。

### 检查状态正常，为什么 Agent 没有显示技能？

`status` 只检查文件与安装记录，不验证 Agent 是否启用或实际加载。请确认 Agent 的目录、当前 profile 和会话；Hermes 项目技能还需要用户信任。

### 安装被强制中断后怎么办？

断电或强制结束进程可能留下 `.lock`、备份或暂存目录。先确认没有安装进程运行，再检查错误提示中的恢复文件，最后清理锁并重试。损坏的安装记录、链接和 junction 路径不会被 `--force` 绕过；不保证跨进程崩溃自动恢复。

## 参考

本项目参考了 [Spec Kit](https://github.com/github/spec-kit)。

- [Codex 技能说明](https://developers.openai.com/codex/skills)
- [Hermes 技能说明](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/)
- [uv 文档](https://docs.astral.sh/uv/)
