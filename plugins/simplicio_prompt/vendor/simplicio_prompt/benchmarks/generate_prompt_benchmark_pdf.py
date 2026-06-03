"""Generate the prompt benchmark PDF report.

Run with the bundled Codex Python when available:

    python benchmarks/generate_prompt_benchmark_pdf.py

The script uses ReportLab if installed. It intentionally keeps the benchmark
figures in source control so the PDF can be regenerated exactly.
"""

from __future__ import annotations

from pathlib import Path
import sys

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from benchmarks.prompt_vs_normal import token_model  # noqa: E402

OUT = ROOT / "benchmarks" / "prompt_vs_normal_benchmark.pdf"

PROMPT = """Use o repo canonico https://github.com/wesleysimplicio/simplicio-prompt.
Leia antes de editar: YOOL_TUPLE_HAMT.md, kernel/yool_tuple_kernel.py,
guardrails/cpu_throttle.py, guardrails/disk_gc.py, examples/python/receipts.py
e scripts/build_hamt.py.

Ao receber qualquer prompt ou mensagem X, sem exigir "Implement X": decomponha em grafo Hilbert-indexed, crie tuple raiz,
use batch_spawn(depth, branching, compression_threshold) para 1.000.000+
subagents sem enumerar, execute work ativo com spawn_agent, roteie por out/in/rd,
route_packet e scan_index, aplique hookwall, compress_token e prune_idle, e use
LaneWorkerPool respeitando YOOL_TUPLE_* env vars.

Execute:
python kernel/yool_tuple_kernel.py

Responda SEMPRE exatamente neste formato (sem variações):
[Tuple Space Snapshot]
[Active Agents/Subagents]
[Total Agents/Subagents]
[Próximo Yool a executar]
[Resultado parcial]"""


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def main() -> int:
    styles = getSampleStyleSheet()
    title = styles["Title"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    body.leading = 13
    small = ParagraphStyle("small", parent=body, fontSize=8.5, leading=10.5)
    code = ParagraphStyle(
        "code",
        parent=small,
        fontName="Courier",
        backColor=colors.HexColor("#F4F6F8"),
        borderColor=colors.HexColor("#D7DEE8"),
        borderWidth=0.5,
        borderPadding=6,
        leading=9.5,
    )

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="Yool Prompt Benchmark",
        author="wesleysimplicio/simplicio-prompt",
    )

    story = [
        Paragraph("Yool Prompt vs Normal Instruction Benchmark", title),
        p(
            "Repository: wesleysimplicio/simplicio-prompt<br/>Run date: 2026-05-21",
            body,
        ),
        Spacer(1, 0.25 * cm),
        Paragraph("Executive Summary", h2),
        p(
            "The Yool prompt is faster because it turns a generic instruction into an "
            "execution protocol: lazy batch_spawn for scale, tuple-space routing, "
            "LaneWorkerPool fan-out, receipts, hookwall checks, and explicit runtime "
            "guardrails. The benchmark measured local runtime mechanics, not hosted LLM "
            "provider behavior.",
            body,
        ),
    ]

    story.extend([
        Spacer(1, 0.2 * cm),
        _bar_chart(
            "Speedup (x)",
            [
                ("Scale 131k vs 1M", 1397.0, colors.HexColor("#2B6CB0")),
                ("Scale 262k vs 1M", 5902.0, colors.HexColor("#2B6CB0")),
                ("Active 256 tasks", 6.37, colors.HexColor("#38A169")),
                ("Active 512 tasks", 9.31, colors.HexColor("#38A169")),
            ],
            max_value=5902.0,
        ),
    ])

    scale_table = Table(
        [
            ["Profile", "Represented agents", "Wall time", "Peak memory"],
            ["Normal instruction, flat list", "131,072", "217.11 ms", "28,749.88 KiB"],
            ["Yool prompt, lazy batch_spawn", "1,048,576", "0.16 ms", "6.32 KiB"],
            ["Observed gain", "8x more agents", "1,397x faster", "4,547x less memory"],
        ],
        colWidths=[6.1 * cm, 3.8 * cm, 3.1 * cm, 4.1 * cm],
    )
    scale_table.setStyle(_table_style())
    story.extend([
        Spacer(1, 0.2 * cm),
        Paragraph("Scale Representation", h2),
        scale_table,
    ])

    larger_scale_table = Table(
        [
            ["Profile", "Represented agents", "Wall time", "Peak memory"],
            ["Normal instruction, flat list", "262,144", "431.45 ms", "57,542.32 KiB"],
            ["Yool prompt, lazy batch_spawn", "1,048,576", "0.07 ms", "6.39 KiB"],
            ["Observed gain", "4x more agents", "5,902x faster", "9,000x less memory"],
        ],
        colWidths=[6.1 * cm, 3.8 * cm, 3.1 * cm, 4.1 * cm],
    )
    larger_scale_table.setStyle(_table_style())
    story.extend([Spacer(1, 0.25 * cm), larger_scale_table])

    story.extend([
        Spacer(1, 0.25 * cm),
        _bar_chart(
            "Peak memory reduction for scale representation (x)",
            [
                ("131k flat vs 1M lazy", 4547.0, colors.HexColor("#805AD5")),
                ("262k flat vs 1M lazy", 9000.0, colors.HexColor("#805AD5")),
            ],
            max_value=9000.0,
        ),
    ])

    exec_table = Table(
        [
            ["Profile", "Tasks", "Wall time", "Throughput", "Peak memory"],
            ["Normal sequential", "256", "603.98 ms", "423.9 tasks/s", "17.33 KiB"],
            ["Yool lane fan-out", "256", "94.87 ms", "2,698.3 tasks/s", "879.82 KiB"],
            [
                "Observed gain",
                "same",
                "6.37x faster",
                "6.37x higher",
                "higher active overhead",
            ],
        ],
        colWidths=[5.0 * cm, 2.0 * cm, 3.0 * cm, 3.6 * cm, 3.7 * cm],
    )
    exec_table.setStyle(_table_style())
    story.extend([Spacer(1, 0.35 * cm), Paragraph("Active Execution", h2), exec_table])

    exec_big_table = Table(
        [
            ["Profile", "Tasks", "Wall time", "Throughput", "Peak memory"],
            ["Normal sequential", "512", "1,212.88 ms", "422.1 tasks/s", "33.55 KiB"],
            [
                "Yool lane fan-out",
                "512",
                "130.28 ms",
                "3,929.9 tasks/s",
                "1,739.41 KiB",
            ],
            [
                "Observed gain",
                "same",
                "9.31x faster",
                "9.31x higher",
                "higher active overhead",
            ],
        ],
        colWidths=[5.0 * cm, 2.0 * cm, 3.0 * cm, 3.6 * cm, 3.7 * cm],
    )
    exec_big_table.setStyle(_table_style())
    story.extend([Spacer(1, 0.25 * cm), exec_big_table])

    token_rows = token_model()
    token_table_data = [
        ["Scenario", "Normal tokens", "Yool tokens", "Savings", "Savings %"]
    ]
    token_chart_rows = []
    for item in token_rows:
        token_table_data.append([
            item.scenario,
            f"{item.normal_tokens:,}",
            f"{item.yool_tokens:,}",
            f"{item.savings_tokens:,}",
            f"{item.savings_pct:.2f}%",
        ])
        if item.savings_pct > 0:
            token_chart_rows.append((
                item.scenario.replace("_", " "),
                item.savings_pct,
                colors.HexColor("#DD6B20"),
            ))
    token_table = Table(
        token_table_data,
        colWidths=[5.2 * cm, 3.0 * cm, 3.0 * cm, 3.0 * cm, 2.4 * cm],
    )
    token_table.setStyle(_table_style())
    story.extend([
        Spacer(1, 0.35 * cm),
        Paragraph("Token Usage and Estimated Savings", h2),
        p(
            "Token numbers are deterministic local estimates using ceil(UTF-8 bytes / 4). "
            "They are not provider billing measurements. The model compares repeated "
            "chat-context orchestration against one prompt plus compact tuple envelopes.",
            body,
        ),
        token_table,
        Spacer(1, 0.2 * cm),
        _bar_chart("Estimated token savings (%)", token_chart_rows, max_value=100.0),
        p(
            "One-off bootstrap is intentionally more expensive with the Yool prompt, "
            "because it carries the execution protocol. Savings appear when work fans out: "
            "the protocol is paid once and subtasks travel as compact tuple envelopes.",
            body,
        ),
    ])

    story.extend([
        Spacer(1, 0.35 * cm),
        Paragraph("Gains Beyond Speed", h2),
        p(
            "Scalability: million-agent trees without flat lists.<br/>"
            "Auditability: tuple state plus receipts.<br/>"
            "Recovery: pending work can be replayed from tuple state.<br/>"
            "Failure isolation: lanes separate planning, build, test, review, and runtime work.<br/>"
            "Guardrails: CPU, queue, compression, hookwall, and disk GC are named controls.<br/>"
            "Portability: the same prompt points Claude, Codex, Hermes, and scripts at the same files.",
            body,
        ),
        Paragraph("Tradeoffs", h2),
        p(
            "For small active workloads, the Yool prompt uses more memory because it "
            "creates tuple envelopes and worker fan-out structures. It pays off when work "
            "is I/O-bound, uses subprocesses, browser automation, APIs, hosted LLM calls, "
            "or large-scale planning/execution.",
            body,
        ),
        Paragraph("Prompt Used", h2),
        p(PROMPT, code),
        Paragraph("Reproduce", h2),
        p(
            "python benchmarks/prompt_vs_normal.py --json<br/>"
            "python benchmarks/prompt_vs_normal.py --tasks 512 --scale-agents 262144 --sleep-ms 2 --json<br/>"
            "python benchmarks/generate_prompt_benchmark_pdf.py",
            code,
        ),
    ])

    doc.build(story)
    print(OUT)
    return 0


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD3DF")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FBFD")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#EAF5EF")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])


