(() => {
  "use strict";

  function refreshProjectPage() {
    document.querySelectorAll(".vp-project-card").forEach((card) => {
      if (card.dataset.ready) return;
      card.dataset.ready = "true";
      card.addEventListener("mouseenter", () => {
        card.style.borderLeft = "3px solid #18181B";
      });
      card.addEventListener("mouseleave", () => {
        card.style.borderLeft = "";
      });
    });
  }

  function init() {
    requestAnimationFrame(refreshProjectPage);
  }

  document.addEventListener("DOMContentLoaded", init);
  window.addEventListener("hashchange", () => setTimeout(init, 80));
  setTimeout(init, 500);
})();
