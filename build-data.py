"""
Reads source from data/ and src/, writes built site to _site/.
Run: python build-data.py
"""
import json, re, shutil, yaml, pathlib, html as html_lib
from collections import defaultdict
from datetime import datetime, timezone

SITE_URL   = "https://tiletest.com"
SITE_NAME  = "Pottery Test Tile Archive"
PHOTO_BASE = "https://pub-fadb8321999f444193651a63bba5967e.r2.dev/"

root    = pathlib.Path(__file__).parent
src_dir = root / "src"
out_dir = root / "_site"

# ── Load source data ──────────────────────────────────────────────────────────
batches = yaml.safe_load((root / "data/batches.yaml").read_text(encoding="utf-8"))
glazes  = yaml.safe_load((root / "data/glazes.yaml").read_text(encoding="utf-8"))

tiles = []
for path in sorted((root / "data/tiles").glob("*.yaml")):
    tiles.extend(yaml.safe_load(path.read_text(encoding="utf-8")))

for b in batches:
    if hasattr(b.get("date"), "isoformat"):
        b["date"] = b["date"].isoformat()

# ── Set up output directory ───────────────────────────────────────────────────
if out_dir.exists():
    shutil.rmtree(out_dir)
out_dir.mkdir()

# Copy static source assets
shutil.copytree(src_dir / "js", out_dir / "js")
print("js/ copied.")

# ── data.js ───────────────────────────────────────────────────────────────────
data_js = (
    "// Auto-generated from batches.yaml + tiles.yaml + glazes.yaml\n"
    "// Edit the YAML files, then run: python build-data.py\n"
    f"window.SITE_DATA = {json.dumps({'batches': batches, 'tiles': tiles, 'glazes': glazes}, indent=2, ensure_ascii=False)};\n"
)
(out_dir / "data").mkdir()
(out_dir / "data" / "data.js").write_text(data_js, encoding="utf-8")
print("data/data.js written.")

# ── index.html (with cache-bust version) ─────────────────────────────────────
version  = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
html_src = (src_dir / "index.html").read_text(encoding="utf-8")
html_src = re.sub(
    r'(<script src="./data/data\.js)(?:\?v=[^"]*)?(")',
    rf'\1?v={version}\2',
    html_src,
)
(out_dir / "index.html").write_text(html_src, encoding="utf-8")
print(f"index.html written (v={version}).")

# ── CNAME ─────────────────────────────────────────────────────────────────────
shutil.copy(root / "CNAME", out_dir / "CNAME")

# ── Helpers ───────────────────────────────────────────────────────────────────

def h(s):
    return html_lib.escape(str(s)) if s is not None else ""

def cone_str(c):
    if isinstance(c, list):
        parts = [cone_str(x) for x in c]
        return f"{parts[0]}–{parts[-1]}" if len(parts) > 1 else parts[0]
    return f"0{abs(c)}" if isinstance(c, int) and c < 0 else str(c)

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", str(s).lower()).strip("-")

batch_map = {b["id"]: b for b in batches}
glaze_map = {g["id"]: g for g in glazes}

def merge_tile(tile):
    batch = batch_map.get(tile["batch"], {})
    merged_tags = list({*(batch.get("tags") or []), *(tile.get("tags") or [])})
    resolved = []
    for gid in (tile.get("glaze_combo") or []):
        g = glaze_map.get(gid, {"id": gid, "name": gid})
        resolved.append(g)
    merged = {**batch, **tile, "tags": merged_tags, "resolvedGlazes": resolved}
    if hasattr(merged.get("date"), "isoformat"):
        merged["date"] = merged["date"].isoformat()
    return merged

merged_tiles = [merge_tile(t) for t in tiles]

# Index: glaze id → tiles that include it
tiles_by_glaze = defaultdict(list)
for mt in merged_tiles:
    for g in mt["resolvedGlazes"]:
        tiles_by_glaze[g["id"]].append(mt)

# Index: brand → product_line → [glaze]  (only glazes with fired tiles)
glaze_tile_count = {g["id"]: len(tiles_by_glaze[g["id"]]) for g in glazes}
brands_index = {}
for glaze in glazes:
    if glaze_tile_count.get(glaze["id"], 0) == 0:
        continue
    brand = glaze.get("brand", "Unknown")
    pl    = glaze.get("product_line", "Unknown")
    brands_index.setdefault(brand, {}).setdefault(pl, []).append(glaze)

