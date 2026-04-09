"""
Converts data/batches.yaml + data/tiles.yaml → data/data.js
Run: python build-data.py
"""
import json, yaml, pathlib

root = pathlib.Path(__file__).parent
batches = yaml.safe_load((root / "data/batches.yaml").read_text(encoding="utf-8"))
tiles   = yaml.safe_load((root / "data/tiles.yaml").read_text(encoding="utf-8"))

# Dates must be strings (YAML parses them as date objects)
for b in batches:
    if hasattr(b.get("date"), "isoformat"):
        b["date"] = b["date"].isoformat()

out = f"// Auto-generated from batches.yaml + tiles.yaml\n// Edit the YAML files, then run: python build-data.py\nwindow.SITE_DATA = {json.dumps({'batches': batches, 'tiles': tiles}, indent=2, ensure_ascii=False)};\n"
(root / "data/data.js").write_text(out, encoding="utf-8")
print("data/data.js updated.")
