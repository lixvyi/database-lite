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
