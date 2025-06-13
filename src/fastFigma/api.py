import requests

def resolve_value(binding: str) -> str:
    """
    Resolves a Figma text binding like:
    $api@https://example.com/data#some.nested.value
    """
    if not binding.startswith("$api@"):
        return binding

    try:
        _, rest = binding.split("@", 1)
        url, _, path = rest.partition("#")

        # Step 1: Fetch data from API
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()

        # Step 2: Traverse the dot-path
        for key in path.strip("/").split("."):
            data = data.get(key)
            if data is None:
                return "?"
        return str(data)

    except Exception as e:
        print(f"⚠️ Error resolving API value for {binding}: {e}")
        return "?"