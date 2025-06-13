import re
import requests
from functools import cached_property
from pydantic import BaseModel, computed_field


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

    @cached_property
    def project_json(self) -> dict:
        headers = {"X-Figma-Token": self.api_token}
        api_url = f"https://api.figma.com/v1/files/{self.file_key}"
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()

    @cached_property
    def ui_elements(self) -> list[dict]:
        """Recursively find all nodes whose names start with '$ui'."""
        def find_ui_nodes(node: dict) -> list[dict]:
            matches = []
            if isinstance(node.get("name"), str) and node["name"].startswith("$ui"):
                matches.append(node)
            for child in node.get("children", []):
                matches.extend(find_ui_nodes(child))
            return matches

        document = self.project_json.get("document", {})
        return find_ui_nodes(document)

    @cached_property
    def vector_nodes(self) -> list[dict]:
        """Recursively find all VECTOR nodes within ui_elements."""
        def collect_vectors(nodes: list[dict]) -> list[dict]:
            vectors = []
            for node in nodes:
                if node.get("type") == "VECTOR":
                    vectors.append(node)
                vectors.extend(collect_vectors(node.get("children", [])))
            return vectors

        return collect_vectors(self.ui_elements)

    @cached_property
    def svg_map(self) -> dict[str, str]:
        """Map VECTOR node IDs to raw SVG markup."""
        svg_map = {}
        for node in self.vector_nodes:
            try:
                svg_map[node["id"]] = self.get_svg_markup(node["id"])
            except Exception as e:
                print(f"⚠️ Could not fetch SVG for node {node['id']}: {e}")
        return svg_map

    def get_svg_markup(self, node_id: str) -> str:
        """Retrieve raw SVG markup for a vector node by ID."""
        headers = {"X-Figma-Token": self.api_token}
        url = f"https://api.figma.com/v1/images/{self.file_key}?ids={node_id}&format=svg"
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        image_url = resp.json()["images"].get(node_id)

        if not image_url:
            raise ValueError(f"No SVG URL returned for node_id {node_id}")

        svg_resp = requests.get(image_url)
        svg_resp.raise_for_status()
        return svg_resp.text
