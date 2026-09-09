import json
import tempfile
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from os_sim import StorageService


def timed(fn):
    start=time.perf_counter();value=fn();return value,(time.perf_counter()-start)*1000


def main():
    with tempfile.TemporaryDirectory() as d:
        store=StorageService(d,cache_pages=8);pid=store.allocate_page()
        _,cold_ms=timed(lambda:store.read_page(pid));before=store.file.reads
        _,warm_ms=timed(lambda:[store.read_page(pid) for _ in range(1000)])
        cache={"cold_read_ms":cold_ms,"warm_1000_reads_ms":warm_ms,"disk_reads_for_1000":store.file.reads-before,"stats":store.stats()};store.close()
    print(json.dumps({"cache":cache},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
