import os
from dotenv import load_dotenv
from fasthtml.common import fast_app, Html, Body, Div, P
from .components.head import get_head_component
from fastFigma.project import FigmaProject
from fastFigma.export import figma_to_fasthtml
from fastFigma.api import resolve_value

load_dotenv()

def collect_vector_nodes(nodes: list[dict]) -> list[dict]:
    vectors = []
    for node in nodes:
        if node.get("type") == "VECTOR":
            vectors.append(node)
        children = node.get("children", [])
        if children:
            vectors.extend(collect_vector_nodes(children))
    return vectors


public_path = os.path.join(os.path.dirname(__file__), "public")

FIGMA_API_TOKEN = os.getenv("FIGMA_API_TOKEN")
URL = "https://www.figma.com/design/4zPVSizRrtpANhJoTejFYu/fastFigma?t=9rwh0m4vsoX3GeMw-1"

project = FigmaProject(url=URL, api_token=FIGMA_API_TOKEN)

# fastHTML app
app, rt = fast_app(
    static_path=public_path,
    live=True
    )

@rt("/")
def home():
    widgets = [figma_to_fasthtml(node, svg_map=project.svg_map) for node in project.ui_elements]

    return Html(
        get_head_component(),
        Body(
            Div(*widgets, cls="figma-widgets-container flex flex-col space-y-4 p-8")
        )
    )

@rt("/api/value")
def get_value(src: str = "", path: str = ""):
    if not src or not path:
        return "?"
    from fastFigma.api import resolve_value
    return resolve_value({"src": src, "path": path})
