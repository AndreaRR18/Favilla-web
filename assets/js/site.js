// VoiceTale site — language menu behavior + scroll reveals.
// Progressive enhancement only: the site is fully usable without JS.
(function () {
  "use strict";

  // Close the language menu when clicking (or focusing) outside of it.
  var menus = document.querySelectorAll(".lang-menu");

  document.addEventListener("click", function (event) {
    menus.forEach(function (menu) {
      if (menu.open && !menu.contains(event.target)) {
        menu.open = false;
      }
    });
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      menus.forEach(function (menu) { menu.open = false; });
    }
  });

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
