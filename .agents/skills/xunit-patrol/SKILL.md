---
name: xunit-patrol
description: >-
  SteelBid Pro xUnit 自动化规则巡检与合规测试技能。
  当需要执行项目回归验证、合规性检查、出标前自检或排查数据漂移时使用此技能。
---

# xUnit Patrol Skill (自动化巡检与规则审计技能)

## 技能说明
本技能用于对 SteelBid Pro 系统执行工业级 xUnit 规范的全盘规则审计。

## 常用命令
```bash
# 执行全套 12 项规则巡检并生成 xUnit XML 测试报告
uv run --with openpyxl python -m src.utils.xunit_inspector

# 运行全套回归单元测试
uv run --with pytest --with openpyxl python -m pytest tests/ -v
```

## 巡检覆盖的核心规则
1. Git Worktree 物理隔离与 `.gitignore` 规则有效性
2. Plan 与 Walkthrough 3 位序列号规范
3. 原始数据 `data/raw/` 只读性与导出报表归档
4. 湛江北站基准指标零漂移（7,118.10t 自算量、83,137,633.41元总报价、76,375,361.03元成本）
5. 两票制代数闭式解析解恒等式（分钱级误差 < 0.05 元）
6. 倒轧加工制作费安全红线（>= 600 元/t）
