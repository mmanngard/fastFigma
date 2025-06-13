# export.py
import inspect
from typing import Any, Dict, List, Union, Optional
from pydantic import BaseModel
from fasthtml.common import Div, P, Img, Safe
from fastFigma.schema import FrameNode, TextNode, VectorNode, Effect
from fastFigma.api import resolve_value
import json
import urllib.parse

Node = Union[Dict[str, Any], FrameNode, TextNode, VectorNode]

# ─── Helper to map a single Effect → Tailwind utilities ───────

def effect_to_tailwind(e: Effect) -> List[str]:
    cls: List[str] = []
    if e.type in ("DROP_SHADOW", "INNER_SHADOW") and e.offset and e.radius and e.color:
        x = int(e.offset["x"])
        y = int(e.offset["y"])
        r = int(e.radius)
        c = e.color
        rgba = f"rgba({int(c.r*255)},{int(c.g*255)},{int(c.b*255)},{c.a})"

        # Drop shadows use the drop-shadow utility
        if e.type == "DROP_SHADOW":
            cls.append(f"drop-shadow-[{x}px_{y}px_{r}px_{rgba}]")

        # Inner shadows combine `shadow-inner` with a shadow offset
        elif e.type == "INNER_SHADOW":
            # Tailwind has `shadow-inner`, but to mimic the same blur/offset we can chain an arbitrary drop-shadow
            cls.append("shadow-inner")
            cls.append(f"drop-shadow-[{x}px_{y}px_{r}px_{rgba}]")
    return cls

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

    # Effects (drop/inner shadows)
    "effects": lambda effs, m=None: [
        cls for e in effs or [] for cls in effect_to_tailwind(e)
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
    "effects": lambda effs, m=None: [
        cls for e in effs or [] for cls in effect_to_tailwind(e)
    ],
}

VECTOR_TW_MAP: Dict[str, Union[Dict[Any, List[str]], Any]] = {
    "absoluteBoundingBox": FRAME_TW_MAP["absoluteBoundingBox"],
    # Vectors don’t get borders by default—map only size & fills if needed
    "fills": FRAME_TW_MAP.get("strokes", lambda _: []),  # if you want fill‐as‐bg
    "effects": lambda effs, m=None: [
        cls for e in effs or [] for cls in effect_to_tailwind(e)
    ],
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
            # inspect mapper signature
            sig = inspect.signature(mapper)
            if len(sig.parameters) == 1:
                cls += mapper(val)
            else:
                cls += mapper(val, m)

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
    return FrameNode.model_validate(node)

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
        text = m.characters or ""

        if m.name and m.name.strip().startswith("$api"):
            # Try to parse JSON payload
            try:
                config = json.loads(m.name.replace("$api", "", 1).strip())
                src = config.get("src")
                path = config.get("path")
                trigger = config.get("trigger", "once")

                print(f"!!!!! {src}")

                # Build HTMX attributes
                encoded_src = urllib.parse.quote(src, safe='')
                attrs["hx-get"] = f"/api/value?src={encoded_src}&path={path}"
                attrs["hx-swap"] = "innerHTML"
                attrs["hx-trigger"] = "load" if trigger == "once" else "every 1s"

                # Placeholder value until HTMX replaces it
                text = "..."

            except Exception as e:
                print(f"⚠️ Invalid $api config in {m.name}: {e}")
                text = "?"

        return P(text, **attrs)

    if isinstance(m, VectorNode):
        svg = svg_map.get(m.id, "") if svg_map else ""
        if svg.strip().startswith("<svg"):
            return Div(Safe(svg), **attrs)
        else:
            return Img(src=svg, alt=m.name or "", **attrs)

    children = [figma_to_fasthtml(c, svg_map) for c in (m.children or [])]
    return Div(*children, **attrs)

def figma_to_fasthtml(
    node: Node,
    svg_map: Optional[Dict[str, str]] = None
):
    model = node if isinstance(node, BaseModel) else parse_node(node)
    return render_node(model, svg_map)
