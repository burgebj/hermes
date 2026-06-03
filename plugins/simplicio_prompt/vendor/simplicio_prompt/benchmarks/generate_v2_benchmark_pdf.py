"""Generate the V2 safe-speed benchmark PDF."""

from __future__ import annotations

import json
from pathlib import Path

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
IN_JSON = ROOT / "benchmarks" / "v2_safe_speed_results.json"
OUT = ROOT / "benchmarks" / "v2_safe_speed_benchmark.pdf"


def main() -> int:
    payload = json.loads(IN_JSON.read_text(encoding="utf-8"))
    results = payload["results"]
    comparisons = payload["comparisons"]

    styles = getSampleStyleSheet()
    title = styles["Title"]
    h2 = styles["Heading2"]
    body = styles["BodyText"]
    body.leading = 13
    small = ParagraphStyle("small", parent=body, fontSize=8.2, leading=10)

    doc = SimpleDocTemplate(
        str(OUT),
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
        title="Yool Safe-Speed Benchmark V2",
        author="wesleysimplicio/simplicio-prompt",
    )

    story = [
        Paragraph("Yool Safe-Speed Benchmark V2", title),
        _p(
            "Comparacao entre instrucao normal, V1 high-throughput e V2 safe-speed.<br/>"
            f"Run date: {payload['run_date']}<br/>"
            f"Python: {payload['environment']['python']}",
            body,
        ),
        Spacer(1, 0.2 * cm),
        Paragraph("Executive Summary", h2),
        _p(
            "A V2 mantem o ganho estrutural da V1 para escala massiva e adiciona "
            "controles seguros de velocidade: cache por input/receipt, LaneWorkerPool "
            "adaptativo, backoff com jitter, circuit breaker por provedor, batching, "
            "compressao de contexto, roteamento local e speculative execution apenas "
            "para tarefas idempotentes.",
            body,
        ),
        Spacer(1, 0.2 * cm),
        _bar_chart(
            "Speed gains (x)",
            _comparison_rows(
                comparisons,
                [
                    "scale_representation",
                    "active_execution",
                    "cache_dedupe",
                    "small_task_batching",
                ],
                metric="wall_ms",
            ),
        ),
        Spacer(1, 0.2 * cm),
        _bar_chart(
            "Provider/token reduction (x)",
            _comparison_rows(
                comparisons,
                [
                    "cache_dedupe",
                    "small_task_batching",
                    "provider_failure_control",
                    "context_compression",
                ],
                metrics={"provider_calls", "tokens"},
            ),
        ),
    ]

    for scenario, heading in [
        ("scale_representation", "Scale Representation"),
        ("active_execution", "Active Execution"),
        ("cache_dedupe", "Cache Dedupe"),
        ("small_task_batching", "Small Task Batching"),
        ("provider_failure_control", "Provider Failure Control"),
        ("context_compression", "Context Compression"),
    ]:
        story.extend([
            Spacer(1, 0.25 * cm),
            Paragraph(heading, h2),
            _result_table([item for item in results if item["scenario"] == scenario]),
        ])

    story.extend([
        Spacer(1, 0.25 * cm),
        Paragraph("Gains Table", h2),
        _comparison_table(comparisons),
        Spacer(1, 0.25 * cm),
        Paragraph("Interpretation", h2),
        _p(
            "V1 ja resolve escala com lazy batch_spawn. V2 melhora a velocidade "
            "real de entrega ao reduzir chamadas repetidas e overhead de orquestracao. "
            "O circuit breaker e o backoff sao importantes porque velocidade sem "
            "controle aumenta risco de rate limit ou bloqueio por provedor. A V2 "
            "acelera evitando trabalho, nao forçando chamadas infinitas.",
            body,
        ),
        Paragraph("Limitations", h2),
        _p(
            "Os numeros medem mecanica local. Provedores reais podem variar por "
            "rate limit, latencia, tamanho de contexto e politica de cache. Para "
            "trabalho CPU-bound puro em Python, subprocessos ou extensoes nativas "
            "ainda sao melhores que threads por causa do GIL.",
            small,
        ),
    ])

    doc.build(story)
    print(OUT)
    return 0


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), style)


