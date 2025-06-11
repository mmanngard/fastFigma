from dotenv import load_dotenv
import re
import requests
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


