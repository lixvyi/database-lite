# 成员 B 实训报告：页式存储、执行与系统机制

## 工作目标

不借助现成数据库完成行数据编码、分页、缓存、持久化和算子执行，并解释逻辑表到磁盘字节的映射。

## 主要实现

PageFile 将 `page_id` 映射为 `page_id × 4096`，并按 64 页 Extent 管理空闲位图。SlottedPage 使用页头、槽目录和从页尾反向增长的记录区；RID 由页号和槽号组成。RecordCodec 使用 NULL bitmap、8 字节整数和长度前缀 UTF-8 字符串。PagedCatalog 固定在页 0，用户表通过 `first_page` 与 Page 的 `next_page` 映射为物理页链。

StorageService 用 OrderedDict 表达 LRU/FIFO，pin 保护使用中页，dirty 控制写回；WAL 屏障保证日志先于数据页落盘，checkpoint 和 generation 支持重启恢复。Executor 按算子树拉取记录，Delete 写 tombstone，Update 原槽更新或迁移 RID，Sort 完成稳定多键排序。RWLock 支持多读单写，Authorizer 组合业务动作、列集合和行过滤器。

## 问题与定位

Windows 测试结束时曾出现临时文件被占用，原因是 HTTPServer 只 shutdown、未关闭监听句柄；增加 `server_close()` 后释放。测试清理也是系统软件正确性的一部分。

## AI 辅助说明

AI 协助整理页格式、测试清单和注释；页偏移、槽目录方向、缓存边界、权限时机和磁盘内容由项目组通过源码和测试验证。

## 收获

本模块把文件 I/O、页、缓存、WAL、锁与记录、RID、执行器、Catalog 连接起来。行锁、Undo 和 MVCC 必须建立在当前明确边界之上。