# ── HTML page template ────────────────────────────────────────────────────────

def page_html(title, description, canonical, breadcrumbs, body):
    bc_items = [
        f'{{"@type":"ListItem","position":{i+1},"name":{json.dumps(name)},"item":{json.dumps(SITE_URL + url)}}}'
        for i, (name, url) in enumerate(breadcrumbs)
    ]
    bc_ld = '{{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{}]}}'.format(
        ",".join(bc_items)
    )
    bc_nav_parts = []
    for i, (name, url) in enumerate(breadcrumbs):
        if i < len(breadcrumbs) - 1:
            bc_nav_parts.append(f'<a href="{h(url)}" class="hover:text-stone-700">{h(name)}</a>')
        else:
            bc_nav_parts.append(f'<span class="text-stone-700">{h(name)}</span>')
    bc_nav = ' <span class="mx-1">›</span> '.join(bc_nav_parts)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{h(title)}</title>
  <meta name="description" content="{h(description)}" />
  <link rel="canonical" href="{SITE_URL}{h(canonical)}" />
  <script src="https://cdn.tailwindcss.com"></script>
  <script type="application/ld+json">{bc_ld}</script>
</head>
<body class="bg-stone-100 text-stone-800 min-h-screen">

  <header class="bg-stone-800 text-stone-100 px-6 py-4">
    <a href="/" class="text-2xl font-semibold tracking-wide hover:text-stone-300">{h(SITE_NAME)}</a>
    <p class="text-stone-400 text-sm mt-1">A personal reference and public resource for glaze testing</p>
  </header>

  <nav class="bg-stone-700 text-stone-300 px-6 py-2 flex flex-wrap gap-x-4 gap-y-1 text-sm">
    <span class="text-stone-500 text-xs uppercase tracking-wide self-center mr-1">Browse by brand:</span>
    {"".join(f'<a href="/brand/{slugify(brand)}/" class="hover:text-white">{h(brand)}</a>' for brand in sorted(brands_index.keys()))}
  </nav>

  <main class="max-w-7xl mx-auto px-4 py-8 flex flex-col gap-6">
    <nav class="text-sm text-stone-400">{bc_nav}</nav>
    {body}
  </main>

  <footer class="max-w-7xl mx-auto px-4 py-6 border-t border-stone-200 text-sm text-stone-400">
    <a href="/" class="hover:text-stone-600">← All tiles</a>
  </footer>

</body>
</html>"""

# ── Tile card ─────────────────────────────────────────────────────────────────

def tile_card(mt, highlight_id=None):
    glaze_parts = []
    for i, g in enumerate(mt["resolvedGlazes"]):
        gid   = g["id"]
        gname = f"{g.get('brand','')} {g.get('name', gid)}".strip()
        label = ""
        if len(mt["resolvedGlazes"]) > 1:
            label = f' <span class="text-stone-400 text-xs">{"base" if i == 0 else "over"}</span>'
        weight = 'class="font-semibold"' if gid == highlight_id else ""
        glaze_parts.append(f'<a href="/glazes/{h(gid)}/" {weight}>{h(gname)}</a>{label}')
    glaze_html = " / ".join(glaze_parts)

    photo_url = PHOTO_BASE + mt.get("photo", "")
    alt = (
        " + ".join(g.get("name", g["id"]) for g in mt["resolvedGlazes"])
        + f" on {mt.get('clay_body','')} cone {mt.get('cone','')} {mt.get('atmosphere','')}"
    )

    return f"""<div class="bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow">
  <div class="aspect-square bg-stone-200 overflow-hidden">
    <img src="{h(photo_url)}" alt="{h(alt)}" loading="lazy" class="w-full h-full object-cover" />
  </div>
  <div class="p-3 flex flex-col gap-1 text-sm">
    <p class="text-xs font-mono text-stone-400">{h(mt.get('id',''))}</p>
    <p class="leading-snug">{glaze_html}</p>
    <p class="text-stone-500 text-xs">{h(mt.get('clay_body',''))}</p>
    <p class="text-stone-400 text-xs">Cone {h(str(mt.get('cone','')))} · {h(mt.get('atmosphere',''))} · {h(str(mt.get('date','')[:7] if mt.get('date') else ''))}</p>
  </div>
