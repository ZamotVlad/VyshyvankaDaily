// Лічильник символів для SEO-полів в адмінці.
(function () {
  var LIMITS = { title: [30, 60], description: [120, 155] };

  function attach(field) {
    var m = field.name.match(/^seo_(title|description)(_uk|_en)?$/);
    if (!m) return;
    var range = LIMITS[m[1]];
    var out = document.createElement("div");
    out.className = "vd-seo-counter";
    field.insertAdjacentElement("afterend", out);
    function update() {
      var n = field.value.trim().length;
      out.textContent = n + " / " + range[0] + "-" + range[1];
      out.dataset.state = n === 0 ? "empty" : n > range[1] ? "over" : n < range[0] ? "short" : "ok";
    }
    field.addEventListener("input", update);
    update();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("input[name^=seo_], textarea[name^=seo_]").forEach(attach);
  });
})();
