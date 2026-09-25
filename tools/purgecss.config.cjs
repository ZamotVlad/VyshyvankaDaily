module.exports = {
  content: [
    "../templates/**/*.html",
    "../apps/**/*.py",
    "../apps/**/templates/**/*.html",
    "../static/js/*.js",
    "../static/vendor/bootstrap/bootstrap.bundle.min.js",
    "../region_content.json",
  ],
  css: ["../static/vendor/bootstrap/bootstrap.full.min.css"],
  variables: true,
  keyframes: true,
  fontFace: true,
  safelist: { standard: [/^show$/, /^showing$/, /^collapsing$/, /^collapse/, /^dropdown/, /^fade$/, /^active$/, /^disabled$/], greedy: [/data-bs-popper/, /data-bs-theme/] },
};
