# 012_plan: 驾驶舱纵向滚动沉浸化、KPI点击穿透、数据统计看板与全维度造价信息重构方案

> **对应标准**：AGENTS.md Rule 4 (3位序列号铁律) & Rule 6 (模式硬隔离) & Rule 19 (xUnit巡检阻断)  
> **反馈依据**：用户在浏览器实测反馈（图 1 真实截图：底部表格高度受限仅露一行、缺乏纵向自然滚动、顶部 KPI 缺少点击穿透查看、缺少数据统计大屏、项目造价与亏损等深度信息量不足）。

---

## 一、 目标描述 (Goal Description)

针对用户在真实操作中指出的体验瓶颈与功能诉求，进行一次**深度交互与数据扩充升级**：

1. **纵向全屏自然流畅滚动 (Full Page Flow & Natural Scroll)**
   - 彻底解除 `#view-dashboard` 内部表格容器的高度拘束，使整个驾驶舱页面呈现为**自顶向下自然延展的大屏长页面**；
   - 优化滚动条设计与自适应容器，使用户可以顺畅往下拉动页面，完整查看全部 14 个项目的海量数据，告别狭窄挤压感。

2. **顶部 4 大 KPI 卡片全量穿透可点击查看 (Interactive KPI Drill-Down)**
   - 给 4 大卡片赋予交互感知状态（悬浮阴影、边框微动、光标指针手势 `cursor-pointer hover:border-blue-500`）；
   - **卡片 1【在投项目 5 个 / 2.88 亿】**：点击弹出「在投项目全景穿透看板 (`dlgInBidProjectsModal`)」，展示 5 大投标工程的自算量、清单量、报价策略与投递排期；
   - **卡片 2【开标倒计时 3 天 / 湛江北站】**：点击弹出「近期开标排期与封标自检清单 (`dlgBidScheduleModal`)」，查看开标日历及湛江北站开标前 7 项红线自检（两票制税金闭式平、制作费大于 600 元/t 阈值等）；
   - **卡片 3【限价空间预警 2 项 / <30 万】**：点击弹出「限价红线预警与调价对冲穿透表 (`dlgPriceLimitModal`)」，查看湛江北站（3.29万）与前海塔楼（21.80万）的调价对冲与成本压缩方案；
   - **卡片 4【本月中标额 1.86 亿 / +12.4%】**：点击弹出「本月中标台账与下浮率分析 (`dlgAwardedSummaryModal`)」，查看中标项目清单、平均下浮 14.7% 对比与施工目标成本交底进度。

3. **驾驶舱全景经营数据统计看板 (Analytics & Statistics Hub)**
   - 在 KPI 卡片与项目列表之间增设**「经营与造价全景统计大屏」**（支持一键展开/收起）：
     * **统计 1：全生命周期 4 阶段造价总额与规模分布**（总造价 ¥6.85 亿元，投标 2.88 亿 / 签约 2.10 亿 / 执行 1.59 亿 / 结算 0.28 亿，带精美进度占比条）；
     * **统计 2：全周期毛利盈亏与风险穿透雷达**（加权毛利率 +5.26%，净毛利额 +¥3,604 万元；亏损预警 2 项 · 亏损额 -¥614 万元；临界监控 3 项；健康盈利 9 项）；
     * **统计 3：钢构总吨位与自算量差穿透统计**（总吨位 50,420 t，单吨综合造价 13,585 元/t，清单与自算净量差 -2,302 t，潜在索赔空间 ¥1,980 万元）；
     * **统计 4：大宗钢材集中采购锁价敞口监控**（已锁价 58.4%，未锁敞口 41.6% 约 20,974 t，钢价波动敏感度测算）。

