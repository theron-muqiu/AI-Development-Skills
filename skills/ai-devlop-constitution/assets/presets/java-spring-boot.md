# Java / Spring Boot 3 双模初始化宪法预设

> 适用技术栈：JDK 17+ / Spring Boot 3.x / MyBatis-Plus / Redis；分布式模式默认适配 Spring Cloud / Nacos / OpenFeign / MQ / Redisson 生态。
> 使用方式：初始化 Java 项目宪法时，先确认项目属于“单体”还是“分布式/微服务”，再将“通用底座 + 对应专属规范”按五字段规则拆分写入 `.ai-dev/memory/` 的 `constitution.md`、`engineering.md`、`architecture.md`、`security.md`；与当前仓库事实不符的条目按实际调整或标为待确认。

## 一、通用底座规范（单体与分布式强制共用）

### 1. 编码与命名

- **命名空间**：全面使用 `jakarta.*`（如 `jakarta.validation`、`jakarta.servlet`），严禁混用旧版 `javax.*`。
- **基础命名**：类名大驼峰，方法/变量小驼峰，常量全大写下划线；POJO 布尔属性禁止加 `is` 前缀（如使用 `deleted`）。
- **注入方式**：统一构造器注入（`@RequiredArgsConstructor` + `private final`），禁止字段 `@Autowired`。
- **线程池**：严禁使用 `Executors` 默认线程池，必须显式配置核心参数、队列上限、拒绝策略及业务线程名前缀。

### 2. 接口、异常与日志

- **RESTful 约定**：路径全小写、名词复数、连字符分隔（如 `/api/v1/user-orders`）；统一返回 `Result<T>(code, message, data, timestamp)` 与 `PageResult<T>`。
- **入参校验与异常处理**：Controller 层统一使用 `@Validated` + JSR-303 注解；异常统一抛出 `BizException(ErrorCode)`，由 `@RestControllerAdvice` 拦截，严禁向前端暴露堆栈。
- **日志规范**：统一 `@Slf4j` + 占位符打印，严禁 `System.out` 和 `e.printStackTrace()`；严禁打印密码、Token、身份证、手机号明文。

### 3. MyBatis-Plus 与 Redis

- **MyBatis-Plus**：强制使用 `LambdaQueryWrapper` / `LambdaUpdateWrapper`（严禁硬编码列名）；禁止 `SELECT *`；XML 中严禁 `${}` 拼接防注入；分页插件必须设置 `maxLimit` 限制单页上限。
- **Redis**：Key 格式为 `项目:模块:业务:唯一ID`；Value 统一 JSON 序列化（严禁 JDK 默认序列化）；所有缓存必须设 TTL 并加随机抖动防雪崩；严禁生产执行 `KEYS *`，规避大 Key（String 小于 10KB，集合元素小于 5000）。

### 4. 安全与 Git

- **防越权**：所有单资源读写接口必须校验当前用户归属权（`WHERE id = ? AND user_id = ?`）。
- **密钥安全**：生产密码、AK/SK 严禁明文入库，必须通过环境变量或配置中心注入。
- **Git 提交**：遵循 Conventional Commits（`feat/fix/refactor/docs/chore(scope): subject`）。

---

## 二、单体应用专属规范（轻量、防大泥球）

> 核心目标：控制复杂度与防止模块间循环依赖。

### 1. 目录结构与模块边界

- **按业务垂直分包**：`com.company.project.module.{user,order,product}`，每个业务包内包含 `controller`、`service`、`mapper`、`model`。
- **严禁跨模块调 Mapper**：`OrderService` 查用户必须调 `UserService`，禁止直接注入 `UserMapper`。
- **精简三层模型**：仅保留 `Entity`（表映射）、`DTO`（入参/跨模块传参，推荐用 `record`）、`VO`（前端展示，用 MapStruct 转换），不做过度抽象。

### 2. 单机事务与并发

- **本地事务**：显式声明 `@Transactional(rollbackFor = Exception.class)`；避免同类自调用导致事务失效；事务内严禁包含外部 HTTP 调用或文件 IO。
- **本地防重与锁**：单机环境下表单防重提交、热点资源并发更新，优先使用 Redis 分布式锁（便于未来平滑扩容至多实例）。

### 3. 单机日志与数据库变更

- **请求追踪**：通过 `HandlerInterceptor` 生成 `requestId` 写入 `MDC`，并在 `afterCompletion` 中执行 `MDC.clear()`。
- **防磁盘打满**：`logback-spring.xml` 必须配置按天滚动、单文件上限（如 `100MB`）、保留天数（如 `30天`）及总容量上限（如 `10GB`）。
- **SQL 变更**：强制使用 Flyway 管理版本化脚本（`V1.0.1__xxx.sql`），严禁线上手工改表不留记录。

---

## 三、分布式 / 微服务专属规范

> 核心目标：服务自治、容错防雪崩、数据最终一致、全链路可观测。

### 1. 服务拆分与工程结构

