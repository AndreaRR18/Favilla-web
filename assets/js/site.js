// Favilla site — reveals, theme toggle, night sky (stars + fireflies), the
// cursor's little firefly. Progressive enhancement only: the site is fully
// usable without JS.
(function () {
  "use strict";

  var root = document.documentElement;

  // Scroll reveal — runs first, so nothing below can stop content appearing.
  // The inline head script hides `.reveal` content (html.js) and un-hides it
  // after a few seconds unless this file says it is in charge (fv-ready):
  // a blocked, failed or broken site.js never leaves the page invisible.
  // Disabled under prefers-reduced-motion via CSS.
  (function () {
    var items = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      items.forEach(function (item) { item.classList.add("revealed"); });
    } else {
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
    }
    root.classList.add("fv-ready");
  })();

  // Dark / light theme toggle. Initial theme is set inline in <head> so there
  // is no flash; here we only react to clicks and sync the button state.
  var toggle = document.querySelector(".theme-toggle");
  if (toggle) {
    var syncButton = function () {
      var light = root.dataset.theme === "light";
      toggle.setAttribute("aria-pressed", light ? "true" : "false");
    };
    syncButton();

    // No explicit choice yet: keep following the OS when it switches
    // (e.g. automatic dark mode at sunset).
    var osLight = window.matchMedia && window.matchMedia("(prefers-color-scheme: light)");
    if (osLight && osLight.addEventListener) {
      osLight.addEventListener("change", function (event) {
        var chosen = null;
        try { chosen = localStorage.getItem("fv-theme"); } catch (e) { /* storage blocked */ }
        if (chosen) { return; }
        root.dataset.theme = event.matches ? "light" : "dark";
        syncButton();
      });
    }

    toggle.addEventListener("click", function () {
      var next = root.dataset.theme === "light" ? "dark" : "light";
      root.dataset.theme = next;
      try {
        localStorage.setItem("fv-theme", next);
      } catch (e) {
        /* private mode: the choice just won't persist */
      }
      syncButton();
    });
  }

  var fine = window.matchMedia && window.matchMedia("(pointer: fine)").matches;
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Night sky — dark theme only, none if reduced motion is requested.
  if (!calm && document.querySelector(".night-sky")) {
    var sky = document.querySelector(".night-sky");

    // a scatter of tiny stars, each twinkling on its own clock
    for (var i = 0; i < 30; i++) {
      var star = document.createElement("i");
      star.className = "star";
      var size = (Math.random() * 1.4 + 0.8).toFixed(1);
      star.style.width = size + "px";
      star.style.height = size + "px";
      star.style.left = (Math.random() * 100).toFixed(2) + "vw";
      star.style.top = (Math.random() * 92).toFixed(2) + "vh";
      star.style.setProperty("--st-dur", (Math.random() * 4 + 2.5).toFixed(2) + "s");
      star.style.setProperty("--st-delay", (-Math.random() * 6).toFixed(2) + "s");
      sky.appendChild(star);
    }

    // ambient fireflies. Positions are fixed so the look is always composed.
    var SPOTS = [
      { x: "12vw", y: "22vh", dx: "26px", dy: "-34px", d: "17s", delay: "0s" },
      { x: "78vw", y: "14vh", dx: "-34px", dy: "22px", d: "21s", delay: "-7s" },
      { x: "64vw", y: "52vh", dx: "20px", dy: "-26px", d: "24s", delay: "-12s" },
      { x: "30vw", y: "66vh", dx: "-24px", dy: "-18px", d: "19s", delay: "-4s" },
      { x: "88vw", y: "70vh", dx: "18px", dy: "-30px", d: "26s", delay: "-16s" },
      { x: "45vw", y: "36vh", dx: "-16px", dy: "-24px", d: "23s", delay: "-9s" },
    ];
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

  // The cursor's companion: the Favilla mark — a bright dot with three flat
  // concentric rings — wandering near the pointer, perching on links, shedding
  // a spark or two when it moves fast, bursting on click, drifting off when
  // you rest. Only on fine pointers (a mouse or trackpad).
  //
  // Under Reduce Motion it does what the app's fireflies do: it stays, but
  // holds still. It sits at a fixed spot beside the pointer (or perched on the
  // link under it), placed on each pointer event — no frame loop, no
  // wandering, no sparks, no blinking, and it doesn't wander off when you rest.
  var fly = document.querySelector(".cursor-fly");
  if (fly && !fine) {
    fly.remove();
  } else if (fly) {
    var px = 0, py = 0;        // pointer, in viewport units
    var fx = 0, fy = 0;        // the firefly
    var lastFx = 0, lastFy = 0;
    var phase = Math.random() * Math.PI * 2;
    var visible = false;       // shown, or still fading out
    var leaving = false;       // fading out (resting, or pointer left the window)
    var idleTimer = null;
    var fadeTimer = null;
    var perchEl = null;        // link/button the firefly is sitting on
    var glow = 0;              // 0..1, brighter when the pointer moves fast
    var lastTrail = 0;
    var running = false;       // the frame loop sleeps while there is nothing to draw

    var place = function () {
      fly.style.transform = "translate3d(" + fx.toFixed(1) + "px," + fy.toFixed(1) + "px,0)";
    };

    // the perch: just above the top-right corner of the hovered link
    var perchSpot = function () {
      if (!perchEl || !document.body.contains(perchEl)) { return null; }
      var r = perchEl.getBoundingClientRect();
      return { x: r.right - 4, y: r.top - 6 };
    };

    // Reduce Motion: put it exactly where it belongs, once per event
    var placeStill = function () {
      var spot = perchSpot();
      fx = spot ? spot.x : px + 18;
      fy = spot ? spot.y : py - 18;
      place();
    };

    // one small spark that drifts out and fades (used for trails and bursts)
    var spawnSpark = function (x, y, dist, dur) {
      var s = document.createElement("i");
      s.className = "fly-spark";
      var ang = Math.random() * Math.PI * 2;
      var dx = Math.cos(ang) * dist;
      var dy = Math.sin(ang) * dist;
      s.style.left = x.toFixed(1) + "px";
      s.style.top = y.toFixed(1) + "px";
      document.body.appendChild(s);
      var anim = s.animate(
        [
          { transform: "translate(0, 0) scale(1)", opacity: 0.9 },
          { transform: "translate(" + dx.toFixed(1) + "px," + dy.toFixed(1) + "px) scale(0.2)", opacity: 0 }
        ],
        { duration: dur, easing: "cubic-bezier(.2,.6,.4,1)" }
      );
      anim.onfinish = function () { s.remove(); };
    };

    // dim and go; `visible` turns false once the CSS fade has finished, which
    // is what lets the frame loop stop
    var fadeOut = function () {
      if (!visible || leaving) { return; }
      leaving = true;
      fly.classList.remove("is-visible");
      if (fadeTimer) { window.clearTimeout(fadeTimer); }
      fadeTimer = window.setTimeout(function () {
        visible = false;
        leaving = false;
      }, 650);
    };

    // Fireflies only come out at night, as in the app's forest: in light mode
    // the companion isn't shown and its frame loop never runs.
    var isDay = function () { return root.dataset.theme === "light"; };

    var hideNow = function () {
      if (idleTimer) { window.clearTimeout(idleTimer); }
      if (fadeTimer) { window.clearTimeout(fadeTimer); }
      visible = false;
      leaving = false;
      fly.classList.remove("is-visible");
    };

    // switching to light mode puts it out at once (the toggle, or the OS)
    new MutationObserver(function () {
      if (isDay()) { hideNow(); }
    }).observe(root, { attributes: true, attributeFilter: ["data-theme"] });

    var wake = function () {
      if (isDay()) { return; }
      if (fadeTimer) { window.clearTimeout(fadeTimer); fadeTimer = null; }
      if (!visible || leaving) {
        if (!visible) {
          // appear near the pointer, not where it was last time
          fx = px + Math.cos(phase) * 30;
          fy = py + Math.sin(phase) * 30;
          lastFx = fx;
          lastFy = fy;
        }
        visible = true;
        leaving = false;
        fly.classList.add("is-visible");
      }
      if (calm) {
        placeStill();
        return; // holds still: no frame loop, no idle drift
      }
      ensureRunning();
      if (idleTimer) { window.clearTimeout(idleTimer); }
      idleTimer = window.setTimeout(function () {
        // rest: the light drifts away and dims — unless it's perched on
        // something, then it just stays there, quietly lit
        if (!perchEl) { fadeOut(); }
      }, 3600);
    };

    document.addEventListener("mousemove", function (event) {
      px = event.clientX;
      py = event.clientY;
      wake();
    }, { passive: true });

    // hovering a link, button or FAQ row: the firefly comes and perches
    // on its top-right corner, wings folded
    document.addEventListener("mouseover", function (event) {
      var t = event.target && event.target.closest
        ? event.target.closest("a, button, summary")
        : null;
      perchEl = t;
      fly.classList.toggle("is-perched", !!t);
      if (calm && visible) { placeStill(); }
    });

    // a perched firefly stays on its link while the page scrolls under it
    if (calm) {
      window.addEventListener("scroll", function () {
        if (visible && perchEl) { placeStill(); }
      }, { passive: true });
    }

    // a tap makes a small burst of sparks
    document.addEventListener("pointerdown", function () {
      if (!visible || leaving || calm) { return; }
      for (var n = 0; n < 6; n++) {
        window.setTimeout(function () {
          spawnSpark(fx, fy, 16 + Math.random() * 24, 500 + Math.random() * 350);
        }, n * 45);
      }
    });

    // the pointer left the window: the light goes with it
    document.addEventListener("mouseleave", function () {
      if (idleTimer) { window.clearTimeout(idleTimer); }
      fadeOut();
    });

    var ensureRunning = function () {
      if (running) { return; }
      running = true;
      window.requestAnimationFrame(tick);
    };

    var tick = function (time) {
      if (!visible) {
        // faded out and gone: stop until the pointer moves again
        running = false;
        return;
      }
      var targetX, targetY, ease;
      var spot = perchSpot();
      if (spot) {
        targetX = spot.x;
        targetY = spot.y;
        ease = 0.14;
      } else if (!leaving) {
        // wander around the pointer, lazy loops instead of a spotlight
        phase += 0.012;
        var radius = 34 + 16 * Math.sin(phase * 0.7);
        targetX = px + Math.cos(phase * 1.1) * radius;
        targetY = py + Math.sin(phase * 1.4) * radius * 0.62;
        ease = 0.055;
      } else {
        // flying off into the night, upward
        targetX = px - 60;
        targetY = py - 90;
        ease = 0.03;
      }
      fx += (targetX - fx) * ease;
      fy += (targetY - fy) * ease;

      var speed = Math.abs(fy - lastFy) + Math.abs(fx - lastFx);
      lastFx = fx;
      lastFy = fy;

      // the light burns brighter the faster you move
      var targetGlow = Math.min(1, speed * 0.09);
      glow += (targetGlow - glow) * 0.12;
      fly.style.setProperty("--fly-glow", glow.toFixed(2));

      // shed a tiny spark now and then when flying quickly
      if (!spot && !leaving && speed > 2.2 && time - lastTrail > 110) {
        lastTrail = time;
        spawnSpark(fx, fy, 6 + Math.random() * 10, 480 + Math.random() * 260);
      }

      place();
      window.requestAnimationFrame(tick);
    };
  }
})();
