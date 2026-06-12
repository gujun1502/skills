# structural-analysis

既有建筑加固 / 改造方案的**结构合理性定量分析**与**中文 PDF 研究报告生成** Claude Code skill。

适用于荷载大幅增加的改造场景（如普通办公改金库 / 档案库 / 重型库房），帮助论证"加固是否成立、还是应当拆除重建"，并产出图文并茂的中文结构分析报告。依据 GB50010 / GB50011 / GB55008 / GB50367。

## 安装位置

`~/.claude/skills/structural-analysis/`

## 触发方式

向 Claude 提及以下任意一项即可：既有建筑加固、老楼改造、结构方案合理性、加固 vs 拆除重建、金库/档案库重荷载改造、柱轴压比、地震力对比、桩基/基础承载力、梁承载力与净高、二次受力(应力滞后)、消能减震局限性、结构专篇/结构分析报告。

也可直接说："这个加固方案合不合理 / 帮我出一份结构分析报告"。

## 目录结构

```
structural-analysis/
├── SKILL.md                          # 入口：方法论 + 规范 + 报告生成要点
├── README.md                         # 本文件
└── scripts/
    ├── analysis.py                   # 核心定量分析引擎（九步验算范本）
    ├── generate_report.py            # 单方案 PDF 报告生成器
    ├── generate_report_bc50.py       # 半金库半办公方案专用报告
    └── generate_integrated_report.py # 多方案综合研究报告（含全部示意图，最完整范本）
```

## 依赖

```bash
pip install numpy matplotlib reportlab
```

Windows 自带中文字体（msyh.ttc / simhei.ttf / simsun.ttc）即可；其他系统需替换为对应中文字体路径。

## 说明

`scripts/` 中的脚本以一个"银行金库改造"工程为**演示样例**，其中的柱网、荷载、截面等为该项目具体取值。复用到新项目时，按新参数替换脚本顶部常量即可。生成的客户机密 PDF / 源数据未纳入本仓库。

## 更新记录

- 2026-06-09：发布 structural-analysis 技能（结构合理性定量分析 + 中文 PDF 报告生成）。
- 2026-06-09：确认技能在 gujun1502/skills 仓库就位，可随时调取。
