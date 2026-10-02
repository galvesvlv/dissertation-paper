"""Public command-line entry point for the dissertation data pipeline.

Use ``python pipeline.py --stage validate`` for a lightweight input check,
``python pipeline.py --stage audit`` to verify generated products, or
``python pipeline.py --stage analysis`` to execute statistical notebooks, or
``python pipeline.py --stage maps`` for the slower high-resolution maps.
Notebook execution is never part of the default validation stage.
"""

from src.main import main


if __name__ == "__main__":
    main()
