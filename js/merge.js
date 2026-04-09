/**
 * mergeTiles(batches, tiles)
 *
 * Takes the raw arrays from batches.yaml and tiles.yaml and returns a flat
 * array of tile objects ready for display and filtering. Tile-level fields
 * take precedence over batch-level fields. Tags are merged (union), not
 * replaced, so a tile inherits its batch tags and can add its own.
 */
function mergeTiles(batches, tiles) {
  const batchMap = Object.fromEntries(batches.map(b => [b.id, b]));

  return tiles.map(tile => {
    const batch = batchMap[tile.batch];
    if (!batch) {
      console.warn(`Tile ${tile.id} references unknown batch "${tile.batch}"`);
      return tile;
    }

    const batchTags = batch.tags ?? [];
    const tileTags = tile.tags ?? [];
    const mergedTags = [...new Set([...batchTags, ...tileTags])];

    return {
      ...batch,       // batch fields first (lower priority)
      ...tile,        // tile fields override batch fields
      tags: mergedTags,           // tags are merged, not overridden
      _batch: batch,              // keep the raw batch for reference (e.g. to show overrides in the UI)
    };
  });
}
