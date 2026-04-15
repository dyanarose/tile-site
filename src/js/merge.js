/**
 * mergeTiles(batches, tiles, glazes)
 *
 * Produces a flat array of tile objects ready for display and filtering.
 * - Tile-level fields override batch-level fields
 * - Tags are merged (union)
 * - glazes: [] (list of IDs) is resolved to full glaze objects
 * - glaze_combo (free text) is kept as a fallback if no structured glazes
 */
function mergeTiles(batches, tiles, glazes = []) {
  const batchMap = Object.fromEntries(batches.map(b => [b.id, b]));
  const glazeMap = Object.fromEntries(glazes.map(g => [g.id, g]));

  return tiles.map(tile => {
    const batch = batchMap[tile.batch];
    if (!batch) {
      console.warn(`Tile ${tile.id} references unknown batch "${tile.batch}"`);
      return tile;
    }

    const batchTags = batch.tags ?? [];
    const tileTags  = tile.tags ?? [];
    const mergedTags = [...new Set([...batchTags, ...tileTags])];

    // Resolve glaze IDs → full glaze objects
    const resolvedGlazes = (tile.glaze_combo ?? [])
      .map(id => {
        const g = glazeMap[id];
        if (!g) console.warn(`Tile ${tile.id} references unknown glaze "${id}"`);
        return g ?? { id, name: id }; // fallback to bare ID if not found
      });

    return {
      ...batch,
      ...tile,
      tags:           mergedTags,
      resolvedGlazes, // full glaze objects for display/filtering
      _batch:         batch,
    };
  });
}
