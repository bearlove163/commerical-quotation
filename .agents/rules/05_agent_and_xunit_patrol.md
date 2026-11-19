# 规则集 05: AI Agent 协作行为守则与 xUnit 自动化巡检阻断规范 (Agent Operational & xUnit Rules)

> **生效级别**：强制执行 (Mandatory)  
> **适用范围**：AI Agent 交互、代码演进、持续集成、质量准入

---

## 核心规则条目

### Rule 15: 先查后改原则 (Read-Before-Edit)
- 在修改任何现有代码、模型或文档之前，Agent 必须先读取目标文件的上下文，确保准确理解现有实现与业务逻辑；
- 严禁盲目猜测参数类型、字段名称或模块路径。

### Rule 16: 回归对账铁律 (Regression Reconciliation)
- 每次对核心计算模块（`src/core/`）或数据层做出修改后，必须运行湛江北站基准对账用例；
- 必须确保以下关键标杆指标**方差严格等于 0.0000**：
  * 自算量总吨位：$7,118.0958\text{ t}$（清单量 $7,945.0000\text{ t}$）
  * 内部总成本测算值：$76,375,361.03\text{ 元}$
  * 外部投标总报价：$83,137,633.41\text{ 元}$
  * 实腹钢柱综合单价：$8,847.5813\text{ 元/t}$（倒轧制作费 $1,181.8968\text{ 元/t}$）

### Rule 17: Windows 跨平台兼容与标准调用规范
- 本系统运行于 Windows 系统环境，执行 Python 统一遵循 `uv run --with <pkg> python <script>` 标准调用方式；
- 代码中文件路径处理一律使用 Python `pathlib.Path`，严禁硬编码 Windows 反斜杠拼接路径。

### Rule 18: 文档与代码同步交付 (Docs as Code)
- 代码新增或重构功能时，必须同步在 `docs/changelogs/` 中输出 3 位序号格式的 plan 与 walkthrough，严禁只改代码不留设计与演练痕迹。

### Rule 19: 自动化 xUnit 巡检阻断原则 (Automated xUnit Patrol Blocking Principle) ⭐
- 在执行代码提交、分支合入或正式出标前，必须运行如下 xUnit 自动化规则巡检引擎：
  ```bash
  uv run --with openpyxl python -m src.utils.xunit_inspector
  ```
- **门禁阻断铁律**：xUnit 巡检包含的 12 项规程（Git隔离、3位序列号、原始只读、财务零漂移、闭式恒等式、微工序完整性、倒轧安全阈值、GUI/API资产）必须**100% 全部 PASS**。出现任何一项 FAIL，一票否决，禁止代码合入主干！
