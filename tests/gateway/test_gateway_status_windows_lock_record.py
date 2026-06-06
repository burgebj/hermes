from gateway import status as gateway_status


def test_lock_record_detects_windows_main_py_gateway_argv():
    record = {
        "pid": 12496,
        "kind": "hermes-gateway",
        "argv": [
            r"C:\Users\Admin\AppData\Local\hermes\hermes-agent\hermes_cli\main.py",
            "gateway",
            "run",
            "--replace",
        ],
        "start_time": None,
    }

    assert gateway_status._record_looks_like_gateway(record) is True
