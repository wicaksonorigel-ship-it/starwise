# -*- coding: utf-8 -*-
"""Bangun halaman tier list per game Starwise.

Sumber:
  - Prydwen Institute: HSR, Zenless Zone Zero, Wuthering Waves,
    Arknights: Endfield, Neverness to Everness
  - Game8: Genshin Impact

Ikon karakter diunduh ke img/tier/<game>/ supaya tidak hotlink.

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

# slug -> (nama tampilan, url prydwen, segmen path icon)
PRYDWEN = {
    "hsr": ("Honkai: Star Rail", "https://www.prydwen.gg/star-rail/tier-list/",
            "honkai-star-rail", "characters"),
    "zzz": ("Zenless Zone Zero", "https://www.prydwen.gg/zenless/tier-list/",
            "zenless-zone-zero", "agents"),
    "wuthering": ("Wuthering Waves", "https://www.prydwen.gg/wuthering-waves/tier-list/",
                  "wuthering-waves", "characters"),
    "endfield": ("Arknights: Endfield", "https://www.prydwen.gg/arknights-endfield/tier-list",
                 "arknights-endfield", "characters"),
    "nte": ("Neverness to Everness", "https://www.prydwen.gg/neverness-to-everness/tier-list",
            "neverness-to-everness", "characters"),
}

GAME8_GI = "https://game8.co/games/Genshin-Impact/archives/297465"

# warna per tier
TIER_COLOR = {
    "T0": "#ef4444", "T05": "#f97316", "T0.5": "#f97316",
    "T1": "#eab308", "T15": "#84cc16", "T1.5": "#84cc16",
    "T2": "#22c55e", "T3": "#14b8a6", "T4": "#3b82f6", "T5": "#6366f1",
    "SS": "#ef4444", "S": "#f97316", "A": "#eab308", "B": "#22c55e",
    "C": "#3b82f6", "D": "#6366f1",
}

TIER_LABEL = {
    "T0": "T0", "T05": "T0.5", "T15": "T1.5",
}

NAV = '''      <nav class="main-nav">
        <a href="index.html">Home</a>
        <a href="games.html">Games</a>
        <a href="anime.html">Anime</a>
        <a href="movies.html">Film</a>
        <a href="news.html">Berita</a>
        <a href="database.html">Database</a>
        <a href="streaming.html">Streaming</a>
        <a href="download.html">Download</a>
      </nav>'''

SKIP_NAMES = {
    "quantum", "physical", "fire", "ice", "lightning", "wind", "imaginary",
    "ether", "electric", "frost", "aero", "glacio", "fusion", "havoc",
    "spectro", "pyro", "hydro", "cryo", "dendro", "geo", "anemo", "electro",
}


def esc(s):
    return html.escape(s, quote=True)


def norm_tier(raw):
    t = raw.upper().replace("-", "")
    return t


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")


def parse_prydwen(url):
    h = fetch(url)
    parts = re.split(r'<div class="tier-rating t-([\w.]+)">', h)
    tiers = []
    for i in range(1, len(parts), 2):
        raw = parts[i]
        body = parts[i + 1]
        pairs = re.findall(
            r'<img alt="([^"]+)"[^>]*src="(https://cdn\.prydwen\.gg/images/[^"]+?)"', body)
        chars = []
        seen = set()
        for alt, src in pairs:
            if alt.lower() in SKIP_NAMES or alt in seen:
                continue
            # Hanya gambar karakter: path mengandung /characters/ atau /agents/
            # (sebagian game pakai akhiran _icon, sebagian tidak).
            if not re.search(r'/(?:characters|agents)/', src):
                continue
            if "/icons/" in src or "/categories/" in src:
                continue
            seen.add(alt)
            chars.append({"name": alt, "icon": src})
        if chars:
            tiers.append({"tier": norm_tier(raw), "chars": chars})
    return tiers


def parse_game8_gi():
    """Game8 menaruh tiap tier dalam <tr> dengan alt="SS Tier" dsb,
    dan nama karakter di alt="Genshin - <Nama> <Role> Rank"."""
    h = fetch(GAME8_GI)
    tiers = []
    for r in re.findall(r'<tr>(.*?)</tr>', h, re.S):
        tl = re.search(r'alt="((?:SS|S|A|B|C|D) Tier)"', r)
        if not tl:
            continue
        label = tl.group(1).replace(" Tier", "")
        pairs = re.findall(
            r'alt="Genshin - (.+?) (?:Main DPS|Sub-DPS|Support|DPS) Rank"'
            r'[^>]*data-src="(https://img\.game8\.co/[^"]+)"', r)
        if not pairs:
            pairs = re.findall(
                r'alt="Genshin - (.+?) [A-Za-z\- ]*Rank"[^>]*data-src="([^"]+)"', r)
        chars = []
        seen = set()
        for name, src in pairs:
            name = name.strip()
            if name in seen or name.lower() in SKIP_NAMES:
                continue
            seen.add(name)
            chars.append({"name": name, "icon": src})
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


def tier_block(t):
    tier = t["tier"]
    color = TIER_COLOR.get(tier, "#6e44ff")
    label = TIER_LABEL.get(tier, tier)
    items = []
    for c in t["chars"]:
        src = c.get("local") or c["icon"]
        items.append(
            '        <span class="tc-item" title="%s">\n'
            '          <img src="%s" alt="%s" loading="lazy" decoding="async">\n'
            '          <span class="tc-name">%s</span>\n'
            '        </span>' % (esc(c["name"]), esc(src), esc(c["name"]), esc(c["name"])))
    return (
        '      <div class="tier-row">\n'
        '        <div class="tier-tag" style="background:%s">%s</div>\n'
        '        <div class="tier-chars">\n%s\n        </div>\n'
        '      </div>' % (color, esc(label), "\n".join(items)))


def build_game(slug, name, tiers, source_name, source_url):
    total = sum(len(t["chars"]) for t in tiers)
    rows = "\n".join(tier_block(t) for t in tiers)
    tier_nav = "".join(
        '<a href="#tier-%s-%s">%s</a>' % (slug, t["tier"], TIER_LABEL.get(t["tier"], t["tier"]))
        for t in tiers)

    return '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tier List %s &#8212; Starwise</title>
  <meta name="description" content="Tier list %s: peringkat karakter dari %s.">
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
      <p class="page-sub">%d karakter dalam %d tier. Sumber peringkat: %s.</p>
    </div>

    <nav class="page-nav tier-nav" aria-label="Navigasi tier">
%s
    </nav>

    <section class="section">
      <div class="tier-table">
%s
      </div>
    </section>

    <section class="section">
      <div class="tier-note">
        <h2 class="section-title">&#8505; Cara Membaca</h2>
        <ul class="tip-list">
          <li><strong>Tier atas bukan berarti wajib.</strong> Karakter tier tinggi biasanya paling efisien untuk konten sulit, tapi karakter tier bawah tetap bisa menyelesaikan sebagian besar konten.</li>
          <li><strong>Peringkat bergantung tim.</strong> Sebuah karakter bisa naik satu tier kalau dipasangkan dengan support yang tepat.</li>
          <li><strong>Meta berubah tiap patch.</strong> Karakter baru dan perubahan sistem bisa menggeser posisi. Cek ulang setelah update besar.</li>
          <li><strong>Sumber peringkat: %s.</strong> Starwise tidak menghitung sendiri, hanya merangkum dari sana.</li>
        </ul>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128279; Lanjutkan</h2>
      <div class="card-grid">
        <a href="tierlist.html" class="card">
          <div class="card-body">
            <h3>Tier List Game Lain</h3>
            <p>Bandingkan peringkat karakter antar game.</p>
          </div>
        </a>
        <a href="games.html" class="card">
          <div class="card-body">
            <h3>Panduan Lengkap</h3>
            <p>Pity, rotasi tim, dan tips farming tiap game.</p>
          </div>
        </a>
      </div>
    </section>

    <p class="review-infobreak">
      Data tier list diambil dari %s pada saat build. Peringkat bisa berubah
      setelah patch baru, jadi anggap ini sebagai ringkasan, bukan patokan mutlak.
    </p>

  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>&copy; 2025 Starwise. Game, Anime &amp; Film.</p>
      <p>Konten untuk tujuan informasi &amp; hiburan.</p>
    </div>
  </footer>

  <script src="js/main.js"></script>
</body>
</html>
''' % (esc(name), esc(name), esc(source_name), NAV, esc(name), esc(name),
       total, len(tiers), esc(source_name), tier_nav, rows, esc(source_name),
       esc(source_name))


def build_index(results):
    cards = []
    for slug, name, n_tier, n_char, logo in results:
        cards.append(
            '        <a href="tierlist-%s.html" class="tile">\n'
            '          <span class="tile-img"><img src="%s" alt="%s" loading="lazy" decoding="async"></span>\n'
            '          <span class="tile-body">\n'
            '            <h3>Tier List %s</h3>\n'
            '            <p>%d karakter dalam %d tier.</p>\n'
            '            <span class="tile-tag">Lihat peringkat &rarr;</span>\n'
            '          </span>\n'
            '        </a>' % (slug, esc(logo), esc(name), esc(name), n_char, n_tier))

    return '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tier List &#8212; Starwise</title>
  <meta name="description" content="Tier list karakter untuk game gacha populer: HSR, Genshin, ZZZ, Wuthering Waves, Endfield, dan NTE.">
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
      <p class="page-sub">Peringkat karakter per game, dirangkum dari Prydwen Institute dan Game8.</p>
    </div>

    <section class="section">
      <p class="section-intro">
        Pilih game untuk melihat tier list lengkapnya. Semua peringkat berasal dari
        sumber pihak ketiga yang kami sebutkan di tiap halaman.
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

  <script src="js/main.js"></script>
</body>
</html>
''' % (NAV, "\n".join(cards))


def main():
    results = []

    for slug, (name, url, cdn_path, kind) in PRYDWEN.items():
        try:
            tiers = parse_prydwen(url)
        except Exception as exc:
            print("%-10s GAGAL ambil: %s" % (slug, exc))
            continue
        if not tiers:
            print("%-10s tidak ada tier terdeteksi" % slug)
            continue
        n_icon = save_icons(slug, tiers)
        out = BASE / ("tierlist-%s.html" % slug)
        out.write_text(build_game(slug, name, tiers, "Prydwen Institute", url),
                       encoding="utf-8")
        n_char = sum(len(t["chars"]) for t in tiers)
        results.append((slug, name, len(tiers), n_char, "img/logo-%s.jpg" % {
            "hsr": "hsr", "zzz": "zzz", "wuthering": "ww",
            "endfield": "endfield", "nte": "nte"}[slug]))
        print("%-10s %d tier, %d karakter, %d ikon" % (slug, len(tiers), n_char, n_icon))
        time.sleep(0.8)

    # Genshin dari Game8
    try:
        gi = parse_game8_gi()
        if gi:
            n_icon = save_icons("genshin", gi)
            out = BASE / "tierlist-genshin.html"
            out.write_text(build_game("genshin", "Genshin Impact", gi, "Game8", GAME8_GI),
                           encoding="utf-8")
            n_char = sum(len(t["chars"]) for t in gi)
            results.append(("genshin", "Genshin Impact", len(gi), n_char, "img/logo-gi.jpg"))
            print("%-10s %d tier, %d karakter, %d ikon" % ("genshin", len(gi), n_char, n_icon))
        else:
            print("genshin  tidak ada tier terdeteksi dari Game8")
    except Exception as exc:
        print("genshin  GAGAL: %s" % exc)

    if not results:
        print("Tidak ada data tier list.")
        return

    (BASE / "tierlist.html").write_text(build_index(results), encoding="utf-8")
    (BASE / "_tier_raw.json").write_text(
        json.dumps([{"slug": r[0], "tiers": r[2], "chars": r[3]} for r in results],
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print("\ntierlist.html dibuat dengan %d game" % len(results))


if __name__ == "__main__":
    main()