# 规则集 03: 工业级代数闭式组价、倒轧平衡与高精度计算规范 (Pricing & Balancing Rules)

> **生效级别**：强制执行 (Mandatory)  
> **适用范围**：核心组价求解、综合单价分摊、清单倒轧平衡、数值精度管理

---

## 核心规则条目

### Rule 8: 代数闭式精确求解原则 (Closed-Form Analytical Precision)
- **坚决摒弃传统 Excel 依靠循环引用、单变量求解或反复迭代试算的落后做法**；
- 当综合单价中含有依单价比例提取的工艺板费 ($r_m$)、公司综合管理费 ($r_g$)、目标税前利润 ($r_p$) 时，必须使用**代数闭式解析解公式一步精确求得综合单价 $C_J$**：
  $$C_J = \frac{(C_{\text{fab\_net}} + C_{\text{trans\_net}}) \times (1 + t_1) + C_{\text{install\_net}} \times (1 + t_2)}{1 - r_m \times (1 + t_1) - (r_g + r_p) \times (1 + t_2)}$$
  *(其中 $t_1=0.13, t_2=0.09$)*
- **分母安全边际保护**：计算前必须校验分母，若分母 $\le 0.05$，必须拦截并抛出 `PricingParameterOverflowException`，提示调减提费率，防止数值发散。

### Rule 9: 9 费项倒轧平衡算法与安全边际预警 (Reverse-Plug Balancing & Safety Guards)
- 在将内部真实成本转换为发包人要求的 9 费项对外综合单价分析表时：
  1. **刚性费用直接锁定**：主材费、抛丸除锈、防腐防火涂料、运杂费、现场吊装、机械措施费、公司管理费、目标利润、税金固定锁定；
  2. **综合加工制作费动态吸收差额**：
     $$\text{综合加工制作费} = \text{目标投标综合单价} - \sum (\text{其余8项锁定直接费用})$$
  3. **制作费安全边际预警三色机制**：
     * **NORMAL (正常绿色)**：倒轧制作费 $\ge 600\text{ 元/t}$，属于安全盈利区间；
     * **WARNING_TIGHT (黄色预警)**：$400 \le \text{制作费} < 600\text{ 元/t}$，触发黄色告警并在界面提示车间成本倒挂风险；
     * **DANGER_LOW (红色熔断)**：$\text{制作费} < 400\text{ 元/t}$，禁止出标，必须强制调高综合单价。

### Rule 14: 高精度数值量化规范 (Decimal Precision Discipline)
- **严禁使用原生浮点数 (float) 进行金额与工程量累加计算**，所有财务和工程指标统一使用 Python `decimal.Decimal`；
- **四舍五入四级量化标准**（统一通过 `src/utils/decimal_calc.py` 处理）：
  * **金额分**：`PRECISION_MONEY = Decimal("0.01")` (保留 2 位小数)
  * **单价元/t**：`PRECISION_PRICE = Decimal("0.0001")` (保留 4 位小数)
  * **工程量吨**：`PRECISION_WEIGHT = Decimal("0.0001")` (保留 4 位小数)
  * **费率比例**：`PRECISION_RATE = Decimal("0.000001")` (保留 6 位小数)
