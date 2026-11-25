function median(values) {
  const sorted = values.sort();
  const mid = Math.floor(sorted.length / 2);
  if (sorted.length % 2 === 0) {
    return (sorted[mid - 1] + sorted[mid]) / 2;
  }
  return sorted[mid];
}

async function saveAll(items, db) {
  items.forEach(async (item) => {
    await db.save(item);
  });
  console.log("all saved");
}

module.exports = { median, saveAll };
