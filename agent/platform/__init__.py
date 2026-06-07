"""
Platform layer public API.
"""
from .platform_info import platform_info
from .ipc import IpcSocket
from .file_locker import FileLocker
from .process import ProcessManager
from .daemon import DaemonManager

__all__ = [
    "platform_info",
    "IpcSocket",
    "FileLocker",
    "ProcessManager",
    "DaemonManager",
]