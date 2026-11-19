---
name: steel-pricing-engine
description: >-
  钢结构核心工业级组价与倒轧平衡引擎技能。
  当需要进行国内两票制闭式解析单价求解、9 费项倒轧平衡计算或海外人天成本与开办费测算时调用此技能。
---

# Steel Pricing Engine Skill (钢结构组价计算技能)

## 技能说明
提供两大核心业务模式的工业级组价算法：
1. **国内两票制闭式求解器**：基于解析公式一步计算出含税综合单价 CJ，杜绝循环迭代。
2. **海外人天成本法与开办费包**：基于派驻工种综合人天包（吃住行日标准+外派津贴+PPE与保险）及现场 Preliminaries 开办费包测算。
3. **9 费项倒轧平衡**：制作费动态吸收差额并监控安全阈值。

## Python 核心调用范式
```python
from decimal import Decimal
from src.core.closed_form_solver import solve_domestic_two_invoice
from src.core.balancing_engine import BalancingEngine

# 国内两票制闭式求解
res = solve_domestic_two_invoice(
    c_fab_net=Decimal("5981.77"),
    c_trans_net=Decimal("302.85"),
    c_install_net=Decimal("1525.69"),
    r_mgmt=Decimal("0.085"),
    r_profit=Decimal("-0.0715"),
)
cj_price = res["composite_unit_price"]

# 9 费项倒轧平衡
rec = BalancingEngine.run_reverse_plug(
    item_code="010101",
    item_name="实腹钢柱",
    target_unit_price=cj_price,
    fee_1_main_steel=Decimal("5131.77"),
    fee_3_rust_removal=Decimal("50.00"),
    fee_4_coating=Decimal("0.00"),
    fee_5_freight=Decimal("302.85"),
    fee_6_installation=Decimal("756.36"),
    fee_7_machinery=Decimal("769.33"),
    fee_8_mgmt_profit=Decimal("655.38"),
    fee_9_taxes=Decimal("0.00"),
    original_fabrication_cost=Decimal("1470.00"),
)
```
