"""
预写日志（WAL）模块。

功能：
- 以追加写方式记录页级 redo 日志，并在每条日志落盘后推进 durable_lsn。
- 为脏页刷盘提供写前日志屏障，保证“先写 WAL，再写数据页”。
- 在系统重启时为恢复流程提供可重放日志记录。

对应需求文档：
- 第 2.2 节“存储介质（必做）”中的持久化要求。
- 第 5.1 节“缓存基本能力（必做）”中脏页写回的一致性保障。
- 第 7.2 节“必须满足的集成要求”中对物理访问可靠性的支撑。
- 第 8.3 节“持久化验证（必做）”中的重启恢复。
"""
import base64
import json
import os
import zlib
from pathlib import Path
from threading import RLock

class WriteAheadLog:
    """只追加 redo WAL；每条记录 fsync 后才允许对应脏页落盘。"""

    def __init__(self, path: Path):
        """初始化对象状态和依赖。"""
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = RLock()
        self.next_lsn = 1
        self.durable_lsn = 0
        for record in self.records():
            self.next_lsn = max(self.next_lsn, record['lsn'] + 1)
            self.durable_lsn = max(self.durable_lsn, record['lsn'])

    def append_page(self, page_id, generation, payload):
        """完成append page相关处理。"""
        with self.lock:
            record = {'lsn': self.next_lsn, 'kind': 'PAGE', 'page_id': page_id, 'generation': generation, 'payload': base64.b64encode(payload).decode(), 'crc32': zlib.crc32(payload)}
            raw = (json.dumps(record, separators=(',', ':')) + '\n').encode()
            with self.path.open('ab') as f:
                f.write(raw)
                f.flush()
                os.fsync(f.fileno())
            self.durable_lsn = self.next_lsn
            self.next_lsn += 1
            return self.durable_lsn

    def records(self):
        """遍历页面中的有效槽记录。"""
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_bytes().splitlines():
            try:
                record = json.loads(line)
                payload = base64.b64decode(record['payload'])
                if zlib.crc32(payload) == record['crc32']:
                    out.append(record)
            except Exception:
                break
        return out
