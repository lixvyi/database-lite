# 成员 A 实训报告：SQL 编译前端与规则优化

## 工作目标

把 SQL 字符串稳定转换为可执行 Logical Plan，并在每阶段保留可解释结构和精确错误位置。

## 主要实现

Lexer 逐字符扫描并维护 offset、line、column，区分关键字、标识符、数值、字符串、操作符与分隔符。Parser 使用递归下降，每个函数对应一个非终结符；分层调用保证乘除、加减、比较、NOT、AND、OR 的优先级。AST 只保存结构、值和源码位置，不耦合执行器。第三阶段从指导书可选项中实现 UPDATE 与 ORDER BY：Parser 分别构造赋值列表和排序键，SemanticAnalyzer 检查目标列、表达式类型、排序列存在性。

SemanticAnalyzer 把标识符绑定到 Catalog 列定义，并集中处理类型规则。PlanBuilder 将 SELECT 转换为 SeqScan、Filter、Sort、Project，将 UPDATE 转为 Update、Filter、SeqScan。Optimizer 深拷贝原计划后执行常量折叠、布尔化简和恒真 Filter 删除，因此可以并排展示优化前后结构。

## 问题与定位

多语句 `CREATE; INSERT;` 最初被整体语义分析，INSERT 看不到尚未执行的表。修复为执行入口按语句顺序完成“分析—执行”。这说明 Catalog 状态属于语义环境，多语句不能简单视为彼此独立。

## AI 辅助说明

AI 用于初始骨架、反例和文档整理；文法、AST 接口、类型规则、优化等价条件及测试结果由项目组确认。随机抽查时应从源码解释，而不是背报告。

## 收获

本模块把词法、语法、符号表、类型系统和 IR 与数据库查询计划连接起来。重点不是 SQL 数量，而是结构可扩展、错误可定位、优化可验证。
