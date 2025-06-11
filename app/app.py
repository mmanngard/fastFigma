import os
from dotenv import load_dotenv
from fasthtml.common import fast_app, Html, Body, Div
from .components.head import get_head_component
from fastFigma.project import FigmaProject
from fastFigma.export import figma_to_fasthtml

load_dotenv()

public_path = os.path.join(os.path.dirname(__file__), "public")

FIGMA_API_TOKEN = os.getenv("FIGMA_API_TOKEN")
URL = "https://www.figma.com/design/4zPVSizRrtpANhJoTejFYu/fastFigma?t=9rwh0m4vsoX3GeMw-1"

project = FigmaProject(url=URL, api_token=FIGMA_API_TOKEN)
ui_elements = project.get_ui_elements()

# fastHTML app
app, rt = fast_app(
    static_path=public_path,
    live=True
    )

@rt("/")
def home():
    widgets = [figma_to_fasthtml(node) for node in ui_elements]

    return Html(
        get_head_component(),
        Body(
            Div(*widgets, cls="figma-widgets-container")
        )
    )