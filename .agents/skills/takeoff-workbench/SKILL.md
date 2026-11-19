---
name: takeoff-workbench
description: >-
  算量工作台截面智能推导与定额自动拉取 (Auto-Pull) 技能。
  当需要处理构件截面规格、识别截面族（CROSS/BOX/PIPE/SPHERE/TRUSS）、推导主板厚度及自动拉取定额时使用。
---

# Takeoff Workbench Skill (算量截面推导与定额自动拉取技能)

## 技能说明
支持键盘高效录入构件规格，智能推导截面分类与最大板厚，秒级向底层库拉取工序定额与材料快照出厂价。

## Python 核心调用范式
```python
from src.core.take_off_analyzer import TakeoffAnalyzer

# 截面解析与板厚推导
spec = "十1300x600x80x80"
shape_family, max_thick = TakeoffAnalyzer.parse_section_spec(spec, name_hint="钢柱十字型")
# 输出: ('CROSS', Decimal('80.0'))
```
