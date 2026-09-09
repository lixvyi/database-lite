# 成员 B 实训报告：操作系统页式存储

## 工作目标

实现固定页文件、缓存、替换策略和持久化页接口，为数据库引擎提供统一的底层访问能力。

## 主要实现

PageFile 将 `page_id` 映射为 `page_id × 4096`，使用位图管理页面分配、释放和复用。PageCache 通过 OrderedDict 实现 LRU/FIFO，pin 保护使用中页，dirty 控制写回，并记录命中、未命中、淘汰和刷新事件。

本部分只保留两个扩展。第一项是按 64 页 Extent 扩展文件，第二项是页级 redo WAL/Checkpoint。WAL 屏障保证日志先于数据页落盘，generation 支持幂等重放。查询调度器、Undo、MVCC 和索引不在实现范围。

## 问题与定位

Windows 测试结束时曾出现临时文件被占用，原因是 HTTPServer 只 shutdown、未关闭监听句柄；增加 `server_close()` 后释放。测试清理也是系统软件正确性的一部分。

## AI 辅助说明

AI 协助整理页格式、测试清单和注释；页偏移、缓存边界、WAL 顺序和磁盘内容由项目组通过源码和测试验证。

## 收获

本模块把文件 I/O、固定页、缓存与 WAL 组合成稳定 PageStore 接口。更复杂的调度、Undo、MVCC 和索引留作后续方向。
