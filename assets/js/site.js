// Favilla site — theme toggle, night fireflies, the cursor's firefly, reveals.
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
        localStorage.setItem("fv-theme", next);
      } catch (e) {
        /* private mode: the choice just won't persist */
      }
      syncButton();
    });
  }

  // Ambient fireflies in the night sky — dark theme only, none if reduced
  // motion is requested. Positions are fixed so the look is always composed.
  var fine = window.matchMedia && window.matchMedia("(pointer: fine)").matches;
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!calm && document.querySelector(".night-sky")) {
    var SPOTS = [
      { x: "12vw", y: "22vh", dx: "26px", dy: "-34px", d: "17s", delay: "0s" },
      { x: "78vw", y: "14vh", dx: "-34px", dy: "22px", d: "21s", delay: "-7s" },
      { x: "64vw", y: "52vh", dx: "20px", dy: "-26px", d: "24s", delay: "-12s" },
      { x: "30vw", y: "66vh", dx: "-24px", dy: "-18px", d: "19s", delay: "-4s" },
      { x: "88vw", y: "70vh", dx: "18px", dy: "-30px", d: "26s", delay: "-16s" },
      { x: "45vw", y: "36vh", dx: "-16px", dy: "-24px", d: "23s", delay: "-9s" },
    ];
    var sky = document.querySelector(".night-sky");
    SPOTS.forEach(function (spot) {
      var ff = document.createElement("i");
      ff.className = "ff";
      ff.style.left = spot.x;
      ff.style.top = spot.y;
      ff.style.setProperty("--ff-dx", spot.dx);
      ff.style.setProperty("--ff-dy", spot.dy);
      ff.style.setProperty("--ff-duration", spot.d);
      ff.style.setProperty("--ff-delay", spot.delay);
      sky.appendChild(ff);
    });
  }

  // The cursor's firefly: it lingers near the pointer, blinks, and drifts off
  // when you rest. Only on fine pointers, never under reduced motion.
  if (!fine || calm) {
    var lonely = document.querySelector(".cursor-fly");
    if (lonely) { lonely.remove(); }
  } else {
    var fly = document.querySelector(".cursor-fly");
    var shell = fly ? fly.querySelector(".fly-shell") : null;
    if (fly && shell) {
      var px = 0, py = 0;        // pointer, in viewport units
      var fx = 0, fy = 0;        // the firefly's position
      var lastFx = 0, lastFy = 0;
      var phase = Math.random() * Math.PI * 2;
      var visible = false;
      var idleTimer = null;
      var leaving = false;

      var wake = function () {
        if (!document.body.contains(fly)) { return; }
        if (!visible) {
          visible = true;
          leaving = false;
          fx = px + Math.cos(phase) * 30;
          fy = py + Math.sin(phase) * 30;
          fly.classList.add("is-visible");
        }
        if (idleTimer) { window.clearTimeout(idleTimer); }
        idleTimer = window.setTimeout(function () {
          // rest: the light drifts away and dims
          leaving = true;
          fly.classList.remove("is-visible");
          window.setTimeout(function () {
            visible = false;
            leaving = false;
          }, 650);
        }, 3200);
      };

      document.addEventListener("mousemove", function (event) {
        px = event.clientX;
        py = event.clientY;
        wake();
      }, { passive: true });

      document.addEventListener("mouseleave", function () {
        leaving = true;
        fly.classList.remove("is-visible");
        if (idleTimer) { window.clearTimeout(idleTimer); }
      });

      var tick = function (time) {
        if (visible) {
          if (!leaving) {
            // wander around the pointer, lazy loops instead of a spotlight
            phase += 0.012;
            var radius = 26 + 14 * Math.sin(phase * 0.7);
            var targetX = px + Math.cos(phase * 1.1) * radius;
            var targetY = py + Math.sin(phase * 1.4) * radius * 0.62;
            fx += (targetX - fx) * 0.055;
            fy += (targetY - fy) * 0.055;
          } else {
            fx += (px - 60 - fx) * 0.03;
            fy += (py - 80 - fy) * 0.03;
          }

          var vy = fy - lastFy;
          lastFx = fx;
          lastFy = fy;

          fly.style.transform = "translate3d(" + fx.toFixed(1) + "px," + fy.toFixed(1) + "px,0)";
          var climb = Math.max(-20, Math.min(20, vy * 26));
          var sway = Math.sin(time * 0.004) * 6;
          shell.style.transform = "rotate(" + (climb + sway).toFixed(1) + "deg)";
        }
        window.requestAnimationFrame(tick);
      };
      window.requestAnimationFrame(tick);
    }
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
