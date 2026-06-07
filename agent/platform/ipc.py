"""
Cross-platform IPC Socket.
"""
import socket
import os
import tempfile
import uuid
from typing import Tuple, Optional

from agent.platform.platform_info import platform_info

class IpcSocket:
    """
    Abstracts over Unix Domain Sockets (on Unix) and Local TCP Sockets (on Windows).
    """

    @staticmethod
    def create_server_socket() -> Tuple[socket.socket, str, Optional[int], Optional[str]]:
        """
        Creates an IPC server socket.
        Returns:
            (server_sock, sock_path, port, token)
        On Unix, returns (sock, path, None, None).
        On Windows, returns (sock, None, port, token).
        """
        if platform_info.is_windows:
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.bind(("127.0.0.1", 0))
            server_port = server_sock.getsockname()[1]
            server_sock.listen(1)
            token = uuid.uuid4().hex
            return server_sock, None, server_port, token
        else:
            _sock_tmpdir = "/tmp" if platform_info.is_macos else tempfile.gettempdir()
            sock_path = os.path.join(_sock_tmpdir, f"hermes_rpc_{uuid.uuid4().hex}.sock")
            server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server_sock.bind(sock_path)
            os.chmod(sock_path, 0o600)
            server_sock.listen(1)
            return server_sock, sock_path, None, None

    @staticmethod
    def cleanup_server_socket(sock_path: Optional[str]) -> None:
        """
        Cleans up the socket file if any.
        """
        if sock_path:
            try:
                os.unlink(sock_path)
            except OSError:
                pass

    @staticmethod
    def get_client_connect_code() -> str:
        """
        Returns the Python source code string for `_connect()` function to be injected in the stub.
        """
        if platform_info.is_windows:
            return '''\
def _connect():
    global _sock
    if _sock is None:
        port = int(os.environ["HERMES_RPC_PORT"])
        token = os.environ["HERMES_RPC_TOKEN"]
        _sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _sock.connect(("127.0.0.1", port))
        _sock.settimeout(300)
        # Authenticate with the server
        _sock.sendall((token + "\\n").encode())
    return _sock
'''
        else:
            return '''\
def _connect():
    global _sock
    if _sock is None:
        _sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        _sock.connect(os.environ["HERMES_RPC_SOCKET"])
        _sock.settimeout(300)
    return _sock
'''
