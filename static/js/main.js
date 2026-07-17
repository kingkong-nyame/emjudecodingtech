/* ═══════════════════════════════════════════════════════════════════
   EmjudeCodingTech — main.js
   Handles: dark mode, navbar scroll, mobile menu, flash dismiss,
            typing animation (home page), footer year
   ═══════════════════════════════════════════════════════════════════ */

/* ── Dark mode ───────────────────────────────────────────────────────── */
const html         = document.documentElement;
const themeToggle  = document.getElementById('theme-toggle');
const THEME_KEY    = 'ect-theme';

function applyTheme(theme) {
  html.setAttribute('data-theme', theme);
  localStorage.setItem(THEME_KEY, theme);
}

// Load saved theme or system preference
const savedTheme = localStorage.getItem(THEME_KEY);
if (savedTheme) {
  applyTheme(savedTheme);
} else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
  applyTheme('dark');
}

themeToggle?.addEventListener('click', () => {
  applyTheme(html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
});

/* ── Navbar scroll shadow ────────────────────────────────────────────── */
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar?.classList.toggle('scrolled', window.scrollY > 10);
}, { passive: true });

/* ── Mobile hamburger menu ───────────────────────────────────────────── */
const hamburger = document.getElementById('hamburger');
const mobileNav = document.getElementById('mobile-nav');

hamburger?.addEventListener('click', () => {
  const open = hamburger.classList.toggle('open');
  mobileNav.classList.toggle('open', open);
  hamburger.setAttribute('aria-expanded', open);
  mobileNav.setAttribute('aria-hidden', !open);
});

// Close mobile nav on link click
mobileNav?.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    hamburger.classList.remove('open');
    mobileNav.classList.remove('open');
  });
});

/* ── Flash message dismiss ───────────────────────────────────────────── */
document.querySelectorAll('.flash__close').forEach(btn => {
  btn.addEventListener('click', () => {
    btn.closest('.flash')?.remove();
  });
});

// Auto-dismiss flashes after 5 seconds
setTimeout(() => {
  document.querySelectorAll('.flash').forEach(f => {
    f.style.transition = 'opacity .4s';
    f.style.opacity = '0';
    setTimeout(() => f.remove(), 400);
  });
}, 5000);

/* ── Footer year ─────────────────────────────────────────────────────── */
const yearEl = document.getElementById('footer-year');
if (yearEl) yearEl.textContent = new Date().getFullYear();

/* ── Typing animation (home page hero) ──────────────────────────────── */
const typedEl = document.getElementById('typed-text');
if (typedEl) {
  const phrases = [
    'Full-stack web developer',
    'Flutter mobile developer',
    'Python & Flask engineer',
    'API & backend specialist',
    'C# / .NET developer',
    'Next.js developer',
  ];
  let phraseIndex = 0, charIndex = 0, deleting = false;

  function type() {
    const phrase = phrases[phraseIndex];
    typedEl.textContent = deleting
      ? phrase.slice(0, --charIndex)
      : phrase.slice(0, ++charIndex);

    if (!deleting && charIndex === phrase.length) {
      deleting = true;
      setTimeout(type, 1800);
      return;
    }
    if (deleting && charIndex === 0) {
      deleting = false;
      phraseIndex = (phraseIndex + 1) % phrases.length;
    }
    setTimeout(type, deleting ? 40 : 70);
  }
  type();
}

/* ── Scroll reveal (simple, no library) ─────────────────────────────── */
const revealEls = document.querySelectorAll('[data-reveal]');

if (revealEls.length > 0) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  revealEls.forEach(el => observer.observe(el));
}

/* ── Portfolio filter (portfolio page) ──────────────────────────────── */
const filterBtns = document.querySelectorAll('[data-filter]');
filterBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const cat = btn.getAttribute('data-filter');
    window.location.search = cat === 'all' ? '' : `?category=${cat}`;
  });
});

/* ── Admin: confirm before delete ───────────────────────────────────── */
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => {
    const msg = form.getAttribute('data-confirm') || 'Are you sure?';
    if (!confirm(msg)) e.preventDefault();
  });
});