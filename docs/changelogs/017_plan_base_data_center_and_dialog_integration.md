# 017. 基础数据中心全量定额资产沉淀与 Dialog 弹窗管理引擎架构规划 (Plan)

> **文档标识**：`017_plan_base_data_center_and_dialog_integration.md`  
> **涉及模块**：`src/services/base_data_service.py`, `src/database/models/master_data_models.py`, `src/api/v1/api_router.py`, `src/gui/workbench/app.html`, `src/gui/workbench/data.json`  
> **前置依赖**：`015_plan_section_families_master_data_and_auto_pull_customization.md`  
> **核心使命**：全面承接原 Excel 审批表全部定额资产，建立六大正交材料规则引擎与钢厂-加工厂调运费模型，构建专业分包与合格名录字典，并提供标准化独立 Dialog 管理交互。

---

## 1. 业务背景与改造目标

1. **原表定额 100% 沉淀**：
   - 制作工序定额：47 项基准定额，全面解耦为 7 道微工序（下料、组立、焊接、探伤矫正、预拼装、抛丸除锈 Sa2.5、车间底漆中间漆）；
   - 现场安装定额：65 项基准定额，穿透人工、辅材、机械措施及其他直接费；
   - 区域大型起重机械：193 项大型吊车（50t~650t 履带吊、25t~500t 汽车吊）在 6 大区域的月租、进出场及油费。
2. **正交材料规则引擎与调运物流模型**：
   - 建立涵盖 235~960 MPa 屈服强度、A~F 冲击温度、AR/CR/TMCP/N/QT 冶金交货状态、7 档板厚连续阶梯、Z向性能（Z15/Z25/Z35）及超声探伤的六大正交原子维度；
   - 重点深化 TMCP 控轧控冷工艺，量化其在车间免预热/低温预热下的综合制造节能工效；
   - 建立钢厂（宝武湛江、韶钢、湘钢、沙钢、武钢等）至不同制造基地（江门、中山、武汉、长兴）的调运运杂费矩阵，闭式计算材料到厂综合结算价；
   - 实现逆向等效基准剥离算法，支撑跨周期、跨项目的长期横向比较。
3. **专业分包产品字典与合格供应商名录**：
   - 沉淀 18 项核心专业分包产品（拉索体系、铸钢件、闭口/开口/桁架楼承板、防火防腐涂装、减隔震支座、无损检测）；
   - 建立 9 项合格分包商企业名录，支持资质、区域与历史优惠下浮评级。
4. **标准化 Dialog 模态框交互体系**：
   - 封装 `dlgQuotaManagement`、`dlgMaterialMatrix`、`dlgSubcontractManagement`、`dlgMachineryManagement` 4 大独立 Dialog 弹窗，支持外部业务模块一键唤起与管理。

---

## 2. 系统技术架构与模型设计

- **数据层**：`src/database/models/master_data_models.py` 定义正交枚举与实体类；
- **服务层**：`src/services/base_data_service.py` 封装原表抽取、闭式解算、调运匹配与逆向剥离等核心领域服务；
- **路由层**：`src/api/v1/api_router.py` 提供 `get_base_master_data()` 与 `calculate_material_landed_cost()` REST 接口；
- **前端工作台**：`src/gui/workbench/app.html` 升级为 8 大子选项卡，内嵌实时测算仿真器并封装 4 大管理 Dialog；
- **回归与测试**：更新 `tests/unit/test_gui_and_api.py`，新增 API 与数据完整性断言。
