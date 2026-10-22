"""ctypes facade for the optional local mGBA adapter."""
from __future__ import annotations
import ctypes as C
from pathlib import Path


class Session:
    def __init__(self, rom, library="build/mgba_bridge.so"):
        self.lib = C.CDLL(str(Path(library).resolve()))
        signatures = {
            "open": ([C.c_char_p], C.c_void_p), "close": ([C.c_void_p], None),
            "frames": ([C.c_void_p,C.c_uint,C.c_uint],None),
            "pixels": ([C.c_void_p],C.POINTER(C.c_uint32)),
            "read": ([C.c_void_p,C.c_uint32],C.c_uint32),
            "write": ([C.c_void_p,C.c_uint32,C.c_uint],None),
            "reg": ([C.c_void_p,C.c_uint],C.c_uint32),
            "state_size": ([C.c_void_p], C.c_size_t),
            "save": ([C.c_void_p,C.c_void_p],C.c_int),
            "load": ([C.c_void_p,C.c_void_p],C.c_int),
            "call": ([C.c_void_p]+[C.c_uint32]*5,C.c_int),
            "export_sram": ([C.c_void_p,C.c_void_p,C.c_size_t],C.c_size_t),
            "import_sram": ([C.c_void_p,C.c_void_p,C.c_size_t],C.c_int),
            "reset": ([C.c_void_p],None),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.lib, "session_"+name)
            fn.argtypes, fn.restype = args, result
        self.handle = self.lib.session_open(str(Path(rom).resolve()).encode())
        self.frames_run = 0
        if not self.handle:
            raise RuntimeError("mGBA could not open the ROM")

    def frames(self, count, keys=0):
        self.lib.session_frames(self.handle,count,keys)
        self.frames_run += count

    def press(self, keys, hold=1, settle=30):
        self.frames(hold,keys)
        self.frames(settle)

    def read(self, address, length):
        return bytes(self.lib.session_read(self.handle,address+i) for i in range(length))

    def write(self, address, data):
        for i,v in enumerate(data):
            self.lib.session_write(self.handle,address+i,v)

    def screenshot(self, path):
        from PIL import Image
        raw = C.string_at(self.lib.session_pixels(self.handle),240*160*4)
        Image.frombytes("RGBA",(240,160),raw).convert("RGB").save(path)

    def state(self):
        buf = C.create_string_buffer(self.lib.session_state_size(self.handle))
        if not self.lib.session_save(self.handle,buf):
            raise RuntimeError("save state failed")
        return buf

    def restore(self, buf):
        if not self.lib.session_load(self.handle,buf):
            raise RuntimeError("load state failed")

    def call(self, address, r0=0,r1=0,r2=0,r3=0):
        if not self.lib.session_call(self.handle,address,r0,r1,r2,r3):
            raise RuntimeError("function probe did not return")
        return self.lib.session_reg(self.handle,0)

    def close(self):
        if self.handle:
            self.lib.session_close(self.handle)
            self.handle = None

    def sram(self):
        buf = C.create_string_buffer(0x20000)
        size = self.lib.session_export_sram(self.handle,buf,len(buf))
        if not 0 < size <= len(buf):
            raise RuntimeError("could not export SRAM")
        return buf.raw[:size]

    def load_sram(self, data):
        buf = C.create_string_buffer(data)
        if not self.lib.session_import_sram(self.handle,buf,len(data)):
            raise RuntimeError("could not import SRAM")
