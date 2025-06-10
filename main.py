from fastFigma.figma import FigmaProject
from dotenv import load_dotenv
import os

load_dotenv()

FIGMA_API_TOKEN = os.getenv("FIGMA_API_TOKEN")

URL = "https://www.figma.com/design/4zPVSizRrtpANhJoTejFYu/fastFigma?t=9rwh0m4vsoX3GeMw-1"

project = FigmaProject(url=URL, api_token=FIGMA_API_TOKEN)

def main():
    print(project.filename)

if __name__ == "__main__":
    main()
