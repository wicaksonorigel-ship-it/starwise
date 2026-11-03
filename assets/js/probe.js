/* ===== Starwise — Tes embed: deteksi video mana yang bisa diputar ===== */

(function () {
  'use strict';

  const items = Array.from(document.querySelectorAll('.probe-item'));
  const elTotal = document.getElementById('total');
  const elTested = document.getElementById('tested');
  const elOk = document.getElementById('ok');
  const elBad = document.getElementById('bad');
  const elResult = document.getElementById('result');
  const btnAll = document.getElementById('test-all');
  const btnCopy = document.getElementById('copy-ok');

  if (!items.length) return;

  const stats = { total: items.length, tested: 0, ok: [], bad: [] };
  elTotal.textContent = stats.total;

  // Deteksi lewat YouTube IFrame API: player mengirim postMessage
  // berisi state. Ini akurat, berbeda dengan membaca halaman.
  const callbacks = Object.create(null);

  window.addEventListener('message', function (ev) {
    if (!ev.data || typeof ev.data !== 'object') return;
    const msg = ev.data;
    // Pesan dari IFrame API
    if (msg.event === 'onError' || (msg.info && msg.info.playabilityStatus &&
        msg.info.playabilityStatus.status !== 'OK')) {
      const vid = msg.id || msg.videoId;
      if (vid && callbacks[vid]) callbacks[vid](false, reasonOf(msg));
    }
    if (msg.event === 'initialDelivery' || msg.event === 'playing' ||
        msg.event === 'onReady') {
      const vid = msg.id || msg.videoId;
      if (vid && callbacks[vid] && !msg.info) callbacks[vid](true, null);
      else if (vid && callbacks[vid] && msg.info &&
               msg.info.playabilityStatus && msg.info.playabilityStatus.status === 'OK' &&
               !callbacks[vid].done) {
        callbacks[vid].done = true;
        callbacks[vid](true, null);
      }
    }
  });

  function reasonOf(msg) {
    const ps = msg.info && msg.info.playabilityStatus;
    return (ps && ps.reason) || msg.reason || 'tidak diketahui';
  }

  function testOne(item) {
    return new Promise(function (resolve) {
      const vid = item.dataset.vid;
      const player = item.querySelector('.probe-player');
      const status = item.querySelector('.probe-status');
      const btn = item.querySelector('.probe-btn');

      status.className = 'probe-status testing';
      status.textContent = 'menguji...';
      btn.disabled = true;

      let settled = false;
      const finish = function (ok, reason) {
        if (settled) return;
        settled = true;
        delete callbacks[vid];

        status.className = 'probe-status ' + (ok ? 'ok' : 'bad');
        status.textContent = ok ? 'BISA embed' : 'tidak bisa (' + (reason || 'blocked') + ')';
        item.classList.toggle('is-ok', ok);
        item.classList.toggle('is-bad', !ok);

        stats.tested++;
        if (ok) stats.ok.push(item); else stats.bad.push(item);
        elTested.textContent = stats.tested;
        elOk.textContent = stats.ok.length;
        elBad.textContent = stats.bad.length;

        // kalau tidak bisa, hapus iframe supaya tidak boros resource
        if (!ok) player.innerHTML = '';
        resolve(ok);
      };

      callbacks[vid] = finish;

      player.innerHTML =
        '<iframe src="https://www.youtube.com/embed/' + vid +
        '?enablejsapi=1&rel=0&playsinline=1" allow="autoplay; encrypted-media" ' +
        'allowfullscreen title="test ' + vid + '"></iframe>';

      // Timeout: kalau 9 detik tidak ada jawaban, anggap tidak bisa
      setTimeout(function () { finish(false, 'timeout'); }, 9000);
    });
  }

  items.forEach(function (item) {
    const btn = item.querySelector('.probe-btn');
    if (btn) btn.addEventListener('click', function () { testOne(item); });
  });

  if (btnAll) {
    btnAll.addEventListener('click', async function () {
      btnAll.disabled = true;
      btnAll.textContent = 'Menguji...';
      for (const item of items) {
        await testOne(item);
        await new Promise(function (r) { setTimeout(r, 350); });
      }
      btnAll.textContent = 'Selesai';
      report();
    });
  }

  if (btnCopy) {
    btnCopy.addEventListener('click', function () {
      if (!stats.ok.length) {
        elResult.textContent = 'Belum ada video yang bisa embed. Jalankan "Tes semua" dulu.';
        return;
      }
      const lines = stats.ok.map(function (item) {
        const ch = item.querySelector('strong').textContent.replace(/^@/, '');
        const code = item.querySelector('code').textContent;
        return ch + '  ' + code;
      });
      const text = lines.join('\n');
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function () {
          elResult.textContent = 'Disalin ' + stats.ok.length +
            ' video yang bisa embed ke clipboard.';
        });
      } else {
        elResult.textContent = 'Salin manual:\n' + text;
      }
    });
  }

  function report() {
    if (elResult) {
      elResult.innerHTML = 'Selesai. <strong>' + stats.ok.length + ' bisa embed</strong>, ' +
        stats.bad.length + ' tidak. Klik "Salin yang bisa" lalu kirim hasilnya ke saya.';
    }
  }

})();