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

  // Search: find matching text in cards, news, downloads on this page
  const searchInput = document.getElementById('search-input');
  const searchBtn = document.getElementById('search-btn');
  const searchResults = document.getElementById('search-results');

  function doSearch() {
    const query = searchInput.value.trim().toLowerCase();
    if (!query) {
      searchResults.innerHTML = '<p class="search-empty">Masukkan kata kunci untuk mencari.</p>';
      return;
    }

    // Gather all searchable elements in the page
    const items = document.querySelectorAll(
      '.card-body h3, .card-body p, .news-item h3, .news-item p, .download-item h4, .download-item p, .section-title'
    );

    const matches = [];
    items.forEach(el => {
      const text = el.textContent.trim().toLowerCase();
      if (text.includes(query)) {
        // Get the card/item container
        const card = el.closest('.card') || el.closest('.news-item') || el.closest('.download-item') || el.closest('section');
        if (card) {
          matches.push(card);
        }
      }
    });

    if (matches.length === 0) {
      searchResults.innerHTML = '<p class="search-empty">Tidak ada hasil untuk "' + searchInput.value + '".</p>';
      return;
    }

    // Build results list — show clickable links to sections
    let html = '<p class="search-count">Ditemukan ' + matches.length + ' hasil:</p><div class="search-match-list">';
    matches.forEach((card, idx) => {
      // Try to find the heading inside
      const heading = card.querySelector('h3') || card.querySelector('h4') || card.querySelector('.news-date') || card;
      const text = heading.textContent.trim();
      html += '<div class="search-match">' + text + '</div>';
    });
    html += '</div>';
    searchResults.innerHTML = html;
  }

  if (searchBtn && searchInput) {
    searchBtn.addEventListener('click', doSearch);
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        doSearch();
        e.preventDefault();
      }
    });
  }

  // Filter kategori di halaman overview streaming
  const catSearch = document.getElementById('cat-search');
  const catGrid = document.getElementById('cat-grid');
  const catEmpty = document.getElementById('cat-empty');
  const catCount = document.getElementById('cat-search-count');

  if (catSearch && catGrid) {
    const catCards = Array.from(catGrid.querySelectorAll('.cat-card'));

    function filterCats() {
      const q = catSearch.value.trim().toLowerCase();
      let shown = 0;

      catCards.forEach(card => {
        const haystack = (card.dataset.search || card.textContent).toLowerCase();
        const hit = !q || haystack.includes(q);
        card.hidden = !hit;
        if (hit) shown++;
      });

      if (catEmpty) catEmpty.hidden = shown !== 0;
      if (catCount) {
        catCount.textContent = q
          ? shown + ' dari ' + catCards.length + ' kategori cocok'
          : catCards.length + ' kategori';
      }
    }

    catSearch.addEventListener('input', filterCats);
    filterCats();
  }

  // Thumbnail YouTube: maxresdefault -> hqdefault -> placeholder
  document.querySelectorAll('img[data-fallback]').forEach(img => {
    img.addEventListener('error', function () {
      const fb = this.getAttribute('data-fallback');
      if (fb && !this.dataset.tried) {
        this.dataset.tried = '1';
        this.src = fb;
      }
    });
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
