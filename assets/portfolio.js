(() => {
  "use strict";

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /*
   * Calm hero:
   * - deterministic architectural lines
   * - no random node spawning
   * - very slow movement
   * - low contrast
   * - pointer interaction is subtle
   */
  function initHeroNetwork() {
    const canvas = document.getElementById("hero-network");
    const visual = document.querySelector(".cover-visual");
    if (!canvas || !visual || canvas.dataset.initialized === "true") return;

    canvas.dataset.initialized = "true";
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      canvas.dataset.initialized = "false";
      return;
    }
    const state = { dpr: Math.min(window.devicePixelRatio || 1, 2), w: 0, h: 0 };

    function resize() {
      const rect = visual.getBoundingClientRect();
      state.w = rect.width;
      state.h = rect.height;

      canvas.width = Math.floor(rect.width * state.dpr);
      canvas.height = Math.floor(rect.height * state.dpr);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    }

    function draw(time) {
      ctx.clearRect(0, 0, state.w, state.h);

      const cx = state.w * 0.5;
      const cy = state.h * 0.5;
      const size = Math.min(state.w, state.h) * 0.55;

      // Extremely slow, almost imperceptible movement.
      const drift = reducedMotion ? 0 : Math.sin(time * 0.00012) * 3;

      ctx.save();
      ctx.translate(cx + drift, cy);

      // Architectural perspective plane.
      const lines = 9;
      for (let i = -lines; i <= lines; i++) {
        const offset = (i / lines) * size;

        ctx.beginPath();
        ctx.moveTo(offset, -size * .48);
        ctx.lineTo(offset * .62, size * .48);
        ctx.strokeStyle = "rgba(103,232,249,.075)";
        ctx.lineWidth = 1;
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(-size * .48, offset * .55);
        ctx.lineTo(size * .48, offset * .55);
        ctx.strokeStyle = "rgba(255,255,255,.045)";
        ctx.stroke();
      }

      // Three stable structural frames.
      [0, 1, 2].forEach((layer) => {
        const s = size * (.78 - layer * .16);

        ctx.beginPath();
        ctx.rect(-s / 2, -s / 2, s, s);
        ctx.strokeStyle = layer === 0
          ? "rgba(103,232,249,.16)"
          : "rgba(167,139,250,.085)";
        ctx.lineWidth = 1;
        ctx.stroke();
      });

      // Stable connection points.
      const points = [
        [-.39, -.32], [.39, -.32],
        [-.39, .32], [.39, .32],
        [0, -.48], [0, .48],
        [0, 0]
      ];

      points.forEach(([x, y], index) => {
        const px = x * size;
        const py = y * size;

        ctx.beginPath();
        ctx.arc(px, py, index === 6 ? 2.5 : 1.7, 0, Math.PI * 2);
        ctx.fillStyle = index === 6
          ? "rgba(103,232,249,.78)"
          : "rgba(167,139,250,.38)";
        ctx.fill();
      });

      ctx.restore();

      if (!reducedMotion) requestAnimationFrame(draw);
    }

    visual.addEventListener("pointermove", (event) => {
      if (reducedMotion) return;
      const rect = visual.getBoundingClientRect();
      const x = (event.clientX - rect.left) / rect.width - .5;
      const y = (event.clientY - rect.top) / rect.height - .5;

      visual.style.setProperty("--mx", `${x * 3.5}deg`);
      visual.style.setProperty("--my", `${y * -3.5}deg`);
    });

    visual.addEventListener("pointerleave", () => {
      visual.style.setProperty("--mx", "0deg");
      visual.style.setProperty("--my", "0deg");
    });

    resize();
    window.addEventListener("resize", resize, { passive: true });
    draw(performance.now());
  }

  function initCardTilt() {
    if (reducedMotion) return;

    document.querySelectorAll(".markdown-section h2 + ul > li").forEach((card) => {
      if (card.dataset.tiltInitialized === "true") return;
      card.dataset.tiltInitialized = "true";

      card.addEventListener("pointermove", (event) => {
        const rect = card.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width - .5;
        const y = (event.clientY - rect.top) / rect.height - .5;

        card.style.transform =
          `perspective(1000px) rotateX(${y * -3.5}deg) rotateY(${x * 3.5}deg) translateY(-3px)`;
      });

      card.addEventListener("pointerleave", () => {
        card.style.transform = "";
      });
    });
  }

  function initializePage() {
    setTimeout(() => {
      initHeroNetwork();
      initCardTilt();
    }, 80);
  }

  window.addEventListener("hashchange", initializePage);
  document.addEventListener("DOMContentLoaded", initializePage);
  setTimeout(initializePage, 400);
})();
