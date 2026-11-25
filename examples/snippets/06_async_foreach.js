const fs = require("fs/promises");

async function loadConfigs(paths) {
  const configs = [];
  paths.forEach(async (p) => {
    const text = await fs.readFile(p, "utf8");
    configs.push(JSON.parse(text));
  });
  return configs;
}

module.exports = { loadConfigs };
