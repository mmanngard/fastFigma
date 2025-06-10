# components/head.py
from fasthtml.common import Head, Script, Link

def get_head_component():
    return Head(
        # Tailwind CSS (with DaisyUI)
        Script(src="https://cdn.tailwindcss.com"),
        Link(
            rel="stylesheet",
            href="https://cdn.jsdelivr.net/npm/daisyui@5"
        ),
        # HTMX for dynamic partial updates
        Script(src="https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js")
)