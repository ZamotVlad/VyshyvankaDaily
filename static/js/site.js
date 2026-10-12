document.addEventListener("DOMContentLoaded", function () {
  // Вкладки регіонів: без JS видно всі групи, з JS - по одній
  document.querySelectorAll("[data-tabs]").forEach(function (root) {
    var list = root.querySelector("[role=tablist]");
    var tabs = root.querySelectorAll("[role=tab]");
    var panels = root.querySelectorAll("[role=tabpanel]");
    if (!list || !tabs.length) return;
    var select = function (index, focus) {
      tabs.forEach(function (tab, i) {
        var on = i === index;
        tab.setAttribute("aria-selected", on);
        tab.tabIndex = on ? 0 : -1;
        panels[i].hidden = !on;
      });
      if (focus) tabs[index].focus();
    };
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () {
        select(i, false);
      });
      tab.addEventListener("keydown", function (e) {
        if (e.key === "ArrowRight") select((i + 1) % tabs.length, true);
        if (e.key === "ArrowLeft") select((i - 1 + tabs.length) % tabs.length, true);
      });
    });
    list.hidden = false;
    root.classList.add("is-ready");
    select(0, false);
  });

  // Зміст: підсвічує розділ, який зараз читають
  var toc = document.querySelector("[data-toc]");
  if (toc) {
    var links = {};
    toc.querySelectorAll("a[href^='#']").forEach(function (a) {
      links[decodeURIComponent(a.getAttribute("href").slice(1))] = a;
    });
    var headings = Object.keys(links)
      .map(function (id) {
        return document.getElementById(id);
      })
      .filter(Boolean);
    var current = null;
    var setCurrent = function (id) {
      if (id === current) return;
      if (current && links[current]) links[current].removeAttribute("aria-current");
      current = id;
      if (links[id]) links[id].setAttribute("aria-current", "true");
    };
    var update = function () {
      var active = headings[0];
      headings.forEach(function (h) {
        if (h.getBoundingClientRect().top < 140) active = h;
      });
      if (active) setCurrent(active.id);
    };
    var ticking = false;
    window.addEventListener(
      "scroll",
      function () {
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(function () {
          update();
          ticking = false;
        });
      },
      { passive: true }
    );
    update();
  }

  // Кнопка «нагору» на довгих сторінках
  var toTop = document.querySelector("[data-to-top]");
  if (toTop && document.documentElement.scrollHeight > window.innerHeight * 3) {
    toTop.hidden = false;
    var topTicking = false;
    var syncTop = function () {
      toTop.classList.toggle("is-visible", window.scrollY > window.innerHeight * 1.5);
      topTicking = false;
    };
    window.addEventListener(
      "scroll",
      function () {
        if (!topTicking) {
          topTicking = true;
          requestAnimationFrame(syncTop);
        }
      },
      { passive: true }
    );
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0 });
      document.getElementById("main-content").focus({ preventScroll: true });
    });
    syncTop();
  }

  // Мобільне меню на весь екран
  var burger = document.querySelector(".vd-burger");
  var panel = document.getElementById("vdMobileNav");
  if (burger && panel) {
    var header = document.querySelector(".vd-header");
    var setMenu = function (open) {
      if (open) {
        document.documentElement.style.setProperty(
          "--vd-header-h",
          header.getBoundingClientRect().bottom + "px"
        );
      }
      panel.hidden = !open;
      burger.setAttribute("aria-expanded", open);
      document.documentElement.classList.toggle("vd-menu-open", open);
    };
    burger.addEventListener("click", function () {
      setMenu(panel.hidden);
    });
    panel.addEventListener("click", function (e) {
      if (e.target.closest("a")) setMenu(false);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) setMenu(false);
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 1060 && !panel.hidden) setMenu(false);
    });
  }

  // Розгортка "Що таке VyshyvankaDaily" на головній
  var landingToggle = document.querySelector(".vd-landing__toggle");
  if (landingToggle) {
    landingToggle.addEventListener("click", function () {
      var body = document.getElementById("landing-body");
      var isOpen = body.classList.toggle("is-open");
      landingToggle.classList.toggle("is-open");
      landingToggle.setAttribute("aria-expanded", isOpen);

      var toggleText = document.getElementById("landing-toggle-text");
      if (toggleText) {
        toggleText.textContent = isOpen ? toggleText.dataset.less : toggleText.dataset.more;
      }
    });
  }

  // Перемикач мови - автоматичне надсилання форми при виборі
  document.querySelectorAll(".vd-lang select").forEach(function (select) {
    select.addEventListener("change", function () {
      select.form.submit();
    });
  });

  // Лайтбокс для фото регіону
  var lightbox = document.getElementById("photo-lightbox");
  if (lightbox) {
    var lightboxImg = lightbox.querySelector(".vd-lightbox__img");
    var lightboxCaption = lightbox.querySelector(".vd-lightbox__caption");
    var closeBtn = lightbox.querySelector(".vd-lightbox__close");

    document.querySelectorAll(".vd-photo-strip__item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        lightboxImg.src = btn.dataset.full;
        lightboxImg.alt = btn.dataset.caption || "";
        lightboxCaption.textContent = btn.dataset.caption || "";
        lightbox.hidden = false;
      });
    });

    function closeLightbox() {
      lightbox.hidden = true;
      lightboxImg.src = "";
    }
    closeBtn.addEventListener("click", closeLightbox);
    lightbox.addEventListener("click", function (e) {
      if (e.target === lightbox) closeLightbox();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !lightbox.hidden) closeLightbox();
    });
  }
});

