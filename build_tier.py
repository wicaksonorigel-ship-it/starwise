# -*- coding: utf-8 -*-
"""Bangun halaman tier list per game Starwise.

Mengambil peringkat + atribut karakter (element, rarity, role) lalu menulis:
  - tierlist-<game>.html  : halaman tier list dengan karakter yang bisa diklik
  - tierlist.html         : daftar semua game
  - _tier_data.json       : data untuk disisipkan ke halaman panduan

Sumber: Prydwen Institute (5 game) dan Game8 (Genshin Impact).
Ikon diunduh ke img/tier/<game>/ supaya tidak hotlink.

Jalankan: python build_tier.py
"""
import html
import json
import pathlib
import re
import time
import urllib.request

BASE = pathlib.Path(__file__).parent
UA = {"User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# slug -> (nama, url, subfolder ikon)
PRYDWEN = {
    "hsr": ("Honkai: Star Rail", "https://www.prydwen.gg/star-rail/tier-list/", "honkai-star-rail"),
    "zzz": ("Zenless Zone Zero", "https://www.prydwen.gg/zenless/tier-list/", "zenless-zone-zero"),
    "wuthering": ("Wuthering Waves", "https://www.prydwen.gg/wuthering-waves/tier-list/", "wuthering-waves"),
    "endfield": ("Arknights: Endfield", "https://www.prydwen.gg/arknights-endfield/tier-list", "arknights-endfield"),
    "nte": ("Neverness to Everness", "https://www.prydwen.gg/neverness-to-everness/tier-list", "nte"),
}
GAME8_GI = "https://game8.co/games/Genshin-Impact/archives/297465"

GAME_SLUG = {
    "hsr": "star-rail", "zzz": "zenless", "wuthering": "wuthering-waves",
    "endfield": "arknights-endfield", "nte": "neverness-to-everness",
}

LOGO = {"hsr": "hsr", "zzz": "zzz", "wuthering": "ww",
        "endfield": "endfield", "nte": "nte", "genshin": "gi"}

# halaman panduan yang mendapat section tier list
GUIDE_MAP = {
    "hsr": "guide-honkai-star-rail.html",
    "zzz": "guide-zenless-zone-zero.html",
    "wuthering": "guide-wuthering-waves.html",
    "endfield": "guide-arknights-endfield.html",
    "nte": "guide-neverness-to-everness.html",
    "genshin": "guide-genshin-impact.html",
}

TIER_COLOR = {
    "T0": "#ef4444", "T05": "#f97316", "T0.5": "#f97316",
    "T1": "#eab308", "T15": "#84cc16", "T1.5": "#84cc16",
    "T2": "#22c55e", "T3": "#14b8a6", "T4": "#3b82f6", "T5": "#6366f1",
    "SS": "#ef4444", "S": "#f97316", "A": "#eab308", "B": "#22c55e",
    "C": "#3b82f6", "D": "#6366f1",
}
TIER_LABEL = {"T05": "T0.5", "T15": "T1.5"}

SKIP = {"quantum", "physical", "fire", "ice", "lightning", "wind", "imaginary",
        "ether", "electric", "frost", "aero", "glacio", "fusion", "havoc",
        "spectro", "pyro", "hydro", "cryo", "dendro", "geo", "anemo", "electro",
        "lumiflux", "honest", "anima", "chaos", "cosmos", "incantation",
        "lakshana", "psyche"}

NAV = '''      <nav class="main-nav">
        <a href="index.html">Home</a>
        <a href="games.html">Games</a>
        <a href="anime.html">Anime</a>
        <a href="movies.html">Film</a>
        <a href="news.html">Berita</a>
        <a href="database.html">Database</a>
        <a href="tierlist.html">Tier List</a>
        <a href="streaming.html">Streaming</a>
        <a href="download.html">Download</a>
      </nav>'''


def esc(s):
    return html.escape(str(s), quote=True)


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")


def parse_prydwen(url):
    """Ambil tier, karakter, element, rarity, dan role dari halaman tier list."""
    h = fetch(url)

    # peta slug -> role (role ditulis sebagai header sebelum grup karakter)
    roles = {}
    cur = ""
    for m in re.finditer(
            r'burst-type-mobile \w+">.*?<!-- -->([A-Za-z ]{2,14})</div>'
            r'|href="/[\w-]+/characters/([^"/]+)"', h, re.S):
        if m.group(1):
            cur = m.group(1).strip()
        elif m.group(2):
            roles.setdefault(m.group(2), cur)

    parts = re.split(r'<div class="tier-rating t-([\w.]+)">', h)
    tiers = []
    for i in range(1, len(parts), 2):
        raw, body = parts[i], parts[i + 1]
        # Struktur berbeda antar game:
        #  HSR/WuWa : <div class="avatar hsr rarity-5"> lalu element di class
        #  ZZZ/NTE  : <div class="avatar ..."> lalu element di alt gambar dalam
        pairs = re.findall(
            r'<a href="/[\w-]+/characters/([^"/]+)">\s*<div class="avatar([^"]*)">'
            r'\s*<img alt="([^"]+)"[^>]*src="(https://cdn\.prydwen\.gg/images/[^"]+?)"'
            r'(.*?)(?=</div>\s*</a>|</a>)', body, re.S)
        chars, seen = [], set()
        for slug, avatarclass, alt, icon, tail in pairs:
            if alt in seen or alt.lower() in SKIP:
                continue
            seen.add(alt)
            # Element punya 4 varian struktur antar game:
            #   HSR  : class="floating-element element hsr Quantum"
            #   WuWa : <span class="floating-element ww-element-tl"><img alt="Glacio"
            #   ZZZ  : <div class="element"><img alt="Electric"
            #   NTE  : <div class="element"><img alt="Psyche"
            el = (re.search(r'floating-element element \w+ (\w+)"', tail)
                  or re.search(r'ww-element-tl"><img alt="([^"]+)"', tail)
                  or re.search(r'class="element"><img alt="([^"]+)"', tail))
            # Rarity: angka (HSR/WuWa) atau huruf (ZZZ: rarity-S, NTE)
            rar = (re.search(r'rarity-(\d+)', avatarclass)
                   or re.search(r'rarity-([A-Z])\b', avatarclass)
                   or re.search(r'rarity-(\d+)', tail)
                   or re.search(r'rarity-([A-Z])\b', tail))
            # WuWa & Endfield tidak punya role; mereka pakai tier-list-tags
            # (mis. "Chafe", "INT Form"). Pakai itu sebagai keterangan.
            tags = re.findall(r'<span class="single-tag[^"]*">([^<]+)</span>', tail)
            tag = ", ".join(t.strip() for t in tags if t.strip())[:40]

            chars.append({
                "name": alt, "slug": slug, "icon": icon,
                "tag": tag,
                "rarity": rar.group(1) if rar else "",
                "element": (el.group(1) if el else "").strip(),
                "role": roles.get(slug, "") or tag,
                "tier": raw.upper().replace("-", ""),
            })
        if chars:
            tiers.append({"tier": raw.upper().replace("-", ""), "chars": chars})
    return tiers


def parse_game8_gi():
    h = fetch(GAME8_GI)
    tiers = []
    for r in re.findall(r'<tr>(.*?)</tr>', h, re.S):
        tl = re.search(r'alt="((?:SS|S|A|B|C|D) Tier)"', r)
        if not tl:
            continue
        label = tl.group(1).replace(" Tier", "")
        pairs = re.findall(
            r'alt="Genshin - (.+?) (Main DPS|Sub-DPS|Support|DPS) Rank"'
            r'[^>]*data-src="(https://img\.game8\.co/[^"]+)"', r)
        chars, seen = [], set()
        for name, role, src in pairs:
            name = name.strip()
            if name in seen or name.lower() in SKIP:
                continue
            seen.add(name)
            chars.append({"name": name, "slug": "", "icon": src, "rarity": "",
                          "element": "", "role": role, "tier": label})
        if chars:
            tiers.append({"tier": label, "chars": chars})
    return tiers


def save_icons(slug, tiers):
    out_dir = BASE / "img" / "tier" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    n = 0
    for t in tiers:
        for c in t["chars"]:
            n += 1
            ext = ".webp" if c["icon"].endswith(".webp") else ".png"
            name = "%s-%03d%s" % (slug, n, ext)
            dest = out_dir / name
            if not dest.exists():
                try:
                    data = urllib.request.urlopen(
                        urllib.request.Request(c["icon"], headers=UA), timeout=22).read()
                    if len(data) > 500:
                        dest.write_bytes(data)
                    else:
                        continue
                except Exception:
                    continue
            c["local"] = "img/tier/%s/%s" % (slug, name)
    return sum(1 for t in tiers for c in t["chars"] if c.get("local"))


def char_html(c, slug):
    src = c.get("local") or c["icon"]
    meta = " &middot; ".join(x for x in [c.get("element"), c.get("role"),
                                         ("R" + c["rarity"]) if c.get("rarity") else ""] if x)
    return (
        '        <button type="button" class="tc-item"'
        ' data-name="%s" data-tier="%s" data-el="%s" data-role="%s"'
        ' data-rarity="%s" data-img="%s" data-slug="%s" data-game="%s">\n'
        '          <img src="%s" alt="%s" loading="lazy" decoding="async">\n'
        '          <span class="tc-name">%s</span>\n'
        '        </button>' % (
            esc(c["name"]), esc(c.get("tier", "")), esc(c.get("element", "")),
            esc(c.get("role", "")), esc(c.get("rarity", "")), esc(src),
            esc(c["slug"]), esc(GAME_SLUG.get(slug, "")), esc(src),
            esc(c["name"]), esc(c["name"])))


def tier_rows(tiers, slug):
    out = []
    for t in tiers:
        tier = t["tier"]
        items = "\n".join(char_html(c, slug) for c in t["chars"])
        out.append(
            '      <div class="tier-row" id="tier-%s-%s">\n'
            '        <div class="tier-tag" style="background:%s">%s</div>\n'
            '        <div class="tier-chars">\n%s\n        </div>\n'
            '      </div>' % (slug, tier, TIER_COLOR.get(tier, "#6e44ff"),
                               esc(TIER_LABEL.get(tier, tier)), items))
    return "\n".join(out)


def tier_section(tiers, slug, compact=False):
    """Section tier list untuk disisipkan ke halaman panduan."""
    nav = "".join(
        '<a href="#tier-%s-%s">%s</a>' % (slug, t["tier"], TIER_LABEL.get(t["tier"], t["tier"]))
        for t in tiers)
    total = sum(len(t["chars"]) for t in tiers)
    return (
        '      <section class="guide-block" id="tier-list">\n'
        '        <h2 class="section-title">&#127942; Tier List Karakter</h2>\n'
        '        <p>%d karakter dalam %d tier, dirangkum dari Prydwen Institute. '
        'Klik karakter untuk melihat detailnya.</p>\n'
        '        <nav class="page-nav tier-nav" aria-label="Navigasi tier">%s</nav>\n'
        '        <div class="tier-table">\n%s\n        </div>\n'
        '        <p class="tier-hint">Tier tinggi bukan berarti wajib. Peringkat bergantung '
        'komposisi tim dan berubah tiap patch.</p>\n'
        '      </section>' % (total, len(tiers), nav, tier_rows(tiers, slug)))


def build_game_page(slug, name, tiers, source_name, source_url):
    total = sum(len(t["chars"]) for t in tiers)
    nav = "".join(
        '<a href="#tier-%s-%s">%s</a>' % (slug, t["tier"], TIER_LABEL.get(t["tier"], t["tier"]))
        for t in tiers)
    return '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tier List %s &#8212; Starwise</title>
  <meta name="description" content="Tier list %s: peringkat %d karakter dari %s. Klik karakter untuk melihat element, role, dan rarity.">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="logo">Starwise</a>
%s
      <button class="menu-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </header>

  <main class="container">

    <nav class="breadcrumb" aria-label="Navigasi">
      <a href="games.html">Games</a>
      <span class="crumb-sep">/</span>
      <a href="tierlist.html">Tier List</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">%s</span>
    </nav>

    <div class="page-header">
      <h1>Tier List %s</h1>
      <p class="page-sub">%d karakter dalam %d tier. Sumber: %s. Klik karakter untuk detail.</p>
    </div>

    <nav class="page-nav tier-nav" aria-label="Navigasi tier">
%s
    </nav>

    <section class="section">
      <div class="tier-table">
%s
      </div>
      <p class="tier-hint">Tier tinggi bukan berarti wajib. Peringkat bisa berubah setelah patch.</p>
    </section>

    <section class="section">
      <h2 class="section-title">&#8505; Cara Membaca</h2>
      <ul class="tip-list">
        <li><strong>Tier atas bukan berarti wajib.</strong> Karakter tier tinggi paling efisien untuk konten sulit, tapi karakter bawah tetap bisa menyelesaikan sebagian besar konten.</li>
        <li><strong>Peringkat bergantung tim.</strong> Karakter bisa naik satu tier kalau dipasangkan dengan support yang tepat.</li>
        <li><strong>Meta berubah tiap patch.</strong> Karakter baru dan perubahan sistem menggeser posisi. Cek ulang setelah update besar.</li>
        <li><strong>Sumber: %s.</strong> Starwise tidak menghitung sendiri, hanya merangkum.</li>
      </ul>
    </section>

    <section class="section">
      <h2 class="section-title">&#128279; Lanjutkan</h2>
      <div class="card-grid">
        <a href="tierlist.html" class="card">
          <div class="card-body"><h3>Tier List Game Lain</h3><p>Bandingkan peringkat antar game.</p></div>
        </a>
        <a href="%s" class="card">
          <div class="card-body"><h3>Panduan Lengkap</h3><p>Pity, rotasi tim, dan tips farming.</p></div>
        </a>
      </div>
    </section>

    <p class="review-infobreak">
      Data diambil dari %s saat build. Peringkat bisa berubah setelah patch baru.
    </p>

  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>&copy; 2025 Starwise. Game, Anime &amp; Film.</p>
      <p>Konten untuk tujuan informasi &amp; hiburan.</p>
    </div>
  </footer>

  <script src="js/tier.js"></script>
  <script src="js/main.js"></script>
</body>
</html>
''' % (esc(name), esc(name), total, esc(source_name), NAV, esc(name), esc(name),
       total, len(tiers), esc(source_name), nav, tier_rows(tiers, slug),
       esc(source_name), GUIDE_MAP.get(slug, "games.html"), esc(source_name))


def build_index(results):
    cards = []
    for slug, name, n_tier, n_char in results:
        cards.append(
            '        <a href="tierlist-%s.html" class="tile">\n'
            '          <span class="tile-img"><img src="img/logo-%s.jpg" alt="%s" loading="lazy" decoding="async"></span>\n'
            '          <span class="tile-body">\n'
            '            <h3>Tier List %s</h3>\n'
            '            <p>%d karakter dalam %d tier. Klik karakter untuk detail.</p>\n'
            '            <span class="tile-tag">Lihat peringkat &rarr;</span>\n'
            '          </span>\n'
            '        </a>' % (slug, LOGO[slug], esc(name), esc(name), n_char, n_tier))

    return '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tier List &#8212; Starwise</title>
  <meta name="description" content="Tier list karakter game gacha: HSR, Genshin, ZZZ, Wuthering Waves, Endfield, dan NTE.">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="logo">Starwise</a>
%s
      <button class="menu-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </header>

  <main class="container">

    <nav class="breadcrumb" aria-label="Navigasi">
      <a href="games.html">Games</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">Tier List</span>
    </nav>

    <div class="page-header">
      <h1>Tier List</h1>
      <p class="page-sub">Peringkat karakter per game. Klik karakter untuk melihat element, role, dan rarity.</p>
    </div>

    <section class="section">
      <p class="section-intro">
        Pilih game untuk melihat tier list lengkapnya. Semua peringkat berasal dari
        Prydwen Institute dan Game8.
      </p>
      <div class="tile-grid">
%s
      </div>
    </section>

    <p class="review-infobreak">
      Starwise tidak menghitung tier list sendiri. Peringkat diambil dari
      Prydwen Institute (HSR, ZZZ, WuWa, Endfield, NTE) dan Game8 (Genshin Impact).
    </p>

  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>&copy; 2025 Starwise. Game, Anime &amp; Film.</p>
      <p>Konten untuk tujuan informasi &amp; hiburan.</p>
    </div>
  </footer>

  <script src="js/tier.js"></script>
  <script src="js/main.js"></script>
</body>
</html>
''' % (NAV, "\n".join(cards))


def main():
    results, data = [], {}

    for slug, (name, url, _) in PRYDWEN.items():
        try:
            tiers = parse_prydwen(url)
        except Exception as exc:
            print("%-10s GAGAL: %s" % (slug, exc))
            continue
        if not tiers:
            print("%-10s tidak ada tier" % slug)
            continue
        n_icon = save_icons(slug, tiers)
        (BASE / ("tierlist-%s.html" % slug)).write_text(
            build_game_page(slug, name, tiers, "Prydwen Institute", url), encoding="utf-8")
        n_char = sum(len(t["chars"]) for t in tiers)
        results.append((slug, name, len(tiers), n_char))
        data[slug] = tiers
        print("%-10s %d tier, %d karakter, %d ikon" % (slug, len(tiers), n_char, n_icon))
        time.sleep(0.8)

    try:
        gi = parse_game8_gi()
        if gi:
            n_icon = save_icons("genshin", gi)
            (BASE / "tierlist-genshin.html").write_text(
                build_game_page("genshin", "Genshin Impact", gi, "Game8", GAME8_GI),
                encoding="utf-8")
            n_char = sum(len(t["chars"]) for t in gi)
            results.append(("genshin", "Genshin Impact", len(gi), n_char))
            data["genshin"] = gi
            print("%-10s %d tier, %d karakter, %d ikon" % ("genshin", len(gi), n_char, n_icon))
    except Exception as exc:
        print("genshin GAGAL: %s" % exc)

    if not results:
        print("Tidak ada data.")
        return

    (BASE / "tierlist.html").write_text(build_index(results), encoding="utf-8")
    (BASE / "_tier_data.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print("\ntierlist.html: %d game" % len(results))
    print("_tier_data.json disimpan untuk penyisipan ke panduan")


if __name__ == "__main__":
    main()