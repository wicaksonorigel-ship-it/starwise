/* ===== Starwise — Berita: filter game + muat ulang ===== */

document.addEventListener('DOMContentLoaded', () => {

  const select = document.getElementById('news-game');
  const shown = document.getElementById('news-shown');
  const lists = Array.from(document.querySelectorAll('.news-list[data-game]'));
  const sections = Array.from(document.querySelectorAll('.section[id^="berita-"]'));
  const refreshBtn = document.getElementById('news-refresh');
  const statusEl = document.getElementById('news-status');

  function applyFilter() {
    const want = select ? select.value : '';
    let total = 0;

    lists.forEach(list => {
      const match = !want || list.dataset.game === want;
      list.hidden = !match;
      if (match) total += list.querySelectorAll('.news-row').length;
    });

    sections.forEach(sec => {
      const list = sec.querySelector('.news-list');
      const match = !want || (list && list.dataset.game === want);
      sec.hidden = !match;
      const count = sec.querySelector('.news-count');
      if (count && match && list) {
        count.textContent = list.querySelectorAll('.news-row').length + ' berita';
      }
    });

    if (shown) {
      shown.textContent = total + ' berita ditampilkan';
    }
  }

  if (select) {
    select.addEventListener('change', applyFilter);
  }
  applyFilter();

  // Tombol muat ulang: cache-busting lewat URL fetch, lalu parse judul/date.
  // Sengaja tidak menulis ulang halaman — cukup tampilkan catatan status
  // supaya pengguna tahu kapan data terakhir di-refresh.
  if (refreshBtn && statusEl) {
    refreshBtn.addEventListener('click', () => {
      refreshBtn.disabled = true;
      refreshBtn.textContent = 'Memuat…';
      statusEl.textContent = 'Mengambil berita terbaru…';

      const url = location.pathname.split('?')[0] + '?t=' + Date.now();

      fetch(url, { cache: 'no-store' })
        .then(r => (r.ok ? r.text() : Promise.reject(r.status)))
        .then(html => {
          const doc = new DOMParser().parseFromString(html, 'text/html');
          const fresh = doc.querySelectorAll('.news-row').length;
          const stamp = doc.querySelector('.status-item:nth-child(2) b');

          if (fresh > 0) {
            statusEl.innerHTML =
              'Ditemukan <b>' + fresh + '</b> berita' +
              (stamp ? ' (terbaru: ' + stamp.textContent + ')' : '') +
              '. Muat ulang halaman untuk melihat daftar.';
          } else {
            statusEl.textContent = 'Tidak ada berita baru sejak refresh terakhir.';
          }
        })
        .catch(() => {
          statusEl.textContent = 'Gagal memuat. Periksa koneksi lalu coba lagi.';
        })
        .finally(() => {
          refreshBtn.disabled = false;
          refreshBtn.textContent = 'Muat berita terbaru';
        });
    });
  }

});