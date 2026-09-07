import json
import tempfile
import time
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from os_sim import QueryScheduler,StorageService
from os_sim.page_file import PAYLOAD_SIZE


def timed(fn):
    start=time.perf_counter();value=fn();return value,(time.perf_counter()-start)*1000


def main():
    with tempfile.TemporaryDirectory() as d:
        store=StorageService(d,cache_pages=8);pid=store.allocate_page()
        _,cold_ms=timed(lambda:store.read_page(pid));before=store.file.reads
        _,warm_ms=timed(lambda:[store.read_page(pid) for _ in range(1000)])
        cache={"cold_read_ms":cold_ms,"warm_1000_reads_ms":warm_ms,"disk_reads_for_1000":store.file.reads-before,"stats":store.stats()};store.close()
    def io_task(i):time.sleep(.001);return i
    _,serial_ms=timed(lambda:[io_task(i) for i in range(1000)])
    scheduler=QueryScheduler(workers=8,queue_capacity=64)
    futures,parallel_ms=timed(lambda:[scheduler.submit(io_task,i) for i in range(1000)])
    _,wait_ms=timed(lambda:[f.result() for f in futures]);scheduler_stats=scheduler.stats();scheduler.close()
    print(json.dumps({"cache":cache,"queue":{"serial_1000_ms":serial_ms,"submit_ms":parallel_ms,"complete_wait_ms":wait_ms,"parallel_total_ms":parallel_ms+wait_ms,"speedup":serial_ms/(parallel_ms+wait_ms),"stats":scheduler_stats}},ensure_ascii=False,indent=2))


if __name__=="__main__":main()
