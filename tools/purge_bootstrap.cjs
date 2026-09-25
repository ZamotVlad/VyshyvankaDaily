// Урізає Bootstrap під класи з шаблонів: cd tools && npm i purgecss@7 && node purge_bootstrap.cjs
const fs = require("fs");
const { PurgeCSS } = require("purgecss");
const config = require("./purgecss.config.cjs");

(async () => {
  const [result] = await new PurgeCSS().purge(config);
  fs.writeFileSync("../static/vendor/bootstrap/bootstrap.min.css", result.css);
  console.log(`bootstrap.min.css: ${result.css.length} bytes`);
})();
