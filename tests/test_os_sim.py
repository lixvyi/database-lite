import tempfile
import unittest
import json
from pathlib import Path

from os_sim import StorageService
from os_sim.errors import InvalidPage,WriteBarrierError
from os_sim.page_file import EXTENT_PAGES,PAYLOAD_SIZE


def payload(text):
    raw=text.encode("utf-8")
    return raw+bytes(PAYLOAD_SIZE-len(raw))


class PageAndDirectoryTests(unittest.TestCase):
    def test_v1_page_payload_migrates_to_full_4kb(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);raw=b"legacy"+bytes(4076-6)
            (root/"tablespace.dat").write_bytes(bytes(20)+raw+bytes(4096*63))
            control={"version":1,"generation":1,"page_count":64,"allocated":[True]+[False]*63,"checkpoint_lsn":0}
            for name in ("control.0.json","control.1.json"):(root/name).write_text(json.dumps(control),encoding="utf-8")
            store=StorageService(root)
            self.assertEqual(len(store.read_page(0)),4096);self.assertTrue(store.read_page(0).startswith(b"legacy"))
            self.assertEqual(store.file.control["version"],2);store.close()
    def test_extent_allocation_release_and_reuse(self):
        with tempfile.TemporaryDirectory() as d:
            store=StorageService(d)
            ids=[store.allocate_page() for _ in range(EXTENT_PAGES+1)]
            self.assertEqual(ids[-1],EXTENT_PAGES);self.assertEqual(store.stats()["total_pages"],EXTENT_PAGES*2)
            store.release_page(7);self.assertEqual(store.allocate_page(),7)
            self.assertEqual(store.page_directory()[7]["offset"],7*4096);store.close()
    def test_correct_read_write_and_release_guard(self):
        with tempfile.TemporaryDirectory() as d:
            store=StorageService(d,dirty_ratio=2);pid=store.allocate_page();store.write_page(pid,payload("中文页"))
            self.assertTrue(store.read_page(pid).startswith("中文页".encode()));store.checkpoint();store.release_page(pid)
            with self.assertRaises(InvalidPage):store.read_page(pid)


class CacheTests(unittest.TestCase):
    def test_cache_reduces_disk_reads(self):
        with tempfile.TemporaryDirectory() as d:
            store=StorageService(d,cache_pages=2);pid=store.allocate_page()
            baseline=store.file.reads
            for _ in range(100):store.read_page(pid)
            stats=store.stats();self.assertEqual(store.file.reads-baseline,1);self.assertEqual(stats["hits"],99);store.close()
    def test_lru_and_fifo_have_observable_difference(self):
        with tempfile.TemporaryDirectory() as d1,tempfile.TemporaryDirectory() as d2:
            def resident(root,policy):
                s=StorageService(root,cache_pages=2,policy=policy);p=[s.allocate_page() for _ in range(3)]
                s.read_page(p[0]);s.read_page(p[1]);s.read_page(p[0]);s.read_page(p[2]);keys=set(s.cache.frames);s.close();return keys
            self.assertEqual(resident(d1,"LRU"),{0,2});self.assertEqual(resident(d2,"FIFO"),{1,2})
    def test_pinned_frames_are_not_evicted_and_events_are_recorded(self):
        with tempfile.TemporaryDirectory() as d:
            store=StorageService(d,cache_pages=1);first=store.allocate_page();second=store.allocate_page()
            store.cache.fetch(first)
            with self.assertRaises(RuntimeError):store.cache.fetch(second)
            store.cache.unpin(first);store.cache.fetch(second);store.cache.unpin(second)
            self.assertEqual([event["event"] for event in store.cache.events],["miss","evict","miss"])
            store.close()
    def test_wal_barrier_prevents_unsafe_flush(self):
        with tempfile.TemporaryDirectory() as d:
            store=StorageService(d,dirty_ratio=2);pid=store.allocate_page();store.write_page(pid,payload("dirty"));store.wal.durable_lsn=0
            with self.assertRaises(WriteBarrierError):store.cache.flush_page(pid)


class RecoveryTests(unittest.TestCase):
    def test_restart_replays_uncheckpointed_page(self):
        with tempfile.TemporaryDirectory() as d:
            crashed=StorageService(d,dirty_ratio=2);pid=crashed.allocate_page();crashed.write_page(pid,payload("committed-in-wal"))
            recovered=StorageService(d,dirty_ratio=2)
            self.assertGreaterEqual(recovered.stats()["recovered_pages"],1)
            self.assertTrue(recovered.read_page(pid).startswith(b"committed-in-wal"));recovered.close()
    def test_checkpoint_makes_data_and_lsn_consistent(self):
        with tempfile.TemporaryDirectory() as d:
            store=StorageService(d,dirty_ratio=2);pid=store.allocate_page();lsn=store.write_page(pid,payload("safe"));info=store.checkpoint()
            self.assertEqual(info["checkpoint_lsn"],lsn);self.assertEqual(store.stats()["dirty"],0);store.close()


if __name__=="__main__":unittest.main()
