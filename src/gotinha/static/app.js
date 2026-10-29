/**
 * Gotinha — frontend
 */

// ============================================================================
// Theme — fixo: o site é papel quente.
// ============================================================================
function initTheme() {
  // Design system atual é claro por design (papel quente). Nada a fazer.
  document.documentElement.setAttribute('data-theme', 'paper');
}

// ============================================================================
// Mobile menu
// ============================================================================
function initMobileMenu() {
  const toggle = document.getElementById('menuToggle');
  const nav = document.getElementById('mobileNav');
  if (!toggle || !nav) return;

  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    nav.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
  });

  nav.addEventListener('click', (e) => {
    if (e.target.closest('a')) {
      nav.classList.remove('is-open');
      nav.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
    }
  });
}

// ============================================================================
// Scroll spy — marca o link do header correspondente à seção visível
// ============================================================================
function initScrollSpy() {
  const links = Array.from(document.querySelectorAll('.nav-link'));
  if (!links.length) return;
  const sections = links
    .map((l) => document.querySelector(l.getAttribute('href')))
    .filter(Boolean);
  if (!sections.length) return;

  const setActive = (id) => {
    links.forEach((l) => {
      const target = l.getAttribute('href').replace('#', '');
      l.classList.toggle('active', target === id);
    });
  };

  const observer = new IntersectionObserver(
    (entries) => {
      // Pega a entrada mais visível no topo
      const visible = entries
        .filter((e) => e.isIntersecting)
        .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
      if (visible) setActive(visible.target.id);
    },
    { rootMargin: '-40% 0px -55% 0px', threshold: 0 }
  );
  sections.forEach((s) => observer.observe(s));
}

// ============================================================================
// Reveal on scroll
// ============================================================================
function initRevealOnScroll() {
  const els = document.querySelectorAll(
    '.passo, .dado, .tema, .citacao, .hero-mascote, .hero-doodle'
  );
  if (!els.length || !('IntersectionObserver' in window)) {
    els.forEach((el) => el.classList.add('reveal', 'is-visible'));
    return;
  }
  els.forEach((el) => el.classList.add('reveal'));
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('is-visible');
          obs.unobserve(e.target);
        }
      });
    },
    { rootMargin: '0px 0px -10% 0px', threshold: 0.05 }
  );
  els.forEach((el) => obs.observe(el));
}

// ============================================================================
// Service worker (offline-first para assets estáticos)
// ============================================================================
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/static/sw.js').catch((err) => {
      console.log('SW registration failed:', err);
    });
  });
}

// ============================================================================
// Init
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initMobileMenu();
  initScrollSpy();
  initRevealOnScroll();
});
