# MiniSQL 文法（与 `minidb/parser.py` 一致）

```ebnf
program        ::= statement* EOF ;
statement      ::= create_stmt | insert_stmt | select_stmt | delete_stmt | update_stmt ;
create_stmt    ::= CREATE TABLE identifier "(" column_def ("," column_def)* ")" ";" ;
column_def     ::= identifier (INT | VARCHAR ("(" integer ")")?) ;
insert_stmt    ::= INSERT INTO identifier "(" id_list ")"
                   VALUES "(" value_list ")" ";" ;
select_stmt    ::= SELECT ("*" | id_list) FROM identifier where_opt order_opt ";" ;
delete_stmt    ::= DELETE FROM identifier where_opt ";" ;
update_stmt    ::= UPDATE identifier SET assignment ("," assignment)* where_opt ";" ;
assignment     ::= identifier "=" expression ;
where_opt      ::= WHERE expression | ε ;
order_opt      ::= ORDER BY order_item ("," order_item)* | ε ;
order_item     ::= identifier (ASC | DESC)? ;
id_list        ::= identifier ("," identifier)* ;
value_list     ::= primary ("," primary)* ;
expression     ::= or_expr ;
or_expr        ::= and_expr (OR and_expr)* ;
and_expr       ::= not_expr (AND not_expr)* ;
not_expr       ::= NOT not_expr | comparison ;
comparison     ::= additive (("="|"=="|"!="|">"|">="|"<"|"<=") additive)? ;
additive       ::= multiplicative (("+"|"-") multiplicative)* ;
multiplicative ::= primary (("*"|"/") primary)* ;
primary        ::= identifier | integer | float | string
                 | "(" expression ")" ;
```

优先级从高到低为：括号/常量/标识符、乘除、加减、比较、NOT、AND、OR。递归下降函数逐层对应非终结符，因此没有直接左递归。

`UPDATE` 与 `ORDER BY` 是 SQL 编译器和数据库引擎共同选定的两项扩展。未实现 `EXPLAIN`、`JOIN`、`GROUP BY`、SQL `NULL` 字面量及其他扩展语法，避免扩大答辩范围。优化前后计划通过 `Database.inspect()` 展示，不需要额外 SQL 语句。