</div>"""

# ── Per-glaze pages ───────────────────────────────────────────────────────────
pages_written = 0

for glaze in glazes:
    gid       = glaze["id"]
    tile_list = tiles_by_glaze.get(gid, [])
    if not tile_list:
        continue

    brand  = glaze.get("brand", "Unknown")
    pl     = glaze.get("product_line", "")
    name   = glaze.get("name", gid)
    sku    = glaze.get("sku", "")
    finish = glaze.get("finish", "")
    color  = glaze.get("color", "")
    bslug  = slugify(brand)
    plslug = slugify(pl)

    rows = []
    if sku:    rows.append(f"<dt class='text-stone-500'>SKU</dt><dd>{h(sku)}</dd>")
    if pl:     rows.append(f"<dt class='text-stone-500'>Line</dt><dd>{h(pl)}</dd>")
    if finish: rows.append(f"<dt class='text-stone-500'>Finish</dt><dd class='capitalize'>{h(finish)}</dd>")
    if color:  rows.append(f"<dt class='text-stone-500'>Color</dt><dd class='capitalize'>{h(color)}</dd>")
    cone_range = glaze.get("cone")
    if cone_range is not None:
        rows.append(f"<dt class='text-stone-500'>Cone range</dt><dd>{h(cone_str(cone_range))}</dd>")
    dl = f'<dl class="grid grid-cols-2 gap-x-8 gap-y-1 text-sm mt-3">{"".join(rows)}</dl>' if rows else ""

    cones = sorted({str(mt.get("cone","")) for mt in tile_list if mt.get("cone") is not None})
    atmos = sorted({mt.get("atmosphere","") for mt in tile_list if mt.get("atmosphere")})
    clays = sorted({mt.get("clay_body","") for mt in tile_list if mt.get("clay_body")})
    n     = len(tile_list)
    cards = "\n".join(tile_card(mt, highlight_id=gid) for mt in tile_list)

    body = f"""<div>
  <h1 class="text-2xl font-semibold">{h(brand)} {h(name)}</h1>
  <p class="text-stone-500 text-sm">{h(brand)} · {h(pl)}</p>
  {dl}
</div>

<p class="text-stone-500 text-sm">{n} fired tile{"s" if n != 1 else ""} in this archive — cone {h(", ".join(cones))}, {h(", ".join(atmos))}, on {h(", ".join(clays))}</p>

<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
{cards}
</div>"""

    desc = (
        f"Fired test tile results for {brand} {pl} {sku} ({name}). "
        f"{n} tile{'s' if n != 1 else ''} at cone {', '.join(cones)}, {', '.join(atmos)}, "
        f"on {', '.join(clays)}. Real pottery photos."
    )

    out_path = out_dir / "glazes" / gid
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "index.html").write_text(
        page_html(
            title=f"{brand} {sku} {name} — Fired Test Tile Results | {SITE_NAME}",
            description=desc,
            canonical=f"/glazes/{gid}/",
            breadcrumbs=[
                ("Home", "/"),
                (brand, f"/brand/{bslug}/"),
                (pl, f"/brand/{bslug}/{plslug}/"),
                (f"{sku} {name}", f"/glazes/{gid}/"),
            ],
            body=body,
        ),
        encoding="utf-8",
    )
    pages_written += 1

# ── Per-product-line pages ────────────────────────────────────────────────────
for brand, pls in brands_index.items():
    bslug = slugify(brand)

    for pl, pl_glazes in pls.items():
        plslug = slugify(pl)
        total  = sum(glaze_tile_count[g["id"]] for g in pl_glazes)

        glaze_cards = []
        for g in sorted(pl_glazes, key=lambda g: g.get("sku", "")):
            gid   = g["id"]
            count = glaze_tile_count[gid]
            glaze_cards.append(
                f'<a href="/glazes/{h(gid)}/" class="bg-white rounded-lg p-3 shadow-sm hover:shadow-md transition-shadow flex flex-col gap-0.5">'
                f'<p class="text-sm font-medium">{h(g.get("name", gid))}</p>'
                f'<p class="text-xs text-stone-500">{h(g.get("sku",""))}</p>'
                f'<p class="text-xs text-stone-400 capitalize">{h(g.get("color",""))}{(" · " + g.get("finish","")) if g.get("finish") else ""}</p>'
                f'<p class="text-xs text-stone-400">{count} tile{"s" if count != 1 else ""}</p>'
                f'</a>'
            )

        body = f"""<div>
  <h1 class="text-2xl font-semibold">{h(brand)} {h(pl)}</h1>
  <p class="text-stone-500 text-sm">{len(pl_glazes)} glazes tested · {total} fired tiles</p>