4. **项目表格海量造价与亏损信息多维扩充 (Rich Cost & Loss Metrics)**
   - 在底层 `data.json` 与前端表格中，大幅追加项目的商务经济指标：
     * **自算吨位 vs 清单吨位** 及 **量差率 (%)**；
     * **单吨综合造价 (元/t)**（如湛江北站 11,680 元/t，松山湖 12,200 元/t）；
     * **合同造价 / 投标报价 (万元)**；
     * **对内测算成本 / 目标成本 (万元)**；
     * **毛利额 / 亏损额 (¥万元，带醒目红绿色阶)**（如湛江北站 -¥594.68万亏损、白云站 +¥1,320.00万毛利）；
     * **钢材锁价比例 & 敞口吨位**；
     * **造价异动与亏损诊断标签**（例如：“量差倒挂超700t”、“未锁价敞口65%”、“低价抢标战略亏损”、“单吨措施费超额”）。
   - 提供**「标准紧凑视图」**与**「造价多维全景视图」**双模式切换，满足不同业务层级对信息密度的要求。

---

## 二、 架构设计与页面全景流 (Architecture Diagram)

```mermaid
flowchart TD
    subgraph ViewDashboard [全新纵向流畅滚动视图 · view-dashboard]
        Header[顶栏：岗位驾驶舱 · 商务经理 + 口径下拉]
        
        subgraph TopKPI [4 大可点击穿透 KPI 卡片]
            K1[在投项目 5个<br/>👉 点击穿透在投全景]
            K2[开标倒计时 3天<br/>👉 点击穿透开标日程与自检]
            K3[限价空间预警 2项<br/>👉 点击穿透调价对冲方案]
            K4[本月中标额 1.86亿<br/>👉 点击穿透中标台账下浮率]
        end
        
        subgraph UrgentSection [我的急办高危队列 (4项)]
            U1[01 湛江限价]
            U2[02 前海特批]
            U3[03 珠海调价]
            U4[04 白云确权]
        end
        
        subgraph StatisticsHub [全新 · 经营与造价全景统计看板]
            S1[4阶段造价分布条<br/>¥6.85亿规模占比]
            S2[毛利盈亏仪表盘<br/>+¥3,604万毛利 / -¥614万亏损]
            S3[单吨造价与量差<br/>13,585元/t / -2,302t量差]
            S4[集采锁价敞口监控<br/>已锁58.4% / 敞口2.0万吨]
        end
        
        subgraph ProjectMatrix [全生命周期 14 项目深度造价表格]
            Tabs[5阶段 Tab 筛选 + 视图模式切换: 紧凑 / 多维造价]
            Notice[阶段管控智能公式栏]
            Table[高密度全景表格<br/>序号 | 项目/阶段 | 自算/清单/量差 | 单吨造价 | 造价总额 | 成本 | 盈亏额 | 毛利率 | 锁价敞口 | 状态]
        end
    end

    Header --> TopKPI
    TopKPI --> UrgentSection
    UrgentSection --> StatisticsHub
    StatisticsHub --> ProjectMatrix

    subgraph Modals [弹窗穿透体系]
        M1[dlgInBidProjectsModal]
        M2[dlgBidScheduleModal]
        M3[dlgPriceLimitModal]
        M4[dlgAwardedSummaryModal]
    end

    K1 -.-> M1
    K2 -.-> M2
    K3 -.-> M3
    K4 -.-> M4
```

---

## 三、 用户评审要点 (User Review Required)

> [!IMPORTANT]
> **1. 页面滚动模式优化**：
> 移除表格局限在屏幕下方的固定高度设定，改为整个 `#view-dashboard` 内部全长平滑纵向滚动（Native Smooth Scroll），让 14 个项目的全部行在用户往下拉动时流畅展现，彻底解决只有一行可见的问题。
> 
> **2. 4 大指标卡交互动作**：
> 点击卡片不再只是无响应，而是唤起对应的穿透详情弹窗，帮助商务经理一键下钻到底层明细；
> 
> **3. 造价与亏损数据透视**：
> 在每个项目行中直接展示「合同造价」、「目标成本」、「盈亏额（万元）」、「单吨造价（元/t）」及「锁价敞口」，亏损项目以醒目红字标注负毛利（如湛江北站 -594.68万、汕头亚青会 -19.56万），信息量极大充实。

---

## 四、 具体变更计划 (Proposed Changes)

