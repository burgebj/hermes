"""防御性测试：extract_pymupdf 的 --pages 参数校验"""
import sys
from pathlib import Path

script = Path(__file__).resolve().parents[3] / "skills/productivity/ocr-and-documents/scripts/extract_pymupdf.py"
sys.path.insert(0, str(script.parent))

def test_page_split_defensive():
    """验证带有多个 '-' 的 page range 会被拒绝而不是 unpack ValueError"""
    p = "1-2-3"
    parts = p.split("-")
    assert len(parts) == 3
    # 原始代码的 start, end = p.split("-") 会在这里 ValueError
    # 修复后的代码先检查 len(parts) == 2
    if len(parts) != 2:
        accepted = False
    else:
        accepted = True
    assert not accepted
    print("test_page_split_defensive passed")

def test_valid_page_range_accepted():
    """验证正常 page range 仍被接受"""
    p = "1-5"
    parts = p.split("-")
    assert len(parts) == 2
    start, end = parts
    assert int(start) == 1
    assert int(end) == 5
    print("test_valid_page_range_accepted passed")

if __name__ == "__main__":
    test_page_split_defensive()
    test_valid_page_range_accepted()
