"""统一格式化核心源码，并为函数补充简短中文用途说明。"""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    *sorted((ROOT / "minidb").glob("*.py")),
    *sorted((ROOT / "minidb" / "storage").glob("*.py")),
    *sorted((ROOT / "os_sim").glob("*.py")),
    ROOT / "minidb_cli.py",
    ROOT / "os_sim_cli.py",
    ROOT / "server.py",
]

SKIP_NAMES = {"__init__.py", "errors.py"}

PURPOSES = {
    "__init__": "初始化对象状态和依赖。",
    "tokenize": "扫描SQL文本并生成Token序列。",
    "advance": "前移字符游标并维护行列位置。",
    "current": "返回当前正在处理的元素。",
    "match": "尝试匹配可选符号并推进游标。",
    "expect": "检查必需符号，不匹配时报告错误。",
    "identifier": "读取并返回一个标识符Token。",
    "parse_all": "解析输入中的全部SQL语句。",
    "statement": "按首关键字分派具体语句解析。",
    "create": "解析CREATE TABLE语句。",
    "insert": "解析INSERT语句。",
    "select": "解析SELECT语句。",
    "delete": "解析DELETE语句。",
    "update": "解析UPDATE语句。",
    "expression": "解析完整表达式。",
    "or_expr": "解析OR逻辑表达式。",
    "and_expr": "解析AND逻辑表达式。",
    "not_expr": "解析NOT一元表达式。",
    "comparison": "解析比较表达式。",
    "additive": "解析加减表达式。",
    "multiplicative": "解析乘除表达式。",
    "primary": "解析标识符、常量或括号表达式。",
    "analyze": "执行语句级语义检查。",
    "expr": "递归检查并推导表达式类型。",
    "check_varchar_length": "检查VARCHAR常量是否超过声明长度。",
    "build": "把AST转换为逻辑执行计划。",
    "optimize": "复制并优化逻辑执行计划。",
    "fold": "递归折叠常量和布尔表达式。",
    "eval_const": "计算仅由常量组成的表达式。",
    "expr_text": "把表达式AST转换为展示文本。",
    "to_dict": "把对象递归转换为可序列化字典。",
    "format": "生成便于阅读的树形文本。",
    "load": "从持久化存储加载状态。",
    "save": "把当前状态持久化保存。",
    "create_table": "登记并持久化新表结构。",
    "exists": "判断指定对象是否存在。",
    "table": "查找并返回表结构。",
    "column": "查找并返回列结构。",
    "rows": "生成当前节点对应的记录集合。",
    "evaluate": "结合当前行递归计算表达式。",
    "acquire_read": "获取共享读锁。",
    "release_read": "释放共享读锁。",
    "acquire_write": "获取独占写锁。",
    "release_write": "释放独占写锁。",
    "scan": "顺序扫描表中的全部有效记录。",
    "run": "按照计划类型执行数据库操作。",
    "lock": "取得指定表对应的读写锁。",
    "execute": "编译并执行SQL语句。",
    "inspect": "返回SQL各编译阶段的检查结果。",
    "close": "刷新状态并释放底层资源。",
    "allocate_page": "分配并返回一个可用物理页。",
    "release_page": "释放指定物理页供后续复用。",
    "read_page": "读取指定页的完整内容。",
    "write_page": "写入指定页的完整内容。",
    "new_page": "创建并固定一个新缓存页。",
    "discard_page": "丢弃未投入使用的新页面。",
    "fetch": "从缓存或磁盘取得指定页面。",
    "unpin": "减少页面固定计数并记录脏状态。",
    "flush": "把脏页安全写回磁盘。",
    "flush_page": "把指定脏页安全写回磁盘。",
    "flush_all": "把全部脏页安全写回磁盘。",
    "checkpoint": "刷新脏页并推进检查点。",
    "stats": "返回缓存和存储运行统计。",
    "status": "返回当前存储服务状态。",
    "append": "追加一条预写日志记录。",
    "records": "遍历页面中的有效槽记录。",
    "encode": "按表结构把行编码为二进制记录。",
    "decode": "按表结构把二进制记录解码为行。",
    "page": "以上下文方式固定并访问缓存页。",
    "main": "解析命令行参数并运行入口逻辑。",
    "connect": "建立并配置业务数据库连接。",
    "init_db": "初始化业务演示数据库。",
    "do_GET": "处理HTTP GET请求。",
    "do_POST": "处理HTTP POST请求。",
    "do_OPTIONS": "处理HTTP跨域预检请求。",
    "respond": "返回JSON格式的HTTP响应。",
    "read_json": "读取并解析HTTP请求体。",
}


class DocstringInjector(ast.NodeTransformer):
    """为缺少说明的函数加入简短中文用途注释。"""

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef):
        self.generic_visit(node)
        if ast.get_docstring(node, clean=False) is None:
            purpose = PURPOSES.get(node.name)
            if purpose is None:
                readable = node.name.strip("_").replace("_", " ") or "内部操作"
                purpose = f"完成{readable}相关处理。"
            node.body.insert(0, ast.Expr(value=ast.Constant(value=purpose)))
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef):
        return self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        return self._visit_function(node)


def format_file(path: Path) -> None:
    """格式化单个Python文件并保留程序语义。"""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    tree = DocstringInjector().visit(tree)
    ast.fix_missing_locations(tree)
    formatted = ast.unparse(tree).rstrip() + "\n"
    path.write_text(formatted, encoding="utf-8")


def main() -> None:
    """处理MiniDB与OS仿真的主要源码文件。"""
    for path in TARGETS:
        if path.name in SKIP_NAMES or not path.exists():
            continue
        format_file(path)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
