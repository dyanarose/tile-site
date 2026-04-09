# Pottery Test Tile Archive

A static single-page app for browsing and filtering pottery test tiles. No server, no build step — just open `index.html` or deploy to any static host.

**Live site:** https://dyanarose.github.io/tile-site/

## Adding tiles after a firing

1. **Photograph** all tiles
2. **Upload photos to R2** — drag and drop in the Cloudflare R2 dashboard, or use rclone for bulk uploads
3. **Edit `data/batches.yaml`** — add one batch block
4. **Edit `data/tiles.yaml`** — add one tile block per tile
5. **Regenerate the data file:**
   ```bash
   python build-data.py
   ```
6. **Deploy:**
   ```bash
   git add .
   git commit -m "Add batch YYYY-MM-DD"
   git push
   ```
   The site updates automatically via GitHub Pages.

## Configuration

The `CONFIG` block at the top of `index.html` controls:

```js
const CONFIG = {
  photoBaseUrl: 'https://your-bucket.r2.dev/',  // R2 public base URL
};
```

## Data format

### `data/batches.yaml`

```yaml
- id: batch-001
  date: 2024-09-14
  clay_body: Valentine's Stoneware
  cone: 10
  atmosphere: reduction        # reduction | oxidation
  glazes:
    - Tenmoku
    - Shino
  notes: "Optional firing notes."
  tags: [high-fire, reduction]
```

### `data/tiles.yaml`

Tiles only record what differs from their parent batch. Minimum required: `id`, `batch`, `photo`.

```yaml
- id: tile-001
  batch: batch-001
  photo: folder/filename.jpg   # path within R2 bucket
  glaze_combo: Tenmoku alone   # optional — specific combo tested
  notes: "Optional tile notes."
  tags: [crawling]             # optional — adds to batch tags
```

## Photo naming

- Primary photo: `tile-001.jpg`
- Optional reverse/detail: `tile-001b.jpg` (inferred automatically)

## Local development

Open `index.html` directly in a browser — no server needed.

After editing YAML, run `python build-data.py` to regenerate `data/data.js`, then refresh.

## Stack

- [Alpine.js](https://alpinejs.dev/) — reactivity
- [Tailwind CSS](https://tailwindcss.com/) — styling (CDN)
- [Cloudflare R2](https://developers.cloudflare.com/r2/) — photo storage (10 GB free, no egress fees)
- [GitHub Pages](https://pages.github.com/) — hosting
