# 驾驶舱多维造价全景表格重复单位剥离与排版优化报告

> **执行编号**：`014`  
> **任务目标**：根据用户反馈，彻底消除表格单元格中与表头重复的单位（`元/t`、`万元`、`t`、`¥`），解决因单元格宽度导致的“万/元”换行与挤压问题，实现工业级金融看板纯数值对齐排版。

---

## 1. 优化前后对照 (Before vs After)

| 列项 | 优化前 (存在单位冗余与换行挤压) | 优化后 (表头统一定义单位，单元格纯数值呈现) | 优化收益 |
| :--- | :--- | :--- | :--- |
| **表头定义** | `自算量 / 清单量 (量差)`<br>`综合造价(元/t)`<br>`合同/投标造价`<br>`测算成本`<br>`毛利/亏损额` | `自算 / 清单量 (t)`<br>`综合造价 (元/t)`<br>`合同/投标 (万元)`<br>`测算成本 (万元)`<br>`毛利/亏损 (万元)` | 明确全表各列统计口径与量纲 |
| **自算/清单量** | `7,118.10 t / 7,945.00 t`<br>`-826.90 t (-10.4%)` (重复3个`t`) | `7,118.10 / 7,945.00`<br>`-826.90 (-10.4%)` | 移除重复的字母 `t`，版面清爽 |
| **综合造价** | `¥11,680 元/t` (表头已带元/t还重复写) | `11,680` (纯数字、右对齐加粗) | 消除表头与单元格的单位冲突 |
| **合同/投标额** | `¥8,313.76 万元` | `8,313.76` (等宽字体、右对齐) | 纯净金融数字展示 |
| **内部测算成本** | `¥7,637.54 万元` | `7,637.54` (等宽字体、右对齐) | 便于纵向上下对齐比对 |
| **毛利/亏损额** | `-¥594.68 万`<br>`元` ❌ (**换行断开成两行**) | `-594.68` ⭐ (**单行徽标，绝不折行**) | 彻底杜绝文字折行破版 |
| **锁价比例 & 敞口** | `52% (敞口: 3,813`<br>`t (约¥1,890`<br>`万))` ❌ (**折成3行**) | `52%`<br>`敞口: 3,813t (1,890万)` (**单行说明**) | 紧凑布局，层次分明 |

---

## 2. 核心改动代码

在 [app.html](file:///C:/Users/Administrator/.gemini/antigravity/worktrees/钢结构商务系统/untitled-worktree/src/gui/workbench/app.html) 与 [index.html](file:///C:/Users/Administrator/.gemini/antigravity/worktrees/钢结构商务系统/untitled-worktree/src/gui/workbench/index.html) 中：

1. **表头规范化**：统一定义列量纲（`(t)`、`(元/t)`、`(万元)`），消除歧义；
2. **清洗过滤引擎**：注入 `cleanNum`、`cleanTonnageDiff`、`cleanExposure` 正则清洗函数，动态剥离各种前缀 `¥`、`$` 及后缀 `元/t`、`万元`、`万`、`t`；
3. **单行不折行保证**：为所有数值单元格增加 `whitespace-nowrap`，彻底终结负数亏损额换行破版问题；
4. **服务底层增强**：将 [run_gui.py](file:///C:/Users/Administrator/.gemini/antigravity/worktrees/钢结构商务系统/untitled-worktree/src/gui/run_gui.py) 的 `socketserver.TCPServer` 升级为 `ThreadingServer`，防止并发连接阻塞。

---

## 3. 验证与访问

- **服务运行地址**：[http://localhost:8765/app.html](http://localhost:8765/app.html)
- **单元与回归测试**：14 项测试全部通过（`uv run --with pytest --with openpyxl python -m pytest tests/ -v`）
- **xUnit 规则巡检**：12 项规则全绿通过（`uv run --with openpyxl python -m src.utils.xunit_inspector`）
