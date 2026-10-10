/* ===== Starwise — Tier List: modal detail karakter ===== */

document.addEventListener('DOMContentLoaded', () => {

  const items = document.querySelectorAll('.tc-item[data-name]');
  if (!items.length) return;

  // Bangun modal sekali, dipakai ulang.
  const overlay = document.createElement('div');
  overlay.className = 'tier-modal';
  overlay.hidden = true;
  overlay.innerHTML =
    '<div class="tier-modal-box" role="dialog" aria-modal="true" aria-labelledby="tm-name">' +
      '<button type="button" class="tier-modal-close" aria-label="Tutup">&times;</button>' +
      '<div class="tier-modal-head">' +
        '<img class="tier-modal-img" alt="">' +
        '<div>' +
          '<h3 id="tm-name"></h3>' +
          '<div class="tier-modal-badges"></div>' +
        '</div>' +
      '</div>' +
      '<dl class="tier-modal-facts"></dl>' +
      '<p class="tier-modal-note"></p>' +
      '<div class="tier-modal-actions"></div>' +
    '</div>';
  document.body.appendChild(overlay);

  const box = overlay.querySelector('.tier-modal-box');
  const elName = overlay.querySelector('#tm-name');
  const elImg = overlay.querySelector('.tier-modal-img');
  const elBadges = overlay.querySelector('.tier-modal-badges');
  const elFacts = overlay.querySelector('.tier-modal-facts');
  const elNote = overlay.querySelector('.tier-modal-note');
  const elActions = overlay.querySelector('.tier-modal-actions');

  let lastFocus = null;

  function labelFor(el) {
    if (!el) return '';
    return el.trim();
  }

  function open(item) {
    lastFocus = document.activeElement;

    const name = item.dataset.name || '';
    const tier = item.dataset.tier || '';
    const element = item.dataset.el || '';
    const role = item.dataset.role || '';
    const rarity = item.dataset.rarity || '';
    const img = item.dataset.img || '';
    const slug = item.dataset.slug || '';

    elName.textContent = name;
    elImg.src = img;
    elImg.alt = name;

    // badge: tier + element + rarity
    const badges = [];
    if (tier) badges.push('<span class="tm-badge tm-tier">Tier ' + tier + '</span>');
    if (element) badges.push('<span class="tm-badge tm-el">' + element + '</span>');
    if (rarity) {
      const star = /^\d+$/.test(rarity) ? rarity + '★' : rarity + '-Rank';
      badges.push('<span class="tm-badge tm-rar">' + star + '</span>');
    }
    elBadges.innerHTML = badges.join('');

    // tabel fakta
    const facts = [
      ['Tier', tier || '-'],
      ['Element', element || '-'],
      ['Role', role || '-'],
      ['Rarity', rarity ? (/^\d+$/.test(rarity) ? rarity + ' bintang' : rarity + '-Rank') : '-'],
    ];
    elFacts.innerHTML = facts.map(function (f) {
      return '<div class="tm-fact"><dt>' + f[0] + '</dt><dd>' + f[1] + '</dd></div>';
    }).join('');

    elNote.textContent =
      'Tier dan atribut dirangkum dari sumber pihak ketiga (Prydwen Institute / Game8). ' +
      'Peringkat bisa berubah setelah patch baru.';

    // tombol aksi
    const actions = [];
    if (slug) {
      const gameSlug = item.dataset.game || '';
      if (gameSlug) {
        actions.push('<a class="btn btn-primary" target="_blank" rel="noopener" href="' +
          'https://www.prydwen.gg/' + gameSlug + '/characters/' + slug +
          '">Build lengkap di Prydwen</a>');
      }
    }
    actions.push('<button type="button" class="btn btn-secondary tier-modal-dismiss">Tutup</button>');
    elActions.innerHTML = actions.join('');

    overlay.hidden = false;
    document.body.classList.add('tier-modal-open');
    box.focus();
  }

  function close() {
    overlay.hidden = true;
    document.body.classList.remove('tier-modal-open');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  items.forEach(function (item) {
    item.addEventListener('click', function () { open(item); });
  });

  overlay.addEventListener('click', function (ev) {
    if (ev.target === overlay) close();
    if (ev.target.closest('.tier-modal-close')) close();
    if (ev.target.closest('.tier-modal-dismiss')) close();
  });

  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && !overlay.hidden) close();
  });

});