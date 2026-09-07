# m3e-canvas 研究：对教学型 Mini-DBMS 控制台的可迁移思路

> 研究范围：仅使用 `lnkiai/m3e-canvas` 的 GitHub 仓库、README、贡献指南和源码。访问日期：2026-09-07。本文区分“仓库事实”和“面向本项目的设计推论”，不把上游项目的说明当作我们的产品需求。

## 结论摘要

m3e-canvas 最值得借鉴的不是它的 Material 3 Expressive 外观，而是它把一个复杂的编辑器拆成了“主工作区 + 工具栏 + 左侧素材/图层 + 右侧检查器 + 可验证输出”的工作台结构，并让状态、操作历史和导出结果都可见。对教学型 Mini-DBMS，最合适的对应关系是：

| m3e-canvas | Mini-DBMS 控制台迁移 |
| --- | --- |
| 画布上的屏幕与节点 | SQL 输入、逻辑计划、物理计划、算子执行链 |
| Parts Palette | 示例 SQL、表/字段目录、可插入语法片段 |
| Layers | 查询阶段树或算子树 |
| Inspector | 当前 Token、AST 节点、算子或 Page 的详细属性 |
| Preview | 执行结果、执行轨迹、页读写动画 |
| Prompt output | `EXPLAIN`/优化计划、可复制的诊断报告 |
| Undo/Redo 与自动保存 | SQL 草稿历史、执行历史和实验状态恢复 |

关键建议：保留项目现有“纸张/墨水/账本”视觉语言，把 m3e-canvas 当作信息架构和交互密度的参考，不复制其高圆角、鲜艳主题或移动端编辑器。

## 1. 上游架构事实

### 1.1 技术形态与部署边界

