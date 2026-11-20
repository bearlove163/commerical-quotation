# SteelBid Pro · 业务计划 (020_plan_master_data_submodule_decoupling_and_rbac.md)

> **版本**：v2.3.0-SUPERADMIN-MODULAR  
> **基准工程**：新建广州至湛江高速铁路站房及相关工程 GZFJ-3 标（湛江北站 · 7,118.10 t / 8,313.76 万元）  
> **定位**：超级管理员全量管理中台、材料分支解耦、独立客商名录中枢与树状自动缩放导航

---

## 1. 计划目标与背景

根据用户最新审阅意见：
1. **超级管理员中台定位**：当前阶段全量开放管理维护，暂不硬编码前端千人千面（预留后台动态可配置数据模型）；
2. **客商名录库提升为独立中枢**：合格供应商名录作为全局共享客商中心，服务于钢企、各分包商、吊机租赁商、检测机构，不与单一材料并排；
3. **左侧二级树状导航自动缩放**：在基础数据中台内部增加左侧二级树状导航，支持一键折叠（图标态 56px）与展开（完整态 240px），确保大屏下宽表格浏览体验；
4. **吊机租赁费用按区域解耦**：覆盖国内 6 大区域与海外典型大区（东南亚、中东、非洲等）；
5. **专业分包 6 大材料小分支解耦**：拉索、铸钢件、楼承板、涂料、支座、无损检测各自独立维护。

详见系统级设计方案文档：[steelbid_pro_master_data_modular_architecture_and_rbac_plan.md](file:///C:/Users/Administrator/.gemini/antigravity/brain/cd82ac03-08cf-4e48-ad7c-1ec078925a57/steelbid_pro_master_data_modular_architecture_and_rbac_plan.md)。