// Кнопка "показати пароль" - для будь-якого поля password на сторінці
// (реєстрація, вхід, зміна/відновлення пароля - усюди одразу, бо шукає
// за типом поля, не за конкретною сторінкою)
var EYE_OPEN =
  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
var EYE_CLOSED =
  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0 1 12 20c-7 0-11-8-11-8a18.7 18.7 0 0 1 5.06-5.94M9.9 4.24A10.4 10.4 0 0 1 12 4c7 0 11 8 11 8a18.7 18.7 0 0 1-2.16 3.19M14.12 14.12a3 3 0 1 1-4.24-4.24"/><path d="M1 1l22 22"/></svg>';

document.querySelectorAll('input[type="password"]').forEach(function (input) {
  var wrapper = document.createElement("div");
  wrapper.style.position = "relative";
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);
  input.style.paddingRight = "40px";

  var toggle = document.createElement("button");
  toggle.type = "button";
  toggle.innerHTML = EYE_CLOSED;
  toggle.setAttribute("aria-label", "Показати пароль");
  toggle.style.cssText =
    "position:absolute; right:8px; top:50%; transform:translateY(-50%); " +
    "background:none; border:none; cursor:pointer; padding:0; display:flex; color: var(--vd-muted);";
  wrapper.appendChild(toggle);

  toggle.addEventListener("click", function () {
    var isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    toggle.innerHTML = isPassword ? EYE_OPEN : EYE_CLOSED;
    toggle.setAttribute("aria-label", isPassword ? "Приховати пароль" : "Показати пароль");
  });
});

