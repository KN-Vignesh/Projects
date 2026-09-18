(() => {
  'use strict';

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function enhancePage() {
    const root = document.querySelector('.markdown-section');
    if (!root) return;

    root.classList.remove('vp-page');
    root.classList.add(location.hash === '#/' || location.hash === '' || /README$/.test(location.hash) ? 'vp-home-page' : 'vp-project-page');

    const links = root.querySelectorAll('a');
    links.forEach((link) => {
      link.addEventListener('click', () => link.classList.add('vp-link-pulse'), { once: true });
    });

    root.querySelectorAll('h2').forEach((heading) => {
      heading.classList.add('vp-section-heading');
      if (!heading.previousElementSibling || !heading.previousElementSibling.classList?.contains('vp-index-marker')) {
        const marker = document.createElement('span');
        marker.className = 'vp-index-marker';
        marker.setAttribute('aria-hidden', 'true');
        marker.textContent = heading.textContent.split(' — ')[0].trim();
        heading.prepend(marker);
      }
    });

    document.querySelectorAll('.vp-project-row').forEach((row) => row.remove());
    root.querySelectorAll('h3').forEach((heading) => {
      heading.classList.add('vp-project-title');
    });

    setupReveal(root);
    setupPointer(root);
  }

  function setupReveal(root) {
    const targets = root.querySelectorAll('h2, h3, table, pre, blockquote, .markdown-section > p');
    if (reducedMotion || !('IntersectionObserver' in window)) {
      targets.forEach((el) => el.classList.add('vp-visible'));
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('vp-visible');
        observer.unobserve(entry.target);
      });
    }, { threshold: 0.06 });

    targets.forEach((el, index) => {
      el.classList.add('vp-reveal');
      el.style.setProperty('--vp-delay', `${Math.min(index * 20, 180)}ms`);
      observer.observe(el);
    });
  }

  function setupPointer(root) {
    if (reducedMotion || window.matchMedia('(pointer: coarse)').matches) return;

    const cards = root.querySelectorAll('h3');
    cards.forEach((heading) => {
      heading.addEventListener('pointermove', (event) => {
        const rect = heading.getBoundingClientRect();
        const x = ((event.clientX - rect.left) / rect.width - 0.5) * 5;
        const y = ((event.clientY - rect.top) / rect.height - 0.5) * 3;
        heading.style.transform = `translate(${x}px, ${y}px)`;
      });
      heading.addEventListener('pointerleave', () => {
        heading.style.transform = '';
      });
    });
  }

  function init() {
    requestAnimationFrame(enhancePage);
  }

  document.addEventListener('DOMContentLoaded', init);
  window.addEventListener('hashchange', () => setTimeout(init, 100));
})();
