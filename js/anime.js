/* ===== Starwise — Anime: pemutar playlist on-demand ===== */

document.addEventListener('DOMContentLoaded', () => {

  const frame = document.getElementById('player-frame');
  const empty = document.getElementById('player-empty');
  const box = document.getElementById('player-box');
  if (!frame || !empty) return;

  let current = null;

  function show(playlistId, videoId, title) {
    if (current) {
      current.src = 'about:blank';
      current.remove();
    }

    const src = 'https://www.youtube.com/embed/' + videoId +
      '?list=' + playlistId + '&rel=0';

    const iframe = document.createElement('iframe');
    iframe.src = src;
    iframe.title = title || 'Player anime';
    iframe.setAttribute('allow',
      'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture');
    iframe.setAttribute('allowfullscreen', '');
    iframe.loading = 'lazy';

    frame.replaceChildren(iframe);
    frame.hidden = false;
    empty.hidden = true;
    current = iframe;

    if (box) {
      box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  document.querySelectorAll('.pl-play').forEach(btn => {
    btn.addEventListener('click', (ev) => {
      ev.preventDefault();
      show(btn.dataset.playlist, btn.dataset.video, btn.dataset.title);
    });
  });

  // Klik kartu playlist juga memutar, kecuali yang diklik link YouTube.
  document.querySelectorAll('.pl-card').forEach(card => {
    card.addEventListener('click', (ev) => {
      if (ev.target.closest('.pl-link') || ev.target.closest('.pl-play')) return;
      const btn = card.querySelector('.pl-play');
      if (btn) btn.click();
    });
  });

});