"""
Cross-platform file locking abstraction.
"""
import os
import contextlib
from agent.platform.platform_info import platform_info

if platform_info.is_windows:
    import msvcrt
else:
    import fcntl

class FileLocker:
    @staticmethod
    def lock(file_descriptor, blocking: bool = True):
        if platform_info.is_windows:
            mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
            try:
                msvcrt.locking(file_descriptor, mode, 1)
            except OSError as e:
                if not blocking and e.errno == 36: # Resource deadlock avoided / lock failed
                    raise BlockingIOError()
                raise
        else:
            mode = fcntl.LOCK_EX
            if not blocking:
                mode |= fcntl.LOCK_NB
            fcntl.flock(file_descriptor, mode)

    @staticmethod
    def unlock(file_descriptor):
        if platform_info.is_windows:
            msvcrt.locking(file_descriptor, msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(file_descriptor, fcntl.LOCK_UN)

    @staticmethod
    @contextlib.contextmanager
    def context(file_descriptor, blocking: bool = True):
        FileLocker.lock(file_descriptor, blocking)
        try:
            yield
        finally:
            FileLocker.unlock(file_descriptor)