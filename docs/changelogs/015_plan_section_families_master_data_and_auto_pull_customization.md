# 基础数据重构（截面族后台设置与定额合并）与算量 Auto-Pull 在线调价设计方案

> **文档编号**：`015`  
> **任务目标**：根据用户评审意见，将系统导航“③ 基础定额库”升级为“③ 基础数据”，并在其中整合“截面族规则后台设置”；同时使算量工作台右侧 Auto-Pull 检查面板的数据全部真实来源于定额库，并支持用户直接在线修改与自定义微调构件参数，即时驱动两票制闭式重算。

---

## 1. 用户反馈与设计需求矩阵

| 用户评审反馈 | 涉及模块与组件 | 落地技术方案 |
| :--- | :--- | :--- |
| **反馈 1**：“截面族要有后台设置功能，可以放到定额一起。都叫基础数据” | 侧边栏导航、`view-database` 基础模块 | 1. 导航栏重命名为 **`③ 基础数据`**；<br>2. 基础数据模块首页增设 **`1. 截面族规则设置 (Section Families)`** Tab；<br>3. 支持查看、新增、编辑、删除截面族规则及板厚提取正则；<br>4. 包含“推导规则在线仿真沙盒”，支持实时输入规格检验推导结果。 |
| **反馈 2**：“这里的信息拉取都会来自于定额” | 算量工作台 Auto-Pull 检查看板 (`#view-takeoff`) | 1. Auto-Pull 检查面板不再使用静态假数据；<br>2. 选中任意构件时，根据构件截面族、材质、板厚，实时从 `masterData.quotas` 与 `section_families` 中动态提取材料快照、7道制作微工序、6道安装微工序及运距台阶。 |
| **反馈 3**：“这里也可以进行相应的修改” | Auto-Pull 检查面板即时编辑控件 | 1. 在面板顶部提供 **`✏️ 编辑调价 / 👁️ 查看明细`** 模式切换；<br>2. 支持直接微调截面规格（回车重推导）、材质选择、截面族变更、最大板厚手工覆盖；<br>3. 支持微调材料除税价、制作微工序调价、安装直接费与运距；<br>4. 实时调用代数闭式解析解刷新两票制单价与合价；<br>5. 提供 **`保存并更新构件`** 与 **`恢复定额默认值`** 按钮。 |

---

## 2. 详细技术实现路径

### 2.1 基础数据模块重构 (view-database)
- **Tab 结构优化**：
  - `Tab 1: 截面族与推导规则 (Section Families)` ⭐（新增）
  - `Tab 2: 材料价格库 (快照)`
  - `Tab 3: 车间制作定额 (7道微工序)`
  - `Tab 4: 现场安装定额 (6道微工序)`
  - `Tab 5: 机械台班与运杂费`
  - `Tab 6: 海外标准费率 (人天开办费)`
- **截面族实体数据结构 (`section_families`)**：
  ```json
  [
    {
      "family_code": "CROSS",
      "family_name": "十字形钢柱",
      "prefix_rules": ["十", "十字", "CROSS"],
      "default_material": "Q355B",
      "thick_rule": "取最后两位或肢板厚度",
      "bound_fab_norm": "胎架组立(95) + 埋弧焊(120) + ≥80mm厚板调价(140)",
      "bound_inst_norm": "高空吊装就位(618.05) + 机械措施(769.33)",
      "is_builtin": true
    },
    ...
  ]
  ```

### 2.2 算量 Auto-Pull 面板真实取数与在线编辑
- **动态拉取映射关系**：
  - `material_price = quotas.materials[comp.material][isThick ? 'thick_80' : 'normal']`
  - `fab_cost = quotas.fabrication.base + (comp.shape_family === 'CROSS' ? 95 : 0) + (comp.max_thickness >= 80 ? 140 : 0)`
  - `inst_cost = quotas.installation.base + (comp.shape_family === 'CROSS' ? 618.05 : 550.00)`
  - `trans_cost = (comp.transport_km / 850.0) * 302.85`
  - `cj_price = solveClosedFormPrice(fab_cost, trans_cost, inst_cost, ...)`
- **即时修改表单与双向绑定**：
  - 提供表单编辑视图，输入字段绑定 `oninput="recalcTakeoffInspector()"`；
  - 提供“应用更新”回写至 `masterData.components`，并刷新平铺表、WBS树形表及项目总额；
  - 提供“重置定额”随时回退手工调整。

---

## 3. 合规与测试计划
1. 单元与集成测试：`uv run --with pytest --with openpyxl python -m pytest tests/ -v`（保证 14 项测试全过）；
2. xUnit 规则巡检：`uv run --with openpyxl python -m src.utils.xunit_inspector`（保证 12 项规则全过）；
3. 3位序列号文档归档：`015_plan_...` 与 `016_walkthrough_...`；
4. 验证本地 GUI 服务与 GitHub Pages 同步。
