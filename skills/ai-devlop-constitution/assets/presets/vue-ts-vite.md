# Vue 3 前端项目初始化宪法预设

> 适用技术栈：Vue 3 + TypeScript + Vite + Pinia + Vue Router（参考 Vue 官方风格指南）。
> 使用方式：初始化 Vue 前端项目宪法时，将以下规范按五字段规则拆分写入 `.ai-dev/memory/` 的 `constitution.md`、`engineering.md`、`architecture.md`、`security.md`；与当前仓库事实不符的条目按实际调整或标为待确认。

## 一、标准目录结构

按职责划分顶层目录，复杂业务在 `views/` 下按业务模块嵌套私有组件和局部 API：

```text
src/
├── api/            # 接口层：按业务模块拆分（如 user.ts、order.ts），严禁在组件内直接写 URL
├── assets/         # 静态资源（图片、图标、全局样式）
├── components/     # 全局通用基础组件（如 BaseTable、BaseModal）
├── composables/    # 组合式函数（Hooks，统一 use 开头，如 usePagination.ts）
├── directives/     # 自定义指令（如 v-permission）
├── layouts/        # 页面布局骨架（如 MainLayout、AuthLayout）
├── router/         # 路由配置与权限守卫
├── stores/         # Pinia 状态管理（按模块拆分）
├── types/          # 全局 TypeScript 类型定义（*.d.ts 或模块类型）
├── utils/          # 纯工具函数（如 request.ts、format.ts，不依赖 Vue 实例）
└── views/          # 页面级组件（按业务域建文件夹）
    └── order/
        ├── index.vue          # 列表主页面
        ├── detail.vue         # 详情页
        └── components/        # 仅 order 页面使用的私有子组件
```

## 二、命名规范

| 类别 | 规范 | 示例 |
| --- | --- | --- |
| 目录名 | 全小写，多词用短横线 `kebab-case` | `user-profile/`、`order-list/` |
| 组件文件名 | 统一大驼峰 `PascalCase`（除 `index.vue` 外），强制多词防与 HTML 标签冲突 | `UserCard.vue`、`OrderTable.vue` |
| 基础/单例组件 | 基础组件以 `Base` 或项目前缀开头；全局单例以 `The` 开头 | `BaseButton.vue`、`TheHeader.vue` |
| 组合式函数 | 小驼峰，强制以 `use` 开头 | `useAuth.ts`、`useTableData.ts` |
| Pinia Store | 文件名小驼峰/短横线，导出函数 `useXxxStore` | `useUserStore` |
| 模板中 Props | 声明用 `camelCase`，模板传参推荐 `kebab-case` | `:user-name="name"` |
| 自定义事件 | 统一 `kebab-case`（如 `update:modelValue`、`submit-form`） | `@submit-form="handleSubmit"` |

## 三、组件与 `<script setup>` 编码规范

### 1. SFC 标签顺序

统一为：`<script setup lang="ts">` → `<template>` → `<style scoped lang="scss">`。

### 2. 宏与代码组织顺序

在 `<script setup>` 内部按逻辑流排列：

1. `import` 导入（第三方库 → 内部工具/API → 子组件 → 类型）
2. `defineOptions` / `defineProps` / `defineEmits` / `defineModel`
3. 路由与 Store 初始化（`useRoute`、`useUserStore`）
4. 响应式状态（`ref` / `reactive`）与计算属性（`computed`）
5. 监听器（`watch` / `watchEffect`）与生命周期钩子（`onMounted`）
6. 业务方法（`handleXxx`、`fetchXxx`）
7. `defineExpose`（仅在确实需要暴露给父组件时使用）

### 3. 核心红线与最佳实践

- **Props 单向数据流**：严禁在子组件内直接修改 `props`，需通过 `emit` 或 `defineModel` 通知父组件。
- **Props 类型声明**：使用 TypeScript 纯类型声明（`defineProps<{ id: number; title?: string }>()`），配合 `withDefaults` 设置默认值。
- **`v-for` 规范**：必须绑定唯一且稳定的 `:key`（严禁使用数组索引 `index` 作为可变更列表的 key）；严禁在同一元素上同时使用 `v-if` 和 `v-for`，应先用 `computed` 过滤数据。
- **组件粒度**：单个 `.vue` 文件建议不超过 300–400 行，复杂逻辑抽离至 `composables/`，复杂 UI 拆分为同级 `components/` 子组件。
- **内存清理**：在 `onMounted` 中注册的全局事件监听、定时器（`setInterval`）、WebSocket 等，必须在 `onUnmounted` 中清理。

## 四、状态管理（Pinia）与接口请求规范

### 1. Pinia 使用边界

- **只存真正的全局共享状态**：如登录用户信息、Token、全局权限菜单、主题/语言配置。
- **严禁滥用 Store**：仅在单个页面或父子组件间使用的数据使用局部 `ref` 或 `props/emit`，不写入 Pinia。
- **统一语法**：推荐使用 Setup Store 语法（`defineStore('user', () => { ... })`），与 `<script setup>` 保持一致。

### 2. Axios 与 API 层封装

- **统一拦截器**：在 `utils/request.ts` 中封装 Axios 实例：请求拦截器自动注入 `Authorization: Bearer <token>`；响应拦截器与后端统一响应体（如 `Result<T>`）对齐，统一处理业务错误码（如 `401` 跳转登录并清理缓存、`403` 提示无权限、`500` 全局提示）。
- **接口强类型**：每个 API 函数明确入参和返回值泛型，例如：

```ts
// src/api/order.ts
export function getOrderList(params: OrderQueryDTO) {
  return request.get<PageResult<OrderVO>>('/api/v1/orders', { params })
}
```

## 五、样式与 CSS 规范

- **样式隔离**：组件内 `<style>` 必须加 `scoped`，防止全局样式污染；修改第三方组件库内部样式时使用 `:deep(.el-input)`。
- **原子化 CSS / 预处理器**：使用 Tailwind CSS / UnoCSS 时避免单行类名过长（超过 8–10 个高频复用组合应抽离为组件）；使用 SCSS/Less 时选择器嵌套层级不超过 3 层，严禁滥用 `!important`。
- **主题与变量**：颜色、字号、圆角、阴影统一使用 CSS 变量（如 `--color-primary`）定义在全局样式文件中，禁止在组件内硬编码色值（如 `#1677ff`）。

## 六、TypeScript 与工程化卡点

- **TS 规范**：开启 `strict: true`；严禁滥用 `any`（未知类型优先用 `unknown` 配合类型守卫）；接口响应对象、表单数据结构必须定义 `interface` 或 `type`。
- **环境变量**：使用 `.env.development`、`.env.production` 隔离配置，暴露给前端的变量必须以 `VITE_` 开头，严禁在前端环境变量中存放任何敏感密钥。
- **自动化工具链**：落地 ESLint（`eslint-plugin-vue` + `@typescript-eslint`）、Prettier 统一格式化，以及 Husky + lint-staged + commitlint 在 `git commit` 前强制校验代码质量与提交信息格式。