def _result_table(rows: list[dict]) -> Table:
    table_data = [
        [
            "Profile",
            "Tasks",
            "Wall ms",
            "Throughput/s",
            "Calls",
            "Cache",
            "Blocked",
            "Tokens",
        ]
    ]
    for row in rows:
        table_data.append([
            row["profile"],
            f"{row['tasks']:,}",
            f"{row['wall_ms']:.2f}",
            f"{row['throughput_tasks_s']:.1f}",
            f"{row['provider_calls']:,}",
            f"{row['cache_hits']:,}",
            f"{row['blocked_calls']:,}",
            f"{row['tokens']:,}",
        ])
    table = Table(
        table_data,
        colWidths=[
            4.2 * cm,
            2.1 * cm,
            2.0 * cm,
            2.3 * cm,
            1.8 * cm,
            1.8 * cm,
            1.8 * cm,
            1.8 * cm,
        ],
    )
    table.setStyle(_table_style())
    return table


def _comparison_table(comparisons: list[dict]) -> Table:
    table_data = [["Scenario", "Baseline", "Improved", "Metric", "Ratio", "Gain"]]
    for item in comparisons:
        ratio = "n/a" if item["ratio"] is None else f"{item['ratio']:.2f}x"
        table_data.append([
            item["scenario"],
            item["baseline"],
            item["improved"],
            item["metric"],
            ratio,
            f"{item['percent']:.2f}%",
        ])
    table = Table(
        table_data,
        colWidths=[3.4 * cm, 3.5 * cm, 3.5 * cm, 2.4 * cm, 1.8 * cm, 2.0 * cm],
    )
    table.setStyle(_table_style())
    return table


def _comparison_rows(
    comparisons: list[dict],
    scenarios: list[str],
    *,
    metric: str | None = None,
    metrics: set[str] | None = None,
) -> list[tuple[str, float, colors.Color]]:
    rows = []
    palette = [
        colors.HexColor("#2B6CB0"),
        colors.HexColor("#38A169"),
        colors.HexColor("#DD6B20"),
        colors.HexColor("#805AD5"),
    ]
    for item in comparisons:
        if item["scenario"] not in scenarios:
            continue
        if metric is not None and item["metric"] != metric:
            continue
        if metrics is not None and item["metric"] not in metrics:
            continue
        if item["ratio"] is None:
            continue
        label = f"{item['scenario']} {item['metric']}"[:38]
        rows.append((label, float(item["ratio"]), palette[len(rows) % len(palette)]))
    return rows


def _bar_chart(title: str, rows: list[tuple[str, float, colors.Color]]) -> Drawing:
    width = 17 * cm
    row_h = 0.55 * cm
    height = 1.0 * cm + row_h * max(1, len(rows))
    drawing = Drawing(width, height)
    drawing.add(
        String(0, height - 0.35 * cm, title, fontName="Helvetica-Bold", fontSize=10)
    )
    if not rows:
        drawing.add(String(0, height - 0.85 * cm, "No comparable rows", fontSize=8))
        return drawing
    max_value = max(value for _label, value, _color in rows)
    label_w = 6.0 * cm
    bar_w = 8.6 * cm
    y = height - 0.85 * cm
    for label, value, color in rows:
        y -= row_h
        drawing.add(String(0, y + 0.12 * cm, label, fontSize=7.2))
        drawing.add(
            Rect(
                label_w,
                y,
                bar_w,
                0.25 * cm,
                fillColor=colors.HexColor("#E8EDF3"),
                strokeColor=None,
            )
        )
        filled = 0 if max_value <= 0 else min(bar_w, bar_w * value / max_value)
        drawing.add(
            Rect(label_w, y, filled, 0.25 * cm, fillColor=color, strokeColor=None)
        )
        drawing.add(
            String(
                label_w + bar_w + 0.2 * cm, y + 0.08 * cm, f"{value:.2f}x", fontSize=7.2
            )
        )
    return drawing


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#CAD3DF")),
        ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#F9FBFD")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


if __name__ == "__main__":
    raise SystemExit(main())