- **独立数据库原则**：每个微服务独占自己的数据库（或 Schema），严禁跨服务直连对方数据库或跨库 JOIN，数据交互必须通过 RPC/API 或事件驱动。
- **标准多模块结构**（以订单服务为例）：

```text
order-service
├── order-api        # 二方包：对外暴露的 Feign/Dubbo 接口、Req/Resp DTO、枚举（轻量化，不带业务依赖）
├── order-core       # 核心服务：controller / service / manager / mapper / entity
└── order-worker     # 可选：独立的定时任务或 MQ 消费者模块（避免重型任务拖垮在线接口）
```

- **模型分层**：在 `Entity / DTO / VO` 基础上，对外 RPC 契约独立为 `Req` / `Resp`（位于 `xxx-api` 模块），且接口变更必须保持向后兼容（只增不删字段，不改字段类型）。

### 2. 服务间通信与容错（OpenFeign / Dubbo）

- **显式超时控制**：所有 RPC/HTTP 调用必须配置连接超时与读取超时（如 `connectTimeout=2s`、`readTimeout=5s`），严禁使用无限等待。
- **谨慎配置重试**：仅允许对纯查询（`GET`）或明确实现幂等的接口开启重试；写接口（下单、扣款）严禁框架层自动重试。
- **熔断与降级**：非核心依赖（如推荐、积分、营销）必须配置熔断降级（Sentinel / Resilience4j），下游故障时返回兜底数据，严禁拖垮主链路。
- **内部接口鉴权**：内部 RPC 接口不直接暴露公网，通过网关路由隔离或内部 Token/mTLS 校验。

### 3. 分布式事务与最终一致性

- **优先最终一致性**：跨服务写操作优先采用本地消息表或 RocketMQ 事务消息实现最终一致性，避免长链路强一致锁死吞吐量。
- **慎用分布式强事务**：仅在资金、核心库存等强一致场景下评估使用 Seata（TCC 模式优于 AT 模式），并严格控制分支事务耗时。

### 4. 消息队列（MQ）规范

- **命名规范**：`Topic` 按 `业务域_事件` 命名（如 `order_created_topic`）；`ConsumerGroup` 按 `服务名_业务_group` 命名，不同服务严禁共用同一个消费组。
- **消费端强制幂等**：MQ 默认“至少投递一次”，所有消费者必须实现幂等（基于业务唯一键防重表、状态机 CAS 更新或 Redis 去重）。
- **消费与重试**：消费逻辑严禁长时间阻塞；无法恢复的业务异常不要无限重试，需接入死信队列（DLQ）并配置告警。

### 5. 分布式锁与定时任务

- **分布式锁（Redisson）**：锁粒度必须细化到具体业务 ID（如 `lock:order:pay:{orderId}`），严禁锁全局；必须设置合理过期时间或启用看门狗机制，释放锁必须在 `finally` 块中执行且校验 `lock.isHeldByCurrentThread()`。
- **分布式定时任务**：严禁在多实例集群中直接使用 Spring `@Scheduled`（会导致多节点重复执行），统一接入调度中心（XXL-JOB / PowerJob），任务逻辑同样需保证幂等。

### 6. 可观测性、配置与发布

- **全链路追踪**：集成 Micrometer Tracing（Spring Boot 3 原生）或 SkyWalking，确保 `traceId` 和 `spanId` 在网关、HTTP/RPC、异步线程池、MQ 之间完整透传。
- **配置中心（Nacos）**：按 `Namespace`（环境 dev/test/prod）+ `Group`（业务组）+ `DataId`（服务名）隔离；敏感配置加密存储；动态刷新配置需评估并发安全。
- **优雅停机与健康检查**：开启 `server.shutdown=graceful`，发版时先摘除注册中心流量、处理完在途请求后再停机；暴露 `/actuator/health/liveness` 与 `/readiness` 探针供容器调度使用（禁止将完整 Actuator 端点暴露至公网）。

---

## 四、单体 vs 分布式关键差异速查

| 维度 | 单体应用 | 分布式 / 微服务 |
| --- | --- | --- |
| **包与模块** | 单工程，按业务垂直分包 | 多服务独立仓库/模块，拆分 `xxx-api` 二方包 |
| **数据访问** | 跨模块调 `Service`，共享单库 | 独立数据库，严禁跨库 JOIN，通过 RPC/MQ 交互 |
| **事务管理** | `@Transactional` 本地事务 | 本地消息表 / MQ 事务消息（最终一致）为主 |
| **定时任务** | 单实例可用 `@Scheduled`，多实例需加锁 | 强制接入 XXL-JOB / PowerJob 调度中心 |
| **链路追踪** | 拦截器 + MDC 生成 `requestId` | Micrometer Tracing / SkyWalking 跨服务透传 `traceId` |
| **配置管理** | `application-{env}.yml` + 环境变量 | Nacos / Apollo 配置中心动态管理 |
| **容错机制** | 全局异常拦截 + 局部降级 | 网关限流 + RPC 超时/熔断/降级 + 优雅停机 |
