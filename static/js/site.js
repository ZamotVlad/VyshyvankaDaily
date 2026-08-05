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
});