### 1. 数据集扩充 (`src/gui/workbench/data.json`)
#### [MODIFY] `src/gui/workbench/data.json`
- 保持原有的 `components` (81 项构件) 与 `bq_items` (13 项清单) 绝对不变；
- 扩充 `cockpit_projects` 14 个项目的多维字段：
  * `tonnage_self`: 自算吨位（如 `7,118.10 t`）
  * `tonnage_bq`: 清单吨位（如 `7,945.00 t`）
  * `tonnage_diff`: 量差与量差率（如 `-709.34 t (-9.97%)`）
  * `cost_total`: 测算总成本（如 `¥7,637.54 万元`）
  * `cost_per_ton`: 单吨测算成本（如 `¥10,729 元/t`）
  * `quote_per_ton`: 单吨综合造价（如 `¥11,680 元/t`）
  * `profit_amount`: 毛利额/亏损额（如 `-¥594.68 万元`、`+¥1,320.00 万元`）
  * `locked_ratio_num`: 锁价百分比
  * `unlocked_exposure_ton`: 未锁敞口吨位
  * `risk_diagnosis`: 亏损/造价风险诊断原因标签数组
- 新增 `cockpit_analytics` 统计数据集（造价分布、毛利总池、吨位造价均值、锁价敞口汇总）。

### 2. 前端界面与交互深度升级 (`src/gui/workbench/app.html`)
#### [MODIFY] `src/gui/workbench/app.html`
- **样式与布局优化**：
  * 为 `#view-dashboard` 增加 `min-h-full pb-16` 与自定义平滑滚动条，解除表格卡片的高度锁死；
  * 给顶部 4 个 KPI 卡片增加 `cursor-pointer hover:shadow-md hover:border-blue-400 active:scale-98 transition group`，绑定穿透点击函数；
- **新增统计看板组件 (`#cockpitStatisticsHub`)**：
  * 渲染 4 大统计视窗（全周期造价阶段分布、毛利盈亏穿透、单吨指标与量差池、锁价敞口敏感度）；
- **新增 4 大 KPI 穿透弹窗**：
  * `dlgInBidProjectsModal`: 在投项目穿透明细；
  * `dlgBidScheduleModal`: 开标排期与湛江北站自检封标看板；
  * `dlgPriceLimitModal`: 限价空间预警穿透与对冲表；
  * `dlgAwardedSummaryModal`: 本月中标工程与下浮率台账；
- **重构项目表格与视图切换**：
  * 增加视图切换开关（标准紧凑模式 vs 多维造价全景模式）；
  * 多维模式下平铺展示：序号、项目/阶段、自算/清单/量差、单吨造价、总造价、总成本、毛利额/亏损额、毛利率、锁价敞口、诊断与状态；
  * 优化行点击事件，保障「湛江北站」秒级穿透算量工作台，其它项目滑出全周期台账抽屉。

### 3. 同步更新 `index.html` 与单元测试
#### [MODIFY] `src/gui/workbench/index.html`
- 与 `app.html` 同步保持一致。
#### [MODIFY] `tests/unit/test_gui_and_api.py`
- 扩展 `test_cockpit_assets_and_data_integrity` 校验新增的统计大屏与造价盈亏指标字段。

---

## 五、 验证计划 (Verification Plan)

### 1. 自动化测试回归
```bash
# 验证全套 14 个测试用例全部通过
uv run --with pytest --with openpyxl python -m pytest tests/ -v

# 验证 12 项 xUnit 规则合规巡检全部通过
uv run --with openpyxl python -m src.utils.xunit_inspector
```

### 2. 本地浏览器界面走查
1. 启动本地服务：`uv run python -m src.gui.run_gui --port 8765`；
2. 打开 `http://localhost:8765/app.html`：
   - 验证页面可无限顺畅往下拉动，项目表格完整呈现且空间开阔；
   - 点击 4 大 KPI 卡片，逐一验证是否能正常弹出穿透弹窗；
   - 验证统计看板的 4 个数据卡片是否清晰呈现全周期造价、毛利盈亏、单吨指标与锁价敞口；
   - 验证表格中的单吨造价、总成本、盈亏额（红绿色阶）是否清晰丰富；
   - 验证点击湛江北站穿透算量工作台及其他项目抽屉是否运转正常。
