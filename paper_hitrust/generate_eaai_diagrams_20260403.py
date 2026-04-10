#!/usr/bin/env python3
from __future__ import annotations

from html import escape
from pathlib import Path


OUT_DIR = Path(__file__).resolve().parent / "figures_eaai"
FONT = "Helvetica, Arial, sans-serif"

PALETTE = {
    "ink": "#32465a",
    "muted": "#6f8193",
    "line": "#7e91a6",
    "light_line": "#b8c7d5",
    "blue_fill": "#eaf3fb",
    "blue_fill_2": "#dfeefb",
    "teal_fill": "#e8f7f3",
    "green_fill": "#eef8ea",
    "orange_fill": "#fff3e0",
    "orange_line": "#d98a35",
    "red_fill": "#faecec",
    "red_line": "#d06565",
    "gray_fill": "#f5f7fa",
    "gray_fill_2": "#f0f3f7",
    "dark_blue": "#2b6ea6",
    "teal": "#3e8f87",
    "soft_green": "#6aa870",
}


class Svg:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.parts: list[str] = []

    def add(self, raw: str) -> None:
        self.parts.append(raw)

    def background(self) -> None:
        self.add(
            f'<rect x="0" y="0" width="{self.width}" height="{self.height}" fill="white" />'
        )

    def title(self, text: str, *, y: float = 36, size: int = 24) -> None:
        self.text(
            self.width / 2,
            y,
            text,
            size=size,
            weight=700,
            anchor="middle",
            fill=PALETTE["ink"],
        )

    def panel_tag(self, x: float, y: float, tag: str) -> None:
        self.round_rect(
            x,
            y,
            40,
            28,
            fill="white",
            stroke=PALETTE["light_line"],
            rx=10,
            stroke_width=1.6,
        )
        self.text(x + 20, y + 20, tag, size=17, weight=700, anchor="middle")

    def dashed_frame(self, x: float, y: float, w: float, h: float) -> None:
        self.round_rect(
            x,
            y,
            w,
            h,
            fill="white",
            stroke=PALETTE["light_line"],
            rx=24,
            stroke_width=1.6,
            dash="7 6",
        )

    def round_rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        fill: str,
        stroke: str,
        rx: float = 18,
        stroke_width: float = 1.8,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" ry="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr} />'
        )

    def line(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str,
        width: float = 1.8,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round"{dash_attr} />'
        )

    def arrow(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        *,
        stroke: str,
        width: float = 2.2,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
            f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" '
            f'marker-end="url(#arrow)"{dash_attr} />'
        )

    def polyline_arrow(
        self,
        points: list[tuple[float, float]],
        *,
        stroke: str,
        width: float = 2.2,
        dash: str | None = None,
    ) -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        coords = " ".join(f"{x},{y}" for x, y in points)
        self.add(
            f'<polyline points="{coords}" fill="none" stroke="{stroke}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" '
            f'marker-end="url(#arrow)"{dash_attr} />'
        )

    def text(
        self,
        x: float,
        y: float,
        text: str,
        *,
        size: int = 16,
        weight: int = 500,
        anchor: str = "start",
        fill: str = PALETTE["ink"],
    ) -> None:
        safe = escape(text)
        self.add(
            f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{safe}</text>'
        )

    def multiline(
        self,
        x: float,
        y: float,
        lines: list[str],
        *,
        size: int = 16,
        weight: int = 500,
        anchor: str = "start",
        fill: str = PALETTE["ink"],
        line_gap: int = 20,
    ) -> None:
        for idx, line in enumerate(lines):
            self.text(
                x,
                y + idx * line_gap,
                line,
                size=size,
                weight=weight,
                anchor=anchor,
                fill=fill,
            )

    def token(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        fill: str,
        stroke: str,
        label: str,
        tfill: str | None = None,
        size: int = 14,
    ) -> None:
        self.round_rect(x, y, w, h, fill=fill, stroke=stroke, rx=10, stroke_width=1.6)
        self.text(
            x + w / 2,
            y + h / 2 + 5,
            label,
            size=size,
            weight=600,
            anchor="middle",
            fill=tfill or PALETTE["ink"],
        )

    def stage_label(self, x: float, y: float, n: int, lines: list[str]) -> None:
        self.add(
            f'<circle cx="{x}" cy="{y}" r="15" fill="{PALETTE["orange_fill"]}" '
            f'stroke="{PALETTE["orange_line"]}" stroke-width="1.6" />'
        )
        self.text(
            x,
            y + 5,
            str(n),
            size=16,
            weight=700,
            anchor="middle",
            fill=PALETTE["orange_line"],
        )
        self.multiline(
            x + 24,
            y + 4,
            lines,
            size=15,
            weight=700,
            line_gap=18,
        )

    def defs(self) -> None:
        self.add(
            f"""
<defs>
  <marker id="arrow" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L10,5 L0,10 z" fill="{PALETTE['line']}" />
  </marker>
</defs>
"""
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        svg = [
            (
                f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" '
                f'height="{self.height}" viewBox="0 0 {self.width} {self.height}">'
            ),
        ]
        self.defs()
        svg.extend(self.parts)
        svg.append("</svg>")
        path.write_text("\n".join(svg), encoding="utf-8")


def small_graph(svg: Svg, x: float, y: float, color: str) -> None:
    nodes = [(x + 10, y + 18), (x + 42, y + 12), (x + 24, y + 40), (x + 56, y + 34)]
    edges = [(0, 1), (0, 2), (1, 2), (1, 3), (2, 3)]
    for a, b in edges:
        svg.line(nodes[a][0], nodes[a][1], nodes[b][0], nodes[b][1], stroke=color, width=1.5)
    for nx, ny in nodes:
        svg.add(
            f'<circle cx="{nx}" cy="{ny}" r="4.5" fill="white" stroke="{color}" stroke-width="1.6" />'
        )


def client_box(svg: Svg, x: float, y: float, title: str, *, poisoned: bool = False) -> None:
    fill = PALETTE["red_fill"] if poisoned else PALETTE["blue_fill"]
    stroke = PALETTE["red_line"] if poisoned else PALETTE["dark_blue"]
    svg.round_rect(x, y, 172, 78, fill=fill, stroke=stroke, rx=16)
    small_graph(svg, x + 14, y + 14, stroke)
    svg.text(x + 104, y + 25, title, size=15, weight=700, anchor="middle")
    svg.text(x + 104, y + 47, "GraphSAGE", size=13, weight=600, anchor="middle", fill=PALETTE["muted"])
    svg.text(x + 104, y + 65, "local update", size=13, weight=500, anchor="middle", fill=PALETTE["muted"])
    if poisoned:
        svg.add(f'<circle cx="{x + 156}" cy="{y + 15}" r="6" fill="{PALETTE["red_line"]}" />')


def group_box(
    svg: Svg,
    x: float,
    y: float,
    label: str,
    members: list[tuple[str, str, str]],
    *,
    w: float = 150,
    h: float = 112,
) -> None:
    svg.round_rect(x, y, w, h, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=18)
    svg.text(x + 14, y + 24, label, size=17, weight=700)
    for idx, (member, fill, stroke) in enumerate(members):
        tx = x + 14 + (idx % 2) * 66
        ty = y + 40 + (idx // 2) * 34
        svg.token(tx, ty, 52, 24, fill=fill, stroke=stroke, label=member, size=12)
    svg.round_rect(
        x + 20,
        y + h - 32,
        w - 40,
        24,
        fill=PALETTE["teal_fill"],
        stroke=PALETTE["teal"],
        rx=10,
        stroke_width=1.4,
    )
    svg.text(
        x + w / 2,
        y + h - 15,
        "group agg",
        size=12,
        weight=700,
        anchor="middle",
        fill=PALETTE["teal"],
    )


def make_fig1() -> Path:
    svg = Svg(1500, 760)
    svg.background()
    svg.title("HiTrust-FedBot framework", y=34, size=23)
    svg.dashed_frame(26, 60, 1448, 650)

    svg.stage_label(86, 96, 1, ["Local", "clients"])
    svg.stage_label(346, 96, 2, ["Upload", "tuple"])
    svg.stage_label(558, 96, 3, ["Trust", "screening"])
    svg.stage_label(930, 96, 4, ["Coverage-aware", "grouping"])
    svg.stage_label(1270, 96, 5, ["Global", "update"])

    svg.round_rect(52, 132, 218, 506, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=22)
    svg.text(161, 160, "Edge clients", size=20, weight=700, anchor="middle")
    client_box(svg, 74, 186, "Client 1")
    client_box(svg, 74, 276, "Client 2", poisoned=True)
    client_box(svg, 74, 366, "Client 3")
    client_box(svg, 74, 456, "Client 4", poisoned=True)
    svg.multiline(
        161,
        570,
        ["non-IID traffic", "graph partitions"],
        size=15,
        weight=500,
        anchor="middle",
        fill=PALETTE["muted"],
        line_gap=18,
    )

    svg.round_rect(320, 252, 152, 150, fill=PALETTE["orange_fill"], stroke=PALETTE["orange_line"], rx=20)
    svg.text(396, 282, "Client upload", size=18, weight=700, anchor="middle", fill=PALETTE["orange_line"])
    svg.token(338, 304, 116, 26, fill="white", stroke=PALETTE["orange_line"], label="model update", size=12)
    svg.token(338, 338, 116, 26, fill="white", stroke=PALETTE["orange_line"], label="val. signal", size=12)
    svg.token(338, 372, 116, 26, fill="white", stroke=PALETTE["orange_line"], label="behavior sum.", size=12)
    svg.arrow(270, 334, 320, 334, stroke=PALETTE["line"])

    svg.round_rect(516, 168, 316, 300, fill=PALETTE["blue_fill"], stroke=PALETTE["dark_blue"], rx=22)
    svg.text(674, 198, "Server trust analysis", size=20, weight=700, anchor="middle")
    svg.round_rect(546, 226, 256, 44, fill="white", stroke=PALETTE["light_line"], rx=14)
    svg.round_rect(546, 282, 256, 44, fill="white", stroke=PALETTE["light_line"], rx=14)
    svg.round_rect(546, 338, 256, 56, fill="white", stroke=PALETTE["light_line"], rx=14)
    svg.text(674, 254, "trust scoring", size=17, weight=700, anchor="middle")
    svg.text(674, 310, "semantic group assignment", size=17, weight=700, anchor="middle")
    svg.multiline(674, 361, ["poison-aware", "retention decision"], size=17, weight=700, anchor="middle", line_gap=18)
    svg.token(548, 416, 76, 24, fill=PALETTE["gray_fill_2"], stroke=PALETTE["light_line"], label="val. F1", tfill=PALETTE["muted"], size=12)
    svg.token(636, 416, 76, 24, fill=PALETTE["gray_fill_2"], stroke=PALETTE["light_line"], label="sim.", tfill=PALETTE["muted"], size=12)
    svg.token(724, 416, 76, 24, fill=PALETTE["gray_fill_2"], stroke=PALETTE["light_line"], label="history", tfill=PALETTE["muted"], size=12)
    svg.arrow(472, 334, 516, 334, stroke=PALETTE["line"])

    svg.round_rect(882, 148, 340, 420, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=22)
    svg.text(1052, 178, "Coverage-safe semantic groups", size=20, weight=700, anchor="middle")
    group_box(
        svg,
        904,
        212,
        "Group A",
        [
            ("u1", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u2", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u7", PALETTE["gray_fill"], PALETTE["light_line"]),
        ],
    )
    group_box(
        svg,
        1068,
        212,
        "Group B",
        [
            ("u3", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u4", PALETTE["red_fill"], PALETTE["red_line"]),
            ("u8", PALETTE["gray_fill"], PALETTE["light_line"]),
        ],
    )
    group_box(
        svg,
        986,
        352,
        "Group C",
        [
            ("u5", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u6", PALETTE["blue_fill"], PALETTE["dark_blue"]),
        ],
        w=152,
        h=108,
    )
    svg.round_rect(930, 494, 244, 42, fill=PALETTE["green_fill"], stroke=PALETTE["soft_green"], rx=14)
    svg.text(1052, 521, "minimum group coverage", size=15, weight=700, anchor="middle", fill=PALETTE["soft_green"])
    svg.arrow(832, 334, 882, 334, stroke=PALETTE["line"])

    svg.round_rect(1264, 224, 176, 88, fill=PALETTE["teal_fill"], stroke=PALETTE["teal"], rx=20)
    svg.multiline(1352, 252, ["Global model", "aggregation"], size=19, weight=700, anchor="middle", fill=PALETTE["teal"], line_gap=19)
    svg.round_rect(1264, 334, 176, 176, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=20)
    svg.text(1352, 360, "Deployment outputs", size=18, weight=700, anchor="middle")
    svg.token(1290, 380, 124, 24, fill="white", stroke=PALETTE["light_line"], label="F1", size=13)
    svg.token(1290, 414, 124, 24, fill="white", stroke=PALETTE["light_line"], label="FPR", size=13)
    svg.token(1290, 448, 124, 24, fill="white", stroke=PALETTE["light_line"], label="retained poison", size=13)
    svg.token(1290, 482, 124, 24, fill="white", stroke=PALETTE["light_line"], label="retained clients", size=13)

    svg.polyline_arrow([(1054, 322), (1200, 322), (1264, 268)], stroke=PALETTE["line"])
    svg.polyline_arrow([(1054, 460), (1200, 460), (1264, 278)], stroke=PALETTE["line"])
    svg.polyline_arrow([(1440, 268), (1456, 268), (1456, 664), (160, 664), (160, 638)], stroke=PALETTE["line"], dash="7 6")
    svg.text(1000, 688, "broadcast next-round global model", size=13, weight=500, anchor="middle", fill=PALETTE["muted"])

    out = OUT_DIR / "fig1_overall_hitrust_framework.svg"
    svg.save(out)
    return out


def make_fig2() -> Path:
    svg = Svg(1450, 620)
    svg.background()
    svg.title("Evaluation and validation workflow", y=34, size=23)
    svg.dashed_frame(28, 58, 1394, 530)

    svg.round_rect(56, 116, 332, 156, fill=PALETTE["blue_fill"], stroke=PALETTE["dark_blue"], rx=22)
    svg.text(222, 146, "Internal topology-aware pilots", size=19, weight=700, anchor="middle")
    for idx, label in enumerate(["scenario_d", "scenario_e", "scenario_f", "scenario_g", "scenario_h"]):
        xx = 84 + (idx % 3) * 100
        yy = 176 + (idx // 3) * 44
        svg.token(xx, yy, 82, 26, fill="white", stroke=PALETTE["dark_blue"], label=label, size=11)
    svg.multiline(
        222,
        248,
        ["topology stress tests", "and group-collapse probes"],
        size=12,
        weight=500,
        anchor="middle",
        fill=PALETTE["muted"],
        line_gap=15,
    )

    svg.round_rect(430, 104, 432, 172, fill=PALETTE["teal_fill"], stroke=PALETTE["teal"], rx=22)
    svg.text(646, 140, "Same-task public validation", size=20, weight=700, anchor="middle", fill=PALETTE["teal"])
    svg.round_rect(482, 176, 138, 72, fill="white", stroke=PALETTE["teal"], rx=16)
    svg.round_rect(672, 176, 138, 72, fill="white", stroke=PALETTE["teal"], rx=16)
    svg.multiline(551, 204, ["Ca-Bench", "scenario_e"], size=18, weight=700, anchor="middle", line_gap=18)
    svg.multiline(741, 204, ["Ca-Bench", "scenario_h"], size=18, weight=700, anchor="middle", line_gap=18)
    svg.round_rect(534, 246, 224, 24, fill=PALETTE["green_fill"], stroke=PALETTE["soft_green"], rx=10, stroke_width=1.4)
    svg.text(646, 263, "primary external evidence", size=12, weight=700, anchor="middle", fill=PALETTE["soft_green"])

    svg.round_rect(912, 126, 450, 132, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=22)
    svg.text(1137, 156, "Auxiliary public transfer", size=19, weight=700, anchor="middle")
    svg.round_rect(1006, 184, 262, 50, fill="white", stroke=PALETTE["light_line"], rx=16)
    svg.multiline(1137, 205, ["NSL-KDD graph-converted", "transfer context"], size=17, weight=700, anchor="middle", line_gap=18)

    svg.round_rect(132, 338, 458, 124, fill=PALETTE["orange_fill"], stroke=PALETTE["orange_line"], rx=22)
    svg.text(174, 368, "Attack regimes", size=19, weight=700, fill=PALETTE["orange_line"])
    svg.token(164, 392, 172, 28, fill="white", stroke=PALETTE["orange_line"], label="sign-flip@0.4", size=12)
    svg.token(350, 392, 196, 28, fill="white", stroke=PALETTE["orange_line"], label="update-noise@0.4", size=12)
    svg.token(164, 426, 172, 28, fill="white", stroke=PALETTE["orange_line"], label="benign-mimic@0.4", size=12)
    svg.token(350, 426, 196, 28, fill="white", stroke=PALETTE["orange_line"], label="ALIE-like@0.4", size=12)

    svg.round_rect(640, 324, 324, 148, fill=PALETTE["blue_fill_2"], stroke=PALETTE["dark_blue"], rx=22)
    svg.text(802, 356, "Matched public paired tests", size=19, weight=700, anchor="middle", fill=PALETTE["dark_blue"])
    svg.token(684, 386, 236, 26, fill="white", stroke=PALETTE["dark_blue"], label="paired confidence intervals", size=12)
    svg.token(684, 420, 236, 26, fill="white", stroke=PALETTE["dark_blue"], label="paired sign tests", size=12)
    svg.token(684, 454, 236, 26, fill="white", stroke=PALETTE["dark_blue"], label="paired t-tests", size=12)

    svg.round_rect(1010, 320, 304, 158, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=22)
    svg.text(1162, 350, "Deployment evidence", size=19, weight=700, anchor="middle")
    svg.token(1052, 378, 220, 24, fill="white", stroke=PALETTE["light_line"], label="F1", size=12)
    svg.token(1052, 410, 220, 24, fill="white", stroke=PALETTE["light_line"], label="FPR", size=12)
    svg.token(1052, 442, 220, 24, fill="white", stroke=PALETTE["light_line"], label="retained poisoned clients", size=12)
    svg.token(1052, 474, 220, 24, fill="white", stroke=PALETTE["light_line"], label="retained clients", size=12)

    svg.arrow(222, 272, 222, 338, stroke=PALETTE["line"])
    svg.arrow(646, 276, 646, 324, stroke=PALETTE["line"])
    svg.arrow(1137, 258, 1137, 320, stroke=PALETTE["line"])
    svg.arrow(590, 400, 640, 400, stroke=PALETTE["line"])
    svg.arrow(964, 400, 1010, 400, stroke=PALETTE["line"])

    out = OUT_DIR / "fig2_evaluation_validation_workflow.svg"
    svg.save(out)
    return out


def make_fig3() -> Path:
    svg = Svg(1480, 620)
    svg.background()
    svg.title("Trust-aware hierarchical aggregation and coverage filtering", y=34, size=23)
    svg.dashed_frame(28, 58, 1424, 530)

    svg.round_rect(50, 132, 178, 404, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=22)
    svg.text(139, 160, "Client updates", size=20, weight=700, anchor="middle")
    for idx in range(8):
        yy = 188 + idx * 38
        fill = PALETTE["red_fill"] if idx in {2, 5} else PALETTE["blue_fill"]
        stroke = PALETTE["red_line"] if idx in {2, 5} else PALETTE["dark_blue"]
        svg.token(86, yy, 106, 24, fill=fill, stroke=stroke, label=f"u{idx + 1}", size=12)
        svg.arrow(192, yy + 12, 270, yy + 12, stroke=PALETTE["line"])

    svg.round_rect(270, 132, 238, 404, fill=PALETTE["blue_fill"], stroke=PALETTE["dark_blue"], rx=22)
    svg.text(389, 160, "Trust estimation", size=20, weight=700, anchor="middle")
    svg.token(310, 206, 158, 28, fill="white", stroke=PALETTE["light_line"], label="validation quality", size=12)
    svg.token(310, 246, 158, 28, fill="white", stroke=PALETTE["light_line"], label="update similarity", size=12)
    svg.token(310, 286, 158, 28, fill="white", stroke=PALETTE["light_line"], label="historical stability", size=12)
    svg.round_rect(310, 360, 158, 88, fill=PALETTE["teal_fill"], stroke=PALETTE["teal"], rx=18)
    svg.multiline(389, 394, ["trust", "normalization"], size=19, weight=700, anchor="middle", fill=PALETTE["teal"], line_gap=18)
    svg.text(389, 486, "normalized trust scores", size=14, weight=500, anchor="middle", fill=PALETTE["muted"])
    svg.arrow(508, 404, 550, 404, stroke=PALETTE["line"])

    svg.round_rect(550, 132, 216, 404, fill=PALETTE["orange_fill"], stroke=PALETTE["orange_line"], rx=22)
    svg.text(658, 160, "Retention decision", size=20, weight=700, anchor="middle", fill=PALETTE["orange_line"])
    svg.round_rect(600, 206, 116, 98, fill="white", stroke=PALETTE["orange_line"], rx=18)
    svg.multiline(658, 238, ["keep if", "score > tau"], size=18, weight=700, anchor="middle", line_gap=18)
    svg.text(658, 344, "retained", size=15, weight=700, anchor="middle")
    svg.token(610, 364, 96, 24, fill=PALETTE["blue_fill"], stroke=PALETTE["dark_blue"], label="u1  u2", size=12)
    svg.token(610, 396, 96, 24, fill=PALETTE["blue_fill"], stroke=PALETTE["dark_blue"], label="u3  u5", size=12)
    svg.text(658, 462, "rejected", size=15, weight=700, anchor="middle", fill=PALETTE["muted"])
    svg.token(610, 480, 96, 24, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], label="u7", size=12, tfill=PALETTE["muted"])
    svg.token(610, 512, 96, 24, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], label="u8", size=12, tfill=PALETTE["muted"])

    svg.round_rect(810, 132, 422, 404, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=22)
    svg.text(1021, 160, "Semantic grouping", size=20, weight=700, anchor="middle")
    group_box(
        svg,
        834,
        198,
        "Group A",
        [
            ("u1", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u2", PALETTE["blue_fill"], PALETTE["dark_blue"]),
        ],
        w=154,
        h=112,
    )
    group_box(
        svg,
        1000,
        198,
        "Group B",
        [
            ("u3", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u4", PALETTE["red_fill"], PALETTE["red_line"]),
        ],
        w=154,
        h=112,
    )
    group_box(
        svg,
        918,
        334,
        "Group C",
        [
            ("u5", PALETTE["blue_fill"], PALETTE["dark_blue"]),
            ("u6", PALETTE["blue_fill"], PALETTE["dark_blue"]),
        ],
        w=154,
        h=110,
    )
    svg.round_rect(1098, 364, 104, 64, fill=PALETTE["green_fill"], stroke=PALETTE["soft_green"], rx=16)
    svg.multiline(1150, 390, ["coverage", "rule"], size=18, weight=700, anchor="middle", fill=PALETTE["soft_green"], line_gap=18)
    svg.arrow(766, 404, 810, 404, stroke=PALETTE["line"])

    svg.round_rect(1266, 236, 160, 170, fill=PALETTE["teal_fill"], stroke=PALETTE["teal"], rx=20)
    svg.multiline(1346, 266, ["Global", "aggregate"], size=20, weight=700, anchor="middle", fill=PALETTE["teal"], line_gap=19)
    svg.token(1290, 308, 112, 24, fill="white", stroke=PALETTE["teal"], label="Group A agg", size=12)
    svg.token(1290, 340, 112, 24, fill="white", stroke=PALETTE["teal"], label="Group B agg", size=12)
    svg.token(1290, 372, 112, 24, fill="white", stroke=PALETTE["teal"], label="coverage-safe", size=12)
    svg.polyline_arrow([(988, 288), (1234, 288), (1266, 320)], stroke=PALETTE["line"])
    svg.polyline_arrow([(1154, 288), (1234, 288), (1266, 352)], stroke=PALETTE["line"])
    svg.polyline_arrow([(1072, 430), (1216, 430), (1266, 384)], stroke=PALETTE["line"])

    out = OUT_DIR / "fig3_trust_hierarchical_aggregation.svg"
    svg.save(out)
    return out


def make_fig4() -> Path:
    svg = Svg(1500, 670)
    svg.background()
    svg.title("Hardening mechanisms for challenging attack regimes", y=34, size=23)

    svg.panel_tag(56, 96, "(a)")
    svg.panel_tag(770, 96, "(b)")

    svg.round_rect(38, 118, 674, 500, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=24)
    svg.text(375, 150, "Condfloor for small-group collapse", size=20, weight=700, anchor="middle")
    svg.round_rect(84, 198, 232, 152, fill=PALETTE["orange_fill"], stroke=PALETTE["orange_line"], rx=20)
    svg.text(200, 226, "Static floor", size=18, weight=700, anchor="middle", fill=PALETTE["orange_line"])
    svg.round_rect(116, 252, 168, 64, fill="white", stroke=PALETTE["orange_line"], rx=16)
    svg.multiline(200, 278, ["one low-trust client", "is still forced to stay"], size=15, weight=700, anchor="middle", line_gap=17)
    svg.token(148, 324, 104, 24, fill=PALETTE["red_fill"], stroke=PALETTE["red_line"], label="poison kept", size=12)

    svg.round_rect(392, 176, 258, 236, fill=PALETTE["teal_fill"], stroke=PALETTE["teal"], rx=22)
    svg.text(521, 206, "Condfloor gate", size=18, weight=700, anchor="middle", fill=PALETTE["teal"])
    svg.round_rect(434, 244, 174, 72, fill="white", stroke=PALETTE["teal"], rx=16)
    svg.multiline(521, 272, ["if total trust mass", "falls below threshold"], size=16, weight=700, anchor="middle", line_gap=18)
    svg.round_rect(456, 334, 130, 48, fill="white", stroke=PALETTE["teal"], rx=14)
    svg.multiline(521, 355, ["skip floor", "repair"], size=16, weight=700, anchor="middle", line_gap=16)

    svg.round_rect(154, 446, 398, 108, fill=PALETTE["green_fill"], stroke=PALETTE["soft_green"], rx=20)
    svg.multiline(
        353,
        482,
        ["abstain from the compromised", "group instead of retaining one proxy"],
        size=19,
        weight=700,
        anchor="middle",
        fill=PALETTE["soft_green"],
        line_gap=20,
    )

    svg.arrow(316, 274, 392, 274, stroke=PALETTE["line"])
    svg.arrow(521, 316, 521, 334, stroke=PALETTE["line"])
    svg.arrow(521, 382, 521, 446, stroke=PALETTE["line"])

    svg.round_rect(752, 118, 710, 500, fill=PALETTE["gray_fill"], stroke=PALETTE["light_line"], rx=24)
    svg.text(1107, 150, "Temporal RootGuard for adaptive camouflage", size=20, weight=700, anchor="middle")
    svg.round_rect(794, 198, 246, 126, fill=PALETTE["blue_fill"], stroke=PALETTE["dark_blue"], rx=20)
    svg.text(917, 226, "Multi-round history", size=18, weight=700, anchor="middle")
    svg.token(820, 272, 60, 24, fill="white", stroke=PALETTE["dark_blue"], label="t-2", size=12)
    svg.token(887, 272, 60, 24, fill="white", stroke=PALETTE["dark_blue"], label="t-1", size=12)
    svg.token(954, 272, 60, 24, fill="white", stroke=PALETTE["dark_blue"], label="t", size=12)

    svg.round_rect(1088, 176, 312, 216, fill=PALETTE["blue_fill_2"], stroke=PALETTE["dark_blue"], rx=22)
    svg.text(1244, 206, "Temporal trust analysis", size=18, weight=700, anchor="middle", fill=PALETTE["dark_blue"])
    svg.token(1128, 236, 232, 24, fill="white", stroke=PALETTE["light_line"], label="trust smoothing", size=12)
    svg.token(1128, 270, 232, 24, fill="white", stroke=PALETTE["light_line"], label="server-root anchor", size=12)
    svg.token(1128, 304, 232, 24, fill="white", stroke=PALETTE["light_line"], label="drift penalty", size=12)
    svg.token(1128, 338, 232, 24, fill="white", stroke=PALETTE["light_line"], label="peer redundancy penalty", size=12)

    svg.round_rect(860, 430, 492, 124, fill=PALETTE["teal_fill"], stroke=PALETTE["teal"], rx=20)
    svg.text(1106, 458, "Weighted keep / reject decision", size=19, weight=700, anchor="middle", fill=PALETTE["teal"])
    for idx, xx in enumerate([910, 996, 1082, 1168]):
        fill = PALETTE["red_fill"] if idx in {1, 2} else PALETTE["blue_fill"]
        stroke = PALETTE["red_line"] if idx in {1, 2} else PALETTE["dark_blue"]
        svg.token(xx, 484, 68, 24, fill=fill, stroke=stroke, label=f"u{idx + 1}", size=12)
    svg.multiline(
        1106,
        522,
        ["camouflaged cluster is down-weighted", "after temporal, anchor, and redundancy checks"],
        size=12,
        weight=500,
        anchor="middle",
        fill=PALETTE["muted"],
        line_gap=14,
    )

    svg.arrow(1040, 261, 1088, 261, stroke=PALETTE["line"])
    svg.arrow(1244, 392, 1244, 430, stroke=PALETTE["line"])
    svg.polyline_arrow([(917, 296), (917, 430)], stroke=PALETTE["line"], dash="7 6")

    out = OUT_DIR / "fig4_hardening_failure_regimes.svg"
    svg.save(out)
    return out


def main() -> None:
    outputs = [make_fig1(), make_fig2(), make_fig3(), make_fig4()]
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
