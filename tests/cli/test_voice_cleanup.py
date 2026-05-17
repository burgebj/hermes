import ast
from pathlib import Path


def test_voice_stop_and_transcribe_has_no_return_in_finally():
    cli_path = Path(__file__).resolve().parents[2] / "cli.py"
    tree = ast.parse(cli_path.read_text(encoding="utf-8"))

    class Finder(ast.NodeVisitor):
        def __init__(self):
            self.in_target = False
            self.returns_in_finally = 0

        def visit_FunctionDef(self, node):
            was_target = self.in_target
            if node.name == "_voice_stop_and_transcribe":
                self.in_target = True
                self.generic_visit(node)
                self.in_target = was_target
                return
            self.generic_visit(node)

        def visit_Try(self, node):
            if self.in_target:
                for stmt in node.finalbody:
                    for child in ast.walk(stmt):
                        if isinstance(child, ast.Return):
                            self.returns_in_finally += 1
            self.generic_visit(node)

    finder = Finder()
    finder.visit(tree)

    assert finder.returns_in_finally == 0
