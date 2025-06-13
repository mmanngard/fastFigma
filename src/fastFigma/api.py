import requests
import json
import re
from typing import Union
from typing import Dict

def resolve_value(binding: Dict[str, str]) -> str:
    try:
        src = binding.get("src")
        path = binding.get("path")

        if not src or not path:
            print("⚠️ Missing 'src' or 'path' in binding")
            return "?"

        response = requests.get(src)
        response.raise_for_status()
        data = response.json()

        for key in path.split("."):
            if not isinstance(data, dict) or key not in data:
                print(f"⚠️ Path key not found: {key}")
                return "?"
            data = data[key]

        return str(data)

    except Exception as e:
        print(f"⚠️ Error resolving API value: {e}")
        return "?"
