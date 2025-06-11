# export.py

from typing import Any, Dict, List, Union, Optional
from pydantic import BaseModel
from fasthtml.common import Div, P, Img
from fastFigma.schema import FrameNode, TextNode, VectorNode

Node = Union[Dict[str, Any], FrameNode, TextNode, VectorNode]

# ─── Declarative Tailwind maps ──────────────────────────────

FRAME_TW_MAP: Dict[str, Union[Dict[Any, List[str]], Any]] = {
    "layoutMode": {
        "HORIZONTAL": ["flex", "flex-row"],
        "VERTICAL":   ["flex", "flex-col"],
    },
    "primaryAxisAlignItems": {
        "MIN":           ["justify-start"],
        "CENTER":        ["justify-center"],
        "MAX":           ["justify-end"],
        "SPACE_BETWEEN": ["justify-between"],
    },
    "counterAxisAlignItems": {
        "MIN":    ["items-start"],
        "CENTER": ["items-center"],
        "MAX":    ["items-end"],
    },

    "itemSpacing":   lambda v: [f"gap-[{int(v)}px]"],
    "paddingTop":    lambda v: [f"pt-[{int(v)}px]"],
    "paddingRight":  lambda v: [f"pr-[{int(v)}px]"],
    "paddingBottom": lambda v: [f"pb-[{int(v)}px]"],
    "paddingLeft":   lambda v: [f"pl-[{int(v)}px]"],

    "cornerRadius": lambda v: [f"rounded-[{int(v)}px]"],

    "absoluteBoundingBox": lambda b: [
        f"w-[{int(b.width)}px]", f"h-[{int(b.height)}px]"
    ],

    # Background color from fills
    "fills": lambda paints, m=None: [
        f"bg-[rgba({int(p.color.r*255)},"
        f"{int(p.color.g*255)},{int(p.color.b*255)},{p.color.a})]"
        for p in paints or []
        if p.type == "SOLID" and p.color
    ],

    # Borders: only by strokeWeight (checked against strokes non-empty)
    "strokeWeight": lambda w, m: (
        ["border", f"border-[{int(w)}px]"] if w and w > 0 and (m.strokes or [])
        else []
    ),
    "strokes": lambda paints, m=None: [
        f"border-[rgba({int(p.color.r*255)},"
        f"{int(p.color.g*255)},{int(p.color.b*255)},{p.color.a})]"
        for p in paints or []
        if p.type == "SOLID" and p.color
    ],
}

TEXT_TW_MAP: Dict[str, Union[Dict[Any, List[str]], Any]] = {
    "style": lambda s: (
        [] if not s else
        # font‐size
        ([f"text-[{int(s.fontSize)}px]"] if s.fontSize else []) +
        # font‐weight
        (["font-bold"] if s.fontWeight and s.fontWeight >= 700 else
         ["font-medium"] if s.fontWeight and s.fontWeight >= 500 else []) +
        # line‐height
        ([f"leading-[{int(s.lineHeightPx)}px]"] if s.lineHeightPx else []) +
        # letter‐spacing
        ([f"tracking-[{int(s.letterSpacing)}px]"] if s.letterSpacing else []) +
        # text‐align
        ([f"text-{s.textAlignHorizontal.lower()}"] if s.textAlignHorizontal else [])
    ),
    "fills": lambda paints: [
        f"text-[rgba({int(p.color.r*255)},{int(p.color.g*255)},{int(p.color.b*255)},{p.color.a})]"
        for p in paints or []
        if p.type == "SOLID" and p.color
    ],
}

VECTOR_TW_MAP: Dict[str, Union[Dict[Any, List[str]], Any]] = {
    "absoluteBoundingBox": FRAME_TW_MAP["absoluteBoundingBox"],
    # Vectors don’t get borders by default—map only size & fills if needed
    "fills": FRAME_TW_MAP.get("strokes", lambda _: []),  # if you want fill‐as‐bg
}
# ─── Generic helpers ────────────────────────────────────────
def tw_from_map(
    m: Union[FrameNode, TextNode, VectorNode],
    mapping: Dict[str, Union[Dict[Any, List[str]], Any]]
) -> List[str]:
    cls: List[str] = []
    for field, mapper in mapping.items():
        val = getattr(m, field, None)
        if val is None or (isinstance(val, list) and not val):
            continue

        if isinstance(mapper, dict):
            cls += mapper.get(val, [])
        else:
            # call either with (val, m) or just (val)
            try:
                cls += mapper(val, m)
            except TypeError:
                cls += mapper(val)

    if m.name:
        cls.append(m.name)
    return cls

# ─── Parsing & Rendering ─────────────────────────────────────
def parse_node(node: Node) -> Union[FrameNode, TextNode, VectorNode]:
    if isinstance(node, BaseModel):
        return node
    t = node.get("type")
    if t == "FRAME":
        return FrameNode.model_validate(node)
    if t == "TEXT":
        return TextNode.model_validate(node)
    if t == "VECTOR":
        return VectorNode.model_validate(node)
    return FrameNode.model_validate(node)  # fallback

def render_node(
    m: Union[FrameNode, TextNode, VectorNode],
    svg_map: Optional[Dict[str, str]] = None
):
    if isinstance(m, FrameNode):
        tw = tw_from_map(m, FRAME_TW_MAP)
    elif isinstance(m, TextNode):
        tw = tw_from_map(m, TEXT_TW_MAP)
    else:
        tw = tw_from_map(m, VECTOR_TW_MAP)

    attrs: Dict[str, Any] = {}
    if tw:
        attrs["cls"] = " ".join(tw)

    if isinstance(m, TextNode):
        return P(m.characters or "", **attrs)

    if isinstance(m, VectorNode):
        src = svg_map.get(m.id, "") if svg_map else ""
        return Img(src=src, alt=m.name or "", **attrs)

    # Frame fallback
    children = [figma_to_fasthtml(c, svg_map) for c in (m.children or [])]
    return Div(*children, **attrs)

def figma_to_fasthtml(
    node: Node,
    svg_map: Optional[Dict[str, str]] = None
):
    """
    Parse and render a Figma node into a Tailwind‐styled FastHTML element.
    """
    model = parse_node(node)
    return render_node(model, svg_map)
