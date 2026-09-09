from __future__ import annotations

import json
import os
import zlib
from pathlib import Path
from threading import RLock
from time import sleep
from uuid import uuid4
from .errors import CorruptPage, InvalidPage

PAGE_SIZE = 4096
PAYLOAD_SIZE = PAGE_SIZE
EXTENT_PAGES = 64
LEGACY_HEADER_SIZE = 20


class PageFile:
    """完整 4KB 页文件；校验和/generation 存入双份页目录控制文件。"""
    def __init__(self, directory: str | Path):
        self.root = Path(directory); self.root.mkdir(parents=True, exist_ok=True)
        self.data_path = self.root / "tablespace.dat"
        self.control_paths = [self.root / "control.0.json", self.root / "control.1.json"]
        self.lock = RLock(); self.reads = self.writes = self.allocations = self.releases = 0
        if not self.data_path.exists(): self.data_path.write_bytes(b"")
        self._control_needs_save=False;self.control = self._load_control()
        if self._control_needs_save:self._save_control()

    def _default_control(self):
        return {"version":2,"generation":0,"page_count":0,"allocated":[],"page_generations":[],"checksums":[],"checkpoint_lsn":0}

    def _load_control(self):
        copies=[]
        for path in self.control_paths:
            try:
                value=json.loads(path.read_text(encoding="utf-8"))
                if value.get("version") in (1,2):copies.append(value)
            except (OSError,ValueError):pass
        control=max(copies,key=lambda x:x.get("generation",0)) if copies else self._default_control()
        if control.get("version")==1:
            self._migrate_v1_pages(control)
            control["version"]=2;control["page_generations"]=[1 if used else 0 for used in control["allocated"]]
            control["checksums"]=[zlib.crc32(self._read_raw(i)) if used else 0 for i,used in enumerate(control["allocated"])]
            self._control_needs_save=True
        if control["page_count"]*PAGE_SIZE>self.data_path.stat().st_size:raise CorruptPage("control file points beyond tablespace")
        return control

    def _read_raw(self,page_id):
        with self.data_path.open("rb") as f:f.seek(page_id*PAGE_SIZE);return f.read(PAGE_SIZE)

    def _migrate_v1_pages(self,control):
        """v1 把 20B 物理头塞在 4KB frame 内；v2 将头信息移入控制文件。"""
        temp=self.data_path.with_suffix(".migrate.tmp")
        with self.data_path.open("rb") as source,temp.open("wb") as target:
            for used in control["allocated"]:
                legacy=source.read(PAGE_SIZE)
                page=(legacy[LEGACY_HEADER_SIZE:]+bytes(LEGACY_HEADER_SIZE)) if used else bytes(PAGE_SIZE)
                target.write(page)
            target.flush();os.fsync(target.fileno())
        os.replace(temp,self.data_path)

    def _save_control(self):
        self.control["generation"]+=1;raw=json.dumps(self.control,ensure_ascii=False,sort_keys=True).encode()
        for path in self.control_paths:
            temp=path.with_name(path.name+f".{uuid4().hex}.tmp")
            with temp.open("wb") as f:f.write(raw);f.flush();os.fsync(f.fileno())
            for attempt in range(3):
                try:os.replace(temp,path);break
                except PermissionError:
                    if attempt==2:raise
                    sleep(.02*(attempt+1))

    def _grow_extent(self):
        start=self.control["page_count"]
        with self.data_path.open("ab") as f:f.write(bytes(PAGE_SIZE*EXTENT_PAGES));f.flush();os.fsync(f.fileno())
        self.control["page_count"]+=EXTENT_PAGES;self.control["allocated"].extend([False]*EXTENT_PAGES)
        self.control["page_generations"].extend([0]*EXTENT_PAGES);self.control["checksums"].extend([0]*EXTENT_PAGES);self._save_control();return start

    def allocate_page(self):
        with self.lock:
            try:page_id=self.control["allocated"].index(False)
            except ValueError:page_id=self._grow_extent()
            self.control["allocated"][page_id]=True;self.control["page_generations"][page_id]=1
            self.control["checksums"][page_id]=zlib.crc32(bytes(PAGE_SIZE));self.allocations+=1;self._save_control();return page_id

    def release_page(self,page_id):
        with self.lock:
            self._validate(page_id);self.control["allocated"][page_id]=False;self.control["page_generations"][page_id]=0;self.control["checksums"][page_id]=0;self.releases+=1
            with self.data_path.open("r+b") as f:f.seek(page_id*PAGE_SIZE);f.write(bytes(PAGE_SIZE));f.flush();os.fsync(f.fileno())
            self._save_control()

    def _validate(self,page_id):
        if page_id<0 or page_id>=self.control["page_count"] or not self.control["allocated"][page_id]:raise InvalidPage(f"page {page_id} is not allocated")

    def read_page(self,page_id):
        with self.lock:
            self._validate(page_id)
            payload=self._read_raw(page_id)
            self.reads+=1
            expected=self.control["checksums"][page_id]
            if len(payload)!=PAGE_SIZE or (expected and zlib.crc32(payload)!=expected):raise CorruptPage(f"checksum mismatch on page {page_id}")
            return payload,self.control["page_generations"][page_id]

    def write_page(self,page_id,payload,generation):
        if len(payload)!=PAGE_SIZE:raise ValueError(f"page must be exactly {PAGE_SIZE} bytes")
        with self.lock:
            self._validate(page_id)
            with self.data_path.open("r+b") as f:f.seek(page_id*PAGE_SIZE);f.write(payload);f.flush();os.fsync(f.fileno())
            self.control["page_generations"][page_id]=generation;self.control["checksums"][page_id]=zlib.crc32(payload);self.writes+=1;self._save_control()

    def set_checkpoint(self,lsn):self.control["checkpoint_lsn"]=lsn;self._save_control()
    @property
    def checkpoint_lsn(self):return self.control["checkpoint_lsn"]
    def page_directory(self):
        return [{"extent":i//EXTENT_PAGES,"page_id":i,"allocated":used,"offset":i*PAGE_SIZE,"generation":self.control["page_generations"][i]} for i,used in enumerate(self.control["allocated"])]
