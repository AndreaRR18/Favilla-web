// VoiceTale site — theme toggle + scroll reveals.
// Progressive enhancement only: the site is fully usable without JS.
(function () {
  "use strict";

  // Dark / light theme toggle. Initial theme is set inline in <head> so there
  // is no flash; here we only react to clicks and sync the button state.
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    var syncButton = function () {
      var light = document.documentElement.dataset.theme === "light";
      toggle.setAttribute("aria-pressed", light ? "true" : "false");
    };
    syncButton();
    toggle.addEventListener("click", function () {
      var next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
      document.documentElement.dataset.theme = next;
      try {
        localStorage.setItem("vt-theme", next);
      } catch (e) {
        /* private mode: the choice just won't persist */
      }
      syncButton();
    });
  }

  // Scroll reveal — disabled under prefers-reduced-motion via CSS.
  var items = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window) || items.length === 0) {
    items.forEach(function (item) { item.classList.add("revealed"); });
    return;
  }

  var observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("revealed");
          observer.unobserve(entry.target);
        }
      });
    },
    { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
  );

  items.forEach(function (item) { observer.observe(item); });
})();
