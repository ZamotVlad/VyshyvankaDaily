document.addEventListener("DOMContentLoaded", function () {
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
