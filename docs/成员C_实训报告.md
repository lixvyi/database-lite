# 成员 C 实训报告：数据库引擎与系统集成

## 工作目标

连接 SQL 编译器和操作系统页服务，实现四条核心 SQL 的真实执行，并保证用户数据和系统目录重启后可恢复。

## 主要实现

Executor 根据 PlanNode 执行 CreateTable、Insert、SeqScan、Filter、Project 和 Delete。TableHeap 通过页链扫描表，以 `(page_id, slot_id)` 作为 RID。RecordCodec 把 Row 编码为字段数、NULL 位图和字段体；SlottedPage 使用页头、槽目录和从页尾反向增长的记录区。

PagedCatalog 从物理页 0 启动，目录的每一列定义都是普通编码记录。目录超过一页时继续分配槽页，因此系统目录和用户数据都通过同一 PageStore 持久化。OSBufferAdapter 是数据库层访问 StorageService 的唯一边界。

数据库引擎只配合实现 UPDATE 和 ORDER BY 两项扩展。UPDATE 使用表级写锁并执行页内更新或 RID 迁移；ORDER BY 使用内存稳定排序。权限、查询调度、索引、事务回滚和 MVCC 不在本次范围。

## 问题与定位

旧版目录把全部 JSON 放在一个 4KB 页面，容量有限，也不够符合“特殊表”要求。新版把目录行编码进 SlottedPage，并支持目录页链。`VARCHAR(n)` 同时在语义层和编码层校验，避免绕过检查写入超长数据。

## AI 辅助说明

AI 用于接口检查、边界用例和文档整理。项目组通过多页目录、300 行跨页、删除后查询和重启恢复测试验证实际行为。

## 收获

本模块说明执行计划如何变成行迭代，逻辑行如何变成页面字节，以及固定的系统目录入口如何在启动时恢复整个数据库结构。
