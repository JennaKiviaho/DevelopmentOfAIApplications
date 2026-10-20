from app.ui import build_ui
from pathlib import Path

def main() -> None:
    """Entry point script for launching the application."""
    demo = build_ui()
    css_path = Path(__file__).with_name("styles.css")
    demo.launch(css=css_path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
