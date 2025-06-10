from dotenv import load_dotenv
import os
import re
import requests
import json
from pydantic import BaseModel, computed_field

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

def figma_node_to_fasthtml(node: dict):
    """
    Recursively map a Figma node to a python-fasthtml element:
      - TEXT   → P(...)
      - VECTOR → Img(...)
      - FRAME  → Div(...)
      - others → Div(...)
    """
    node_type = node.get("type")
    name = node.get("name", "").strip()
    # build the 'cls' attribute only if there's a name
    kwargs = {"cls": name} if name else {}

    # first convert all children
    children = [figma_node_to_fasthtml(c) for c in node.get("children", [])]

    if node_type == "TEXT":
        # TEXT nodes: content is in 'characters'
        return P(node.get("characters", ""), **kwargs)

    if node_type == "VECTOR":
        # VECTOR nodes: render as <img>, with alt=name
        return Img(alt=name or None, **kwargs)

    # FRAME and any other type: render as <div>
    return Div(*children, **kwargs)
