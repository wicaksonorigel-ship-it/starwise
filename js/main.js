/* ===== Starwise — Main JS ===== */

document.addEventListener('DOMContentLoaded', () => {

  // Mobile menu toggle
  const menuToggle = document.querySelector('.menu-toggle');
  const mainNav = document.querySelector('.main-nav');

  if (menuToggle && mainNav) {
    menuToggle.addEventListener('click', () => {
      mainNav.classList.toggle('open');
      menuToggle.setAttribute('aria-expanded', mainNav.classList.contains('open'));
    });
  }

  // Active nav link based on current page
  const currentPath = location.pathname;
  const navLinks = document.querySelectorAll('.main-nav a');
  navLinks.forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath.endsWith(href)) {
      link.classList.add('active');
    }
  });

  // Video cards: thumbnail click -> open YouTube in new tab
  const videoThumbs = document.querySelectorAll('.video-thumb');
  videoThumbs.forEach(thumb => {
    thumb.addEventListener('click', () => {
      const href = thumb.getAttribute('data-video');
      if (href) {
        window.open(href, '_blank', 'noopener');
      }
    });

    // Hover play overlay subtle scale
    const overlay = thumb.querySelector('.play-overlay');
    if (overlay) {
      thumb.addEventListener('mouseenter', () => {
        overlay.style.transform = 'scale(1.05)';
      });
      thumb.addEventListener('mouseleave', () => {
        overlay.style.transform = 'scale(1)';
      });
    }
  });

  // YouTube embed in modal/inline (optional pattern) — here we just link out
  // For inline embed demo, any iframe with class .embed-yt will load on click
  const embedTriggers = document.querySelectorAll('[data-embed-yt]');
  embedTriggers.forEach(el => {
    el.addEventListener('click', () => {
      const iframe = document.getElementById(el.getAttribute('data-embed-yt'));
      if (iframe) {
        iframe.src = iframe.dataset.embedSrc || iframe.src;
        iframe.style.display = 'block';
        el.style.display = 'none';
      }
    });
  });

});
