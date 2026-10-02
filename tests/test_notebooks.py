import ast
import json
from pathlib import Path


def test_notebooks_do_not_expose_personal_paths():
    root = Path(__file__).resolve().parents[1]
    notebooks = root.joinpath("notebooks").glob("*.ipynb")
    forbidden = ("/content/drive", "MyDrive", "My Drive", "/home/")
    for notebook in notebooks:
        content = notebook.read_text(encoding="utf-8")
        assert not any(value in content for value in forbidden), notebook


def test_notebooks_use_current_data_layout():
    root = Path(__file__).resolve().parents[1]
    heatwave = root.joinpath("notebooks/heatwave_indexes.ipynb").read_text(encoding="utf-8")
    official = root.joinpath("notebooks/Oficial_25_11_25.ipynb").read_text(encoding="utf-8")
    paper = root.joinpath("notebooks/paper_19.08.2026.ipynb").read_text(encoding="utf-8")
    assert "return str(ERA5_MONTHLY_DIR" in heatwave
    assert "base_path = str(ERA5_CAPITALS_DIR)" in heatwave
    assert "Could not locate the project root" in heatwave
    assert "Could not locate the project root" in official
    assert "Could not locate the project root" in paper
    assert "displayName" not in heatwave
    assert "userId" not in heatwave
    assert "displayName" not in official
    assert "userId" not in official
    assert "displayName" not in paper
    assert "userId" not in paper
    assert "\nreturn str(ERA5_MONTHLY_DIR" not in heatwave
    assert "user.upper()" not in official
    assert "ROOT = Path(\n    \\\"DATA_DIR\\\"" not in paper
    assert "Indices_ondas_calor" not in paper


def test_notebook_code_cells_compile():
    root = Path(__file__).resolve().parents[1]
    for notebook in root.joinpath("notebooks").glob("*.ipynb"):
        document = json.loads(notebook.read_text(encoding="utf-8"))
        for index, cell in enumerate(document["cells"]):
            if cell.get("cell_type") != "code":
                continue
            source = "\n".join(
                line
                for line in "".join(cell.get("source", [])).splitlines()
                if not line.lstrip().startswith(("!", "%"))
            )
            try:
                ast.parse(source)
            except SyntaxError as error:
                raise AssertionError(f"{notebook} cell {index}: {error}") from error