- 仓库是 Next.js/React 应用，根目录按 `app/`、`components/`、`lib/`、`public/` 和 `docs/` 分层；`package.json` 与源码目录共同表明 UI 组件和无界面逻辑被分开维护。[仓库根目录](https://github.com/lnkiai/m3e-canvas) · [package.json](https://github.com/lnkiai/m3e-canvas/blob/main/package.json)
- README 明确说明其构建产物是静态导出目录 `out/`，由 GitHub Pages 发布；这与“没有服务端账户系统、主要状态留在浏览器”的产品边界一致。[README：Develop](https://github.com/lnkiai/m3e-canvas#develop) · [Security policy](https://github.com/lnkiai/m3e-canvas/blob/main/SECURITY.md)
- README 说明设计内容自动保存在浏览器 `localStorage`，可见其核心编辑循环是 client-side/local-first，而非每一步都依赖后端。[README：What it does](https://github.com/lnkiai/m3e-canvas#what-it-does)

### 1.2 文件职责

- `app/page.tsx` 是应用编排层，承载工作区交互与整体状态；该文件体量很大，说明它是中心协调器，也暴露出“继续增长时需要拆分状态域”的维护风险。[app/page.tsx](https://github.com/lnkiai/m3e-canvas/blob/main/app/page.tsx)
- `components/` 按用户能感知的工作台区域拆分，如 `Toolbar`、`PartsPalette`、`Layers`、`Inspector`、`Preview`、`PromptPanel`、`ThemePanel`；这种按界面职责命名的结构能让答辩者从文件名快速定位功能。[components 目录](https://github.com/lnkiai/m3e-canvas/tree/main/components)
- `lib/` 放置可独立验证的纯逻辑或数据转换，包括项目序列化、提示词生成、主题/颜色/形状 token、整理布局、分享编码与国际化；大量相邻 `*.test.ts` 表明这些逻辑被从视图中抽离后单测。[lib 目录](https://github.com/lnkiai/m3e-canvas/tree/main/lib)
- 贡献指南进一步给出变更位置约定，并要求所有界面字符串保持多语言一致；这是“目录就是职责地图”的直接证据。[CONTRIBUTING.md](https://github.com/lnkiai/m3e-canvas/blob/main/CONTRIBUTING.md)

### 1.3 状态与可逆操作

- README 明示 undo/redo、键盘快捷键、自动保存与“一键整理，再按一次撤销”。这套组合让高频试错成本很低，适合复杂编辑型工具。[README：What it does](https://github.com/lnkiai/m3e-canvas#what-it-does)
- `lib/project.ts` 将项目数据的读取/写入职责从 UI 抽离；`project.test.ts` 紧邻实现，适合参考为 Mini-DBMS 的“会话快照/演示场景”序列化层。[lib/project.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/project.ts) · [lib/project.test.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/project.test.ts)
- `lib/tidy.ts` 与配套测试把“整理”实现为独立、可测试的变换，而不是散落在拖拽 UI 中。[lib/tidy.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/tidy.ts) · [lib/tidy.test.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/tidy.test.ts)

## 2. 可迁移的 UI 与交互模式

### 2.1 工作台而非仪表盘

m3e-canvas 的核心是持续操作同一份对象：中央工作区呈现对象，工具栏切换模式，侧栏选择或检查对象，预览验证结果。Mini-DBMS 也应采用同样的“Operate”模式：用户的第一目标是写 SQL、理解执行并检查页，而不是先看装饰性统计卡。

推荐桌面结构：

```text
┌ 顶栏：数据库 / 会话 / 运行 / 停止 / EXPLAIN / 重置演示 ┐
├ 左 240px ─────┬──────── 主工作区 ────────┬ 右 320px ┤
│ Schema/历史   │ SQL 编辑器               │ Inspector │
│ 阶段导航      │ AST / 计划 / 结果 / Page │ 节点详情  │
└───────────────┴───────────────────────────┴───────────┘
```

这对应上游 `PartsPalette`、`Layers`、`Inspector` 和 `Toolbar` 的职责拆分，而不是复制具体组件造型。[components 目录](https://github.com/lnkiai/m3e-canvas/tree/main/components)

### 2.2 选择—检查—验证闭环

- 在 AST 或物理计划中点选节点，右侧 Inspector 显示输入、输出 schema、估算行数、实际行数、代价、耗时和对应源码位置。
- 在 Page 可视化中点选页或槽位，Inspector 显示 `page_id`、页类型、LSN、free-space、slot offset/length、脏页与 pin count。
- 执行前用“计划”页验证解析/绑定/优化结果；执行后用“结果/轨迹”页验证实际行为。它对应上游“在画布建立关系，再进入 Preview 点通流程”的分离。[README：navigation and preview](https://github.com/lnkiai/m3e-canvas#what-it-does) · [components/Preview.tsx](https://github.com/lnkiai/m3e-canvas/blob/main/components/Preview.tsx)

### 2.3 输出应可复制、可解释

上游不仅展示画布，还把结构转换成自然语言 prompt，并允许复制或导出 PNG。[components/PromptPanel.tsx](https://github.com/lnkiai/m3e-canvas/blob/main/components/PromptPanel.tsx) · [lib/prompt.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/prompt.ts)

Mini-DBMS 可把该模式迁移为：

1. `EXPLAIN` 输出结构化计划树；
2. `EXPLAIN ANALYZE` 显示估算值与实际值对比；
3. “复制优化报告”生成优化前/后计划、规则命中、代价变化、页读取次数、缓存命中率；
4. 每个 Token/AST/算子/Page 节点提供“复制 JSON”，便于报告和答辩。

这是用户所要求“token 要输出优化计划”和“优化前后明细结构变化”的合适交互承载方式。

### 2.4 专业工具级快捷键与反馈

上游把选择/抓手、缩放、适配画布、复制、删除、预览、撤销/重做等高频动作放入键盘，并在 README 提供完整表格。[README：Keyboard](https://github.com/lnkiai/m3e-canvas#keyboard)

可迁移的最小快捷键：`Ctrl+Enter` 执行、`Ctrl+Shift+Enter` EXPLAIN、`Ctrl+L` 聚焦 SQL、`Ctrl+K` 命令面板、`Esc` 停止/关闭、`Ctrl+Z` 恢复 SQL 草稿。按钮仍需有文字/tooltip，快捷键不能成为唯一入口。

## 3. 视觉语言：借鉴原则，不复制皮肤

### 可借鉴

- **语义 token 集中管理**：上游用 `lib/tokens.ts`、`theme.ts`、`color.ts` 把颜色、形状、字体、动效变成可配置系统，并有测试覆盖。[lib/tokens.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/tokens.ts) · [lib/theme.ts](https://github.com/lnkiai/m3e-canvas/blob/main/lib/theme.ts)
- **状态不仅靠颜色**：计划节点应同时使用图标/标签/边框表达“已解析、已优化、运行中、失败”，满足课堂投影和色觉差异场景。
- **密度分层**：中央区域容纳高密度代码和树；右侧只显示当前选择；高级信息可折叠，默认视图保持清晰。
- **动效说明因果**：只在 SQL 阶段推进、算子产出数据、页从磁盘进入 buffer pool 时使用短动效；支持 reduced motion。

### 不建议照搬

- 不采用大面积高饱和主题、过度圆润的 FAB 或玩具化画布；数据库实训控制台需要代码、表格和十六进制/页布局拥有更高视觉权重。
- 不把所有结构都做成自由拖拽。AST、执行计划、B+Tree 与 Page 映射应由系统生成；允许缩放、展开和检查，但不应让用户拖动后改变事实结构。
- 不把运行态仅保存在 `localStorage`。SQL 草稿和面板布局可以本地保存，但数据页、目录、WAL、权限和事务状态必须来自 Mini-DBMS 后端/数据文件，避免 UI 状态伪装成数据库真相。
- 不照搬上游的单一大型页面协调器。Mini-DBMS 本身已有解析、存储、执行三条明确边界，前端也应按领域拆出状态与 API。

## 4. 建议的前端文件结构

```text
web/
├─ app/                       # 壳、路由、全局错误边界
├─ features/
│  ├─ sql-editor/             # SQL 输入、token 高亮、历史
│  ├─ parser-inspector/       # Token 流、AST、语义绑定
│  ├─ plan-explorer/          # 逻辑/物理计划、前后 diff
│  ├─ execution-monitor/      # 算子状态、结果、耗时
│  ├─ storage-inspector/      # file→page→slot→record
│  ├─ buffer-pool/            # frame、pin、dirty、替换
│  └─ access-control/         # 行/列/业务权限解释
├─ components/                # Toolbar、Tree、Inspector、Table 等通用 UI
├─ lib/
│  ├─ api/                    # 后端契约
│  ├─ models/                 # Token/AST/Plan/Page 类型
│  ├─ formatters/             # EXPLAIN、字节与时间格式化
│  └─ session/                # 仅 UI 会话与草稿持久化
└─ styles/tokens.css          # 现有纸张/墨水设计 token
```

该结构吸收上游“可见区域放 components、纯转换放 lib”的优点，同时按本项目三个课程模块继续下钻，使两名成员能解释目录归属和调用边界。

## 5. 建议的首版页面优先级

1. **SQL 工作台**：编辑、Token 流、AST、执行结果与错误定位。
2. **执行计划对比**：优化前后双栏/切换 diff，显示规则、代价、行数与页读数。
3. **存储实验室**：逻辑表/记录到文件/Page/Slot 的映射，可读取真实数据文件元信息。
4. **Buffer Pool**：frame 列表、页命中/缺页、LRU/Clock 轨迹、dirty flush。
5. **事务与权限**：锁等待图、事务状态；用户→角色→业务→表→行策略→字段脱敏的决策解释。

先做 1–3 能完整讲通“解析→计划→执行→页访问”；4–5 再承接并发、缓存和细粒度权限加分项。

## 6. 研究边界与许可

- 本文没有复用 m3e-canvas 源码或素材，只提炼公开仓库中的架构和交互模式。
- 若以后直接复制代码，应遵守其 MIT 许可证并保留版权和许可声明。[LICENSE](https://github.com/lnkiai/m3e-canvas/blob/main/LICENSE)
- 上游的 AI key 本地保存策略仅是其静态工具的安全边界说明，不应直接成为本项目权限/token 设计依据。[SECURITY.md](https://github.com/lnkiai/m3e-canvas/blob/main/SECURITY.md)