def _bar_chart(
    title: str, rows: list[tuple[str, float, colors.Color]], max_value: float
) -> Drawing:
    width = 17 * cm
    row_h = 0.55 * cm
    height = 1.0 * cm + row_h * len(rows)
    drawing = Drawing(width, height)
    drawing.add(
        String(0, height - 0.35 * cm, title, fontName="Helvetica-Bold", fontSize=10)
    )
    label_w = 5.4 * cm
    bar_w = 9.0 * cm
    x = label_w
    y = height - 0.85 * cm
    for label, value, color in rows:
        y -= row_h
        drawing.add(String(0, y + 0.12 * cm, label[:34], fontSize=7.5))
        drawing.add(
            Rect(
                x,
                y,
                bar_w,
                0.25 * cm,
                fillColor=colors.HexColor("#E8EDF3"),
                strokeColor=None,
            )
        )
        filled = (
            0 if max_value <= 0 else max(0.0, min(bar_w, bar_w * value / max_value))
        )
        drawing.add(Rect(x, y, filled, 0.25 * cm, fillColor=color, strokeColor=None))
        drawing.add(
            String(x + bar_w + 0.25 * cm, y + 0.08 * cm, f"{value:,.2f}", fontSize=7.5)
        )
    return drawing


if __name__ == "__main__":
    raise SystemExit(main())
