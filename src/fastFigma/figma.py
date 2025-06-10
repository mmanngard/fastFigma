from dotenv import load_dotenv
import os
import re
import requests
import json
from pydantic import BaseModel, computed_field
from typing import Dict
from fasthtml.common import Div, P, Img

class FigmaProject(BaseModel):
    url: str
    api_token: str

    def _extract(self) -> tuple[str, str]:
        pattern = r"https?://www\.figma\.com/(?:file|design)/([A-Za-z0-9]+)/([^?]+)"
        match = re.search(pattern, self.url)
        if not match:
            raise ValueError(f"Invalid Figma URL format: {self.url!r}")
        return match.group(1), match.group(2)

    @computed_field
    def file_key(self) -> str:
        return self._extract()[0]

    @computed_field
    def filename(self) -> str:
        return self._extract()[1]

    def get_project_json(self) -> dict:
        headers = {
            "X-Figma-Token": self.api_token
        }
        api_url = f"https://api.figma.com/v1/files/{self.file_key}"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raises an error for non-200 responses
        return response.json()
    
    def get_ui_elements(self) -> list[dict]:
        """
        Recursively find all nodes in the Figma file whose names start with '$ui'.
        """
        def find_ui_nodes(node: dict) -> list[dict]:
            matches = []
            if 'name' in node and isinstance(node['name'], str) and node['name'].startswith('$ui'):
                matches.append(node)
            for child in node.get('children', []):
                matches.extend(find_ui_nodes(child))
            return matches

        data = self.get_project_json()
        document = data.get("document", {})
        return find_ui_nodes(document)


#
_PRIMARY_MAP = {
    "MIN":           "flex-start",
    "MAX":           "flex-end",
    "CENTER":        "center",
    "SPACE_BETWEEN": "space-between",
}
_COUNTER_MAP = {
    "MIN":    "flex-start",
    "MAX":    "flex-end",
    "CENTER": "center",
}

def _rgba_from_paint(paint: dict) -> str:
    c = paint["color"]
    r, g, b = int(c["r"]*255), int(c["g"]*255), int(c["b"]*255)
    a = c.get("a", 1.0)
    return f"rgba({r},{g},{b},{a})" if a < 1 else f"rgb({r},{g},{b})"

def _extract_flex_styles(node: dict) -> Dict[str, str]:
    styles: Dict[str, str] = {}
    lm = node.get("layoutMode")
    if lm in ("HORIZONTAL", "VERTICAL"):
        styles["display"]        = "flex"
        styles["flex-direction"] = "row" if lm == "HORIZONTAL" else "column"
        pa = node.get("primaryAxisAlignItems")
        if pa in _PRIMARY_MAP:
            styles["justify-content"] = _PRIMARY_MAP[pa]
        ca = node.get("counterAxisAlignItems")
        if ca in _COUNTER_MAP:
            styles["align-items"]      = _COUNTER_MAP[ca]
        if gap := node.get("itemSpacing"):
            styles["gap"] = f"{gap}px"
        pt, pr = node.get("paddingTop",0), node.get("paddingRight",0)
        pb, pl = node.get("paddingBottom",0), node.get("paddingLeft",0)
        styles["padding"] = f"{pt}px {pr}px {pb}px {pl}px"
    return styles

def _extract_fill_stroke_styles(node: dict) -> Dict[str,str]:
    styles: Dict[str,str] = {}
    if node.get("type") != "TEXT":
        # Background color
        for paint in node.get("fills", []):
            if paint.get("type") == "SOLID":
                styles["background-color"] = _rgba_from_paint(paint)
                break
        # Border
        strokes = node.get("strokes", [])
        weight  = node.get("strokeWeight", 0)
        if strokes and weight > 0:
            first = strokes[0]
            if first.get("type") == "SOLID":
                styles["border"] = f"{weight}px solid {_rgba_from_paint(first)}"
    return styles

def _extract_text_styles(node: dict) -> Dict[str, str]:
    styles: Dict[str, str] = {}
    s = node.get("style", {})
    if fam := s.get("fontFamily"):    styles["font-family"]    = fam
    if size:= s.get("fontSize"):      styles["font-size"]      = f"{size}px"
    if weight:=s.get("fontWeight"):   styles["font-weight"]    = str(weight)
    if lh:=    s.get("lineHeightPx"): styles["line-height"]    = f"{lh}px"
    if ls:=    s.get("letterSpacing"):styles["letter-spacing"] = f"{ls}px"
    for paint in node.get("fills", []):  # TEXT uses fills as text color
        if paint.get("type") == "SOLID":
            styles["color"] = _rgba_from_paint(paint)
            break
    return styles

def _extract_size_styles(node: dict) -> Dict[str,str]:
    styles: Dict[str,str] = {}
    if box := node.get("absoluteBoundingBox"):
        if w := box.get("width"):
            styles["width"]  = f"{w}px"
        if h := box.get("height"):
            styles["height"] = f"{h}px"
    return styles

def _extract_border_radius(node: dict) -> Dict[str,str]:
    styles: Dict[str,str] = {}
    # Uniform radius
    if cr := node.get("cornerRadius"):
        styles["border-radius"] = f"{cr}px"
    # Per-corner radii
    elif radii := node.get("rectangleCornerRadii"):
        # Figma order: top-left, top-right, bottom-right, bottom-left
        vals = [f"{r}px" for r in radii]
        styles["border-radius"] = " ".join(vals)
    return styles

def figma_node_to_fasthtml(node: dict):
    """
    Recursively map a Figma node to a python-fasthtml element,
    capturing layout, fills, strokes, typography, size, and corner radius.
    """
    ntype = node.get("type")
    name  = node.get("name", "").strip()

    # 1) Gather all style bits
    styles: Dict[str,str] = {}
    if ntype == "FRAME":
        styles.update(_extract_flex_styles(node))
    styles.update(_extract_fill_stroke_styles(node))
    if ntype == "TEXT":
        styles.update(_extract_text_styles(node))
    styles.update(_extract_size_styles(node))
    styles.update(_extract_border_radius(node))

    # 2) Build attrs dict
    attrs: Dict[str,str] = {}
    if name:
        attrs["cls"] = name
    if styles:
        attrs["style"] = "; ".join(f"{k}:{v}" for k,v in styles.items())

    # 3) Recurse children
    children = [figma_node_to_fasthtml(c) for c in node.get("children", [])]

    # 4) Return the appropriate tag
    if ntype == "TEXT":
        return P(node.get("characters", ""), **attrs)
    if ntype == "VECTOR":
        return Img(alt=name or None, **attrs)
    return Div(*children, **attrs)