// Мапа регіонів на /regions/: наведення, вибір з наближенням, частини України.
(function () {
  var root = document.querySelector("[data-vd-map]");
  if (!root) return;
  var svg = root.querySelector(".vd-map__svg");
  var layer = root.querySelector(".vd-map__regions");
  var box = root.querySelector(".vd-map__box");
  var panel = root.querySelector(".vd-map__panel");
  var regions = Array.prototype.slice.call(root.querySelectorAll(".vd-map__rg"));
  var labels = {};
  root.querySelectorAll(".vd-map__lbl[data-for]").forEach(function (l) {
    labels[l.getAttribute("data-for")] = l;
  });
  var W = +svg.getAttribute("data-w");
  var H = +svg.getAttribute("data-h");
  var full = [0, 0, W, H];
  var vb = full.slice();
  var active = null;
  var group = "";
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Ширина підписів під текст; підпис не виходить за межі мапи.
  root.querySelectorAll(".vd-map__lbl").forEach(function (l) {
    var t = l.querySelector("text");
    var r = l.querySelector("rect");
    var w = t.getComputedTextLength() + 22;
    r.setAttribute("width", w);
    r.setAttribute("x", -w / 2);
    var m = /translate\(([-\d.]+)[ ,]+([-\d.]+)\)/.exec(l.getAttribute("transform") || "");
    if (!m || !l.hasAttribute("data-for")) return;
    var x = Math.min(Math.max(+m[1], w / 2 + 4), W - w / 2 - 4);
    var y = Math.min(Math.max(+m[2], 15), H - 15);
    l.setAttribute("transform", "translate(" + x + " " + y + ")");
  });

  // Поява грає один раз за сесію.
  var seen = false;
  try {
    seen = sessionStorage.getItem("vdMapSeen") === "1";
    sessionStorage.setItem("vdMapSeen", "1");
  } catch (e) {}
  if (seen || reduce) {
    root.classList.add("is-ready");
  } else {
    setTimeout(function () {
      root.classList.add("is-ready");
    }, regions.length * 50 + 1500);
  }

  function animateVB(to) {
    if (reduce) {
      vb = to;
      svg.setAttribute("viewBox", to.join(" "));
      return;
    }
    var from = vb.slice();
    var t0 = performance.now();
    function step(now) {
      var t = Math.min(1, (now - t0) / 650);
      var k = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      vb = from.map(function (v, i) {
        return v + (to[i] - v) * k;
      });
      svg.setAttribute("viewBox", vb.join(" "));
      if (t < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function fit(els, pad) {
    var x1 = Infinity, y1 = Infinity, x2 = -Infinity, y2 = -Infinity;
    function add(b) {
      x1 = Math.min(x1, b.x);
      y1 = Math.min(y1, b.y);
      x2 = Math.max(x2, b.x + b.width);
      y2 = Math.max(y2, b.y + b.height);
    }
    els.forEach(function (el) {
      add(el.querySelector(".vd-map__linen").getBBox());
      var l = labels[el.getAttribute("data-slug")];
      if (l) {
        var m = /translate\(([-\d.]+) ([-\d.]+)\)/.exec(l.getAttribute("transform"));
        var rb = l.querySelector("rect");
        if (m) add({ x: +m[1] - rb.getAttribute("width") / 2, y: +m[2] - 11, width: +rb.getAttribute("width"), height: 22 });
      }
    });
    var w = x2 - x1 + pad * 2;
    var h = y2 - y1 + pad * 2;
    if (w / h > W / H) {
      var nh = (w * H) / W;
      y1 -= (nh - h) / 2;
      h = nh;
    } else {
      var nw = (h * W) / H;
      x1 -= (nw - w) / 2;
      w = nw;
    }
    return [x1 - pad, y1 - pad, w, h];
  }

  function highlight(el, raise) {
    regions.forEach(function (r) {
      var on = r === el || r === active;
      r.classList.toggle("is-on", on);
      var l = labels[r.getAttribute("data-slug")];
      if (l) l.classList.toggle("is-show", on || (group && r.getAttribute("data-group") === group));
    });
    svg.classList.toggle("is-dim", !!(el || active));
    if (el && raise !== false && root.classList.contains("is-ready") && layer.lastElementChild !== el) {
      layer.appendChild(el);
    }
  }

  function field(name) {
    return panel.querySelector('[data-f="' + name + '"]');
  }

  function select(el) {
    active = el;
    var sel = panel.querySelector(".vd-map__sel");
    var idle = panel.querySelector(".vd-map__idle");
    if (!el) {
      sel.hidden = true;
      idle.hidden = false;
      panel.classList.remove("is-open");
      highlight(null);
      var inGroup = regions.filter(function (r) {
        return r.getAttribute("data-group") === group;
      });
      animateVB(group ? fit(inGroup, 30) : full);
      return;
    }
    field("group").textContent = el.getAttribute("data-group-label");
    field("name").textContent = el.getAttribute("data-name");
    field("teaser").textContent = el.getAttribute("data-teaser");
    field("motif").textContent = el.getAttribute("data-motif");
    field("url").href = el.getAttribute("href");
    var sw = field("colors");
    sw.innerHTML = "";
    el.getAttribute("data-colors").split(" ").forEach(function (c) {
      if (!c) return;
      var s = document.createElement("span");
      s.className = "vd-swatch";
      s.style.backgroundColor = c;
      sw.appendChild(s);
    });
    sel.hidden = false;
    idle.hidden = true;
    panel.classList.add("is-open");
    highlight(el);
    animateVB(fit([el], 60));
  }

  regions.forEach(function (el) {
    el.addEventListener("pointerenter", function (e) {
      if (e.pointerType === "mouse") highlight(el);
    });
    el.addEventListener("pointerleave", function () {
      highlight(active);
    });
    el.addEventListener("focus", function () {
      highlight(el, false);
    });
    el.addEventListener("blur", function () {
      if (!active) highlight(null);
    });
    el.addEventListener("click", function (e) {
      // Другий клік по вибраному регіону - перехід на його сторінку.
      if (active === el) return;
      e.preventDefault();
      select(el);
    });
  });

  panel.querySelector(".vd-map__close").addEventListener("click", function () {
    select(null);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && active) select(null);
  });

  root.querySelectorAll(".vd-map__chip").forEach(function (b) {
    b.addEventListener("click", function () {
      group = b.getAttribute("data-group");
      root.querySelectorAll(".vd-map__chip").forEach(function (x) {
        x.setAttribute("aria-pressed", x === b ? "true" : "false");
      });
      regions.forEach(function (r) {
        r.classList.toggle("is-in", r.getAttribute("data-group") === group);
      });
      svg.classList.toggle("is-grouped", !!group);
      select(null);
    });
  });

  if (!reduce && window.matchMedia("(hover: hover)").matches) {
    box.addEventListener("pointermove", function (e) {
      var r = box.getBoundingClientRect();
      svg.style.setProperty("--ry", ((e.clientX - r.left) / r.width - 0.5) * 5 + "deg");
      svg.style.setProperty("--rx", -((e.clientY - r.top) / r.height - 0.5) * 5 + "deg");
    });
    box.addEventListener("pointerleave", function () {
      svg.style.setProperty("--rx", "0deg");
      svg.style.setProperty("--ry", "0deg");
    });
  }
})();