</div>
<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
{"".join(glaze_cards)}
</div>"""

        out_path = out_dir / "brand" / bslug / plslug
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "index.html").write_text(
            page_html(
                title=f"{brand} {pl} Glaze Test Results | {SITE_NAME}",
                description=f"Fired test tile results for {len(pl_glazes)} {brand} {pl} glazes. Real pottery photos at cone {', '.join(sorted({str(mt.get('cone','')) for g in pl_glazes for mt in tiles_by_glaze.get(g['id'],[]) if mt.get('cone') is not None}))}.",
                canonical=f"/brand/{bslug}/{plslug}/",
                breadcrumbs=[
                    ("Home", "/"),
                    (brand, f"/brand/{bslug}/"),
                    (pl, f"/brand/{bslug}/{plslug}/"),
                ],
                body=body,
            ),
            encoding="utf-8",
        )
        pages_written += 1

# ── Per-brand pages ───────────────────────────────────────────────────────────
for brand, pls in brands_index.items():
    bslug        = slugify(brand)
    total_tiles  = sum(glaze_tile_count[g["id"]] for pl_glazes in pls.values() for g in pl_glazes)
    total_glazes = sum(len(v) for v in pls.values())

    pl_cards = []
    for pl, pl_glazes in sorted(pls.items()):
        plslug = slugify(pl)
        count  = sum(glaze_tile_count[g["id"]] for g in pl_glazes)
        pl_cards.append(
            f'<a href="/brand/{h(bslug)}/{h(plslug)}/" class="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">'
            f'<p class="font-medium">{h(pl)}</p>'
            f'<p class="text-sm text-stone-500 mt-1">{len(pl_glazes)} glazes · {count} tiles</p>'
            f'</a>'
        )

    body = f"""<div>
  <h1 class="text-2xl font-semibold">{h(brand)}</h1>
  <p class="text-stone-500 text-sm">{total_glazes} glazes tested across {len(pls)} product line{"s" if len(pls) != 1 else ""} · {total_tiles} fired tiles</p>
</div>
<div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
{"".join(pl_cards)}
</div>"""

    out_path = out_dir / "brand" / bslug
    out_path.mkdir(parents=True, exist_ok=True)
    (out_path / "index.html").write_text(
        page_html(
            title=f"{brand} Glaze Test Results | {SITE_NAME}",
            description=f"Fired test tile results for {brand} glazes — {', '.join(sorted(pls.keys()))}. Real pottery photos from a personal glaze testing archive.",
            canonical=f"/brand/{bslug}/",
            breadcrumbs=[("Home", "/"), (brand, f"/brand/{bslug}/")],
            body=body,
        ),
        encoding="utf-8",
    )
    pages_written += 1

# ── sitemap.xml ───────────────────────────────────────────────────────────────
urls = [SITE_URL + "/"]
for gid in tiles_by_glaze:
    urls.append(f"{SITE_URL}/glazes/{gid}/")
for brand, pls in brands_index.items():
    bslug = slugify(brand)
    urls.append(f"{SITE_URL}/brand/{bslug}/")
    for pl in pls:
        urls.append(f"{SITE_URL}/brand/{bslug}/{slugify(pl)}/")

sitemap_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for url in urls:
    sitemap_lines.append(f"  <url><loc>{url}</loc></url>")
sitemap_lines.append("</urlset>")
(out_dir / "sitemap.xml").write_text("\n".join(sitemap_lines) + "\n", encoding="utf-8")
print(f"sitemap.xml written ({len(urls)} URLs).")

print(f"Static pages written: {pages_written}")
print(f"Output: {out_dir}")
