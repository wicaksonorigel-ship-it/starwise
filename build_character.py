# -*- coding: utf-8 -*-
"""Bangun halaman build karakter Starwise, didesain mengikuti Prydwen.

Sumber data: Prydwen Institute (halaman karakter per game).
Untuk setiap karakter dihasilkan build-<game>-<slug>.html berisi
Light Cone/Weapon, Relic/Gear set, stat per slot, dan tim.

Jalankan: python build_character.py            (semua game)
          python build_character.py hsr        (satu game saja)
"""
import html
import json
import pathlib
import re
import sys
import time
import urllib.request

BASE = pathlib.Path(__file__).parent
UA = {"User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}

# slug -> (nama, path prydwen, judul label per section)
GAMES = {
    "hsr": ("Honkai: Star Rail", "star-rail",
            {"weapon": "Light Cone", "gear": "Relic Set", "stats": "Stat Utama"}),
    "zzz": ("Zenless Zone Zero", "zenless",
            {"weapon": "W-Engine", "gear": "Drive Disc", "stats": "Stat Utama"}),
    "wuthering": ("Wuthering Waves", "wuthering-waves",
                  {"weapon": "Weapon", "gear": "Echo Set", "stats": "Stat Utama"}),
    "endfield": ("Arknights: Endfield", "arknights-endfield",
                 {"weapon": "Weapon", "gear": "Gear", "stats": "Stat Utama"}),
    "nte": ("Neverness to Everness", "neverness-to-everness",
            {"weapon": "Arc", "gear": "Cartridge", "stats": "Stat Utama"}),
}

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

IMG_DIR = BASE / "img" / "build"


def esc(s):
    return html.escape(str(s), quote=True)


def fetch(url):
    return urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")


def grab(h, start, ends):
    i = h.find(start)
    if i < 0:
        return ""
    j = len(h)
    for e in ends:
        k = h.find(e, i + len(start))
        if k > 0:
            j = min(j, k)
    return h[i:j]


def parse_build(h):
    """Ambil weapon, gear, dan stat dari halaman karakter Prydwen.

    Tiap game memakai markup berbeda, jadi tiap bagian mencoba beberapa pola:
      HSR      : Best Light Cones / Best Relic Sets / Best Stats (stats-header)
      ZZZ      : Best W-Engines / Best Disk Drives / main-stats (Disk 4/5/6)
      WuWa     : Build / Echoes / ww-stat
      Endfield : Best Weapons / Best Gear
      NTE      : Best Arcs / Best Cartridges / Main Stats + Sub Stats
    """
    out = {"weapon": [], "gear": [], "stats": [], "substats": [], "teams": []}

    def names_in(seg):
        """Nama item: coba set-name, lalu name+rarity."""
        n = re.findall(r'<span class="[^"]*set-name[^"]*">([^<]+?)(?:<!--|<)', seg)
        if not n:
            n = re.findall(r'<span class="[^"]*name[^"]*rarity-\w[^"]*">([^<]+?)(?:<!--|<)', seg)
        if not n:
            n = re.findall(r'<span class="[^"]*cone-name[^"]*">([^<]+?)(?:<!--|<)', seg)
        if not n:
            # WuWa: <div class="ww-set-image Nama Set"><img ...>Nama Set</button>
            n = re.findall(r'<div class="ww-set-image[^"]*"[^>]*>.*?</div>([^<]+)</button>', seg, re.S)
        return list(dict.fromkeys(x.strip() for x in n if x.strip()))

    def pcts_in(seg):
        return re.findall(r'percentage[^"]*"><p>([\d.]+)%', seg)

    # ---------- WEAPON ----------
    for s, e in [("Best Light Cones", ["Best Relic Sets"]),
                 ("Best W-Engines", ["Best Disk Drives", "Best Drive Discs", "Best Teams"]),
                 ("Best Arcs", ["Best Cartridges"]),
                 ("Best Weapons", ["Best Gear", "Potentials Review"]),
                 ("Build", ["Gameplay and teams", "SD/DA Analytics", "Echoes"])]:
        seg = grab(h, s, e)
        if not seg:
            continue
        nm = names_in(seg)
        if nm:
            pc = pcts_in(seg)
            for i, n in enumerate(nm[:6]):
                out["weapon"].append({"name": n, "pct": pc[i] if i < len(pc) else ""})
            break

    # ---------- GEAR ----------
    for s, e in [("Best Relic Sets", ["Best Stats", "Calculations"]),
                 ("Best Disk Drives", ["Best Disk Drives Stats", "Best Teams", "Calculations"]),
                 ("Best Drive Discs", ["Best Teams", "Calculations"]),
                 ("Best Gear", ["Potentials Review", "Skill Priority"]),
                 ("Best Cartridges", ["Best Arcs"]),
                 ("Best Echo Sets", ["Best Echo Stats", "Gameplay and teams", "Calculations"]),
                 ("Echoes", ["Gameplay and teams", "Calculations"])]:
        seg = grab(h, s, e)
        if not seg:
            continue
        nm = names_in(seg)
        if nm:
            pc = pcts_in(seg)
            for i, n in enumerate(nm[:6]):
                out["gear"].append({"name": n, "pct": pc[i] if i < len(pc) else ""})
            break

    # ---------- STAT ----------
    # HSR: <div class="stats-header"><span>Body</span></div>
    i = h.find("Best Stats")
    if i > 0:
        seg = h[i:i + 12000]
        for m in re.finditer(
                r'<div class="stats-header"><span>([^<]+)</span></div>(.*?)'
                r'(?=<div class="flex-1">|<div class="stats-header">|$)', seg, re.S):
            slot, body = m.group(1).strip(), m.group(2)
            vals = [v.strip() for v in re.findall(r'<span>([A-Za-z%/\- ]{2,24})</span>', body)
                    if v.strip() and v.strip() not in ("=", slot)]
            if vals:
                out["stats"].append({"slot": slot, "values": list(dict.fromkeys(vals))[:4]})

    # ZZZ / WuWa / NTE: <div class="box"><div class="stats-inside"><strong>Disk 4</strong></div>
    #                    <div class="list-stats">CRIT Rate%</div>
    if not out["stats"]:
        for m in re.finditer(
                r'<div class="stats-inside"><strong[^>]*>([^<]+)</strong></div>'
                r'<div class="list-stats">([^<]+)</div>', h):
            out["stats"].append({"slot": m.group(1).strip(),
                                 "values": [m.group(2).strip()]})
    # WuWa: <div class="ww-stat"><img alt="ATK%"...><span>ATK%</span></div>
    if not out["stats"]:
        vals = re.findall(r'class="ww-stat"><img alt="([^"]+)"', h)
        if vals:
            out["stats"].append({"slot": "Stat", "values": list(dict.fromkeys(vals))[:6]})

    # NTE: Main Stats / Sub Stats heading
    if not out["stats"]:
        for m in re.finditer(
                r'<div class="stats-header"><span>([^<]+)</span></div>(.*?)'
                r'(?=<div class="stats-header">|</section>|$)', h, re.S):
            slot, body = m.group(1).strip(), m.group(2)
            vals = [v.strip() for v in re.findall(r'<span>([A-Za-z%/\- ]{2,24})</span>', body)
                    if v.strip()]
            if vals:
                out["stats"].append({"slot": slot, "values": list(dict.fromkeys(vals))[:4]})

    # NTE: <div class="stats-header"><span>Main Stats</span></div>
    #      <div class="stats"><p>Crit DMG &gt; Psyche DMG % &gt; ATK %</p></div>
    if not out["stats"]:
        for m in re.finditer(
                r'<div class="stats-header"><span>([^<]+)</span></div>'
                r'<div class="stats"><p>(.*?)</p>', h, re.S):
            slot = m.group(1).strip()
            vals = [html.unescape(v).strip()
                    for v in re.split(r'\s*&gt;\s*|\s*>\s*', m.group(2))
                    if v.strip()]
            if vals:
                out["stats"].append({"slot": slot, "values": vals[:6]})

    # Endfield: gear dari "Best Gear" -> single-row dengan nama di <span class="...name...">
    if not out["gear"]:
        seg = grab(h, "Best Gear", ["Potentials Review", "Skill Priority"])
        if seg:
            nm = re.findall(r'<span class="[^"]*name[^"]*">([^<]+?)(?:<!--|<)', seg)
            pc = re.findall(r'<span>([\d.]+)%</span>', seg)
            for i, n in enumerate(list(dict.fromkeys(x.strip() for x in nm if x.strip()))[:6]):
                out["gear"].append({"name": n, "pct": pc[i] if i < len(pc) else ""})

    # Endfield: stat dari bagian Attributes
    if not out["stats"]:
        seg = grab(h, "Attributes", ["Skills", "Talents"])
        if seg:
            vals = re.findall(r'<span class="[^"]*stat-name[^"]*">([^<]+)</span>', seg)
            if not vals:
                vals = re.findall(r'alt="([A-Za-z% ]{2,20})"[^>]*stat', seg)
            if vals:
                out["stats"].append({"slot": "Atribut", "values": list(dict.fromkeys(vals))[:8]})

    # ---------- SUBSTAT ----------
    m = re.search(r'<span>Substats:</span>\s*(?:<!-- -->)?([^<]+)', h)
    if m:
        out["substats"] = [x.strip() for x in m.group(1).split(">") if x.strip()][:6]
    if not out["substats"]:
        seg = grab(h, "Substats Priority", ["Calculations", "Review"])
        if seg:
            vals = [v.strip() for v in re.findall(r'<span>([A-Za-z%/\- ]{3,24})</span>', seg)
                    if v.strip() and v.strip() != "="]
            out["substats"] = list(dict.fromkeys(vals))[:6]

    # ---------- RINGKASAN ----------
    md = re.search(r'<meta name="description" content="([^"]+)"', h)
    out["summary"] = html.unescape(md.group(1))[:300] if md else ""

    return out


def stat_table(stats):
    if not stats:
        return '<p class="build-empty">Data stat belum tersedia untuk karakter ini.</p>'
    rows = []
    for s in stats:
        vals = " &middot; ".join(esc(v) for v in s["values"])
        rows.append(
            '        <div class="build-stat-row">\n'
            '          <span class="build-stat-slot">%s</span>\n'
            '          <span class="build-stat-val">%s</span>\n'
            '        </div>' % (esc(s["slot"]), vals))
    return '      <div class="build-stats">\n%s\n      </div>' % "\n".join(rows)


def rank_list(items, label, kind):
    if not items:
        return ('<p class="build-empty">Data %s belum tersedia untuk karakter ini.</p>'
                % esc(label.lower()))
    rows = []
    for i, it in enumerate(items[:6], 1):
        pct = ('<span class="build-pct">%s%%</span>' % esc(it["pct"])) if it.get("pct") else ""
        best = " build-best" if i == 1 else ""
        rows.append(
            '        <div class="build-rank%s">\n'
            '          <span class="build-rank-n">%d</span>\n'
            '          <span class="build-rank-name">%s</span>\n'
            '          %s\n'
            '        </div>' % (best, i, esc(it["name"]), pct))
    return '      <div class="build-ranks">\n%s\n      </div>' % "\n".join(rows)


def build_page(slug, game_name, c, source_url):
    labels = GAMES[slug][2]
    meta = " &middot; ".join(x for x in [c.get("element"), c.get("role"),
                                        ("R" + c["rarity"]) if c.get("rarity") else ""] if x)
    img = c.get("local") or ""
    tier_url = "tierlist-%s.html" % slug
    guide_url = "guide-%s.html" % {
        "hsr": "honkai-star-rail", "zzz": "zenless-zone-zero",
        "wuthering": "wuthering-waves", "endfield": "arknights-endfield",
        "nte": "neverness-to-everness"}[slug]

    return '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Build %s &#8212; %s &#8212; Starwise</title>
  <meta name="description" content="Build %s untuk %s: %s, %s, dan stat utama.">
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
      <a href="%s">Tier List</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">Build %s</span>
    </nav>

    <header class="build-head">
      <img class="build-avatar" src="%s" alt="%s" loading="eager" decoding="async">
      <div>
        <h1>%s</h1>
        <p class="build-meta">%s</p>
        <div class="build-badges">
          <span class="tm-badge tm-tier">Tier %s</span>
          %s
        </div>
      </div>
    </header>

    <p class="build-summary">%s</p>

    <nav class="page-nav">
      <a href="#weapon">%s</a>
      <a href="#gear">%s</a>
      <a href="#stats">%s</a>
      %s
    </nav>

    <section class="section build-block" id="weapon">
      <h2 class="section-title">&#9876; %s Terbaik</h2>
      <p class="build-note">Diurutkan dari yang paling kuat. Persentase menunjukkan performa relatif terhadap pilihan terbaik.</p>
%s
    </section>

    <section class="section build-block" id="gear">
      <h2 class="section-title">&#128142; %s Terbaik</h2>
      <p class="build-note">Set terbaik untuk karakter ini, diurutkan berdasarkan prioritas.</p>
%s
    </section>

    <section class="section build-block" id="stats">
      <h2 class="section-title">&#128202; %s</h2>
      <p class="build-note">Stat yang dicari pada tiap slot.</p>
%s
    </section>

    %s

    <section class="section">
      <h2 class="section-title">&#128279; Lanjutkan</h2>
      <div class="card-grid">
        <a href="%s" class="card">
          <div class="card-body"><h3>Tier List %s</h3><p>Lihat posisi karakter ini dan lainnya.</p></div>
        </a>
        <a href="%s" class="card">
          <div class="card-body"><h3>Panduan %s</h3><p>Pity, rotasi tim, dan tips farming.</p></div>
        </a>
        <a href="%s" class="card" target="_blank" rel="noopener">
          <div class="card-body"><h3>Halaman asli Prydwen</h3><p>Kalkulasi lengkap dan penjelasan detail.</p></div>
        </a>
      </div>
    </section>

    <p class="review-infobreak">
      Build ini dirangkum dari Prydwen Institute. Starwise tidak menghitung sendiri.
      Angka bisa berubah setelah patch atau karakter baru rilis.
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
''' % (
        esc(c["name"]), esc(game_name), esc(c["name"]), esc(game_name),
        esc(labels["weapon"]), esc(labels["gear"]), NAV, esc(tier_url), esc(c["name"]),
        esc(img), esc(c["name"]), esc(c["name"]), meta, esc(c.get("tier", "-")),
        ('<span class="tm-badge tm-el">%s</span>' % esc(c["element"])) if c.get("element") else "",
        esc(c.get("summary", "")),
        esc(labels["weapon"]), esc(labels["gear"]), esc(labels["stats"]),
        '<a href="#teams">Tim</a>' if c.get("teams") else "",
        esc(labels["weapon"]), rank_list(c.get("weapon"), labels["weapon"], "weapon"),
        esc(labels["gear"]), rank_list(c.get("gear"), labels["gear"], "gear"),
        esc(labels["stats"]), stat_table(c.get("stats")),
        ('''    <section class="section build-block" id="teams">
      <h2 class="section-title">&#128101; Tim yang Direkomendasikan</h2>
      <p class="build-note">Karakter yang sering dipasangkan bersama.</p>
      <div class="build-teams">
%s
      </div>
    </section>''' % "\n".join(
            '        <span class="build-team-chip">%s</span>' % esc(t)
            for t in c.get("teams", []))) if c.get("teams") else "",
        esc(tier_url), esc(game_name), esc(guide_url), esc(game_name), esc(source_url))


# urutan tier dari terbaik ke terburuk, untuk memilih satu tier saat
# sebuah karakter muncul di lebih dari satu tier.
TIER_ORDER = ["T0", "SS", "T05", "T0.5", "S", "T1", "T15", "T1.5", "A",
              "T2", "B", "T3", "C", "T4", "D", "T5", "0", "05", "1", "15", "2", "3", "4", "5"]


def tier_rank(t):
    try:
        return TIER_ORDER.index(t)
    except ValueError:
        return 999


def load_chars(slug):
    """Ambil karakter unik. Kalau satu karakter muncul di beberapa tier
    (mis. Anaxa di T1 dan T1.5), pakai tier terbaiknya supaya konsisten."""
    f = BASE / "_tier_data.json"
    if not f.exists():
        return []
    data = json.loads(f.read_text(encoding="utf-8"))
    tiers = data.get(slug, [])
    best = {}
    for t in tiers:
        for c in t["chars"]:
            key = c.get("slug") or c["name"]
            cur = best.get(key)
            if cur is None or tier_rank(t["tier"]) < tier_rank(cur.get("tier", "Z")):
                cc = dict(c)
                cc["tier"] = t["tier"]
                best[key] = cc
    return list(best.values())


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    total = 0

    for slug, (game_name, path, labels) in GAMES.items():
        if only and slug != only:
            continue
        chars = load_chars(slug)
        if not chars:
            print("%-10s tidak ada karakter di _tier_data.json" % slug)
            continue

        ok = 0
        for c in chars:
            cs = c.get("slug")
            if not cs:
                # fallback: generate slug dari nama (dipakai untuk game yang
                # tidak punya slug di data tier list, mis. Genshin)
                nm = c.get("name", "")
                cs = re.sub(r"[^a-z0-9]+", "-", nm.lower()).strip("-")
            if not cs:
                continue
            url = "https://www.prydwen.gg/%s/characters/%s" % (path, cs)
            try:
                h = fetch(url)
                c.update(parse_build(h))
                c["source"] = url
            except Exception as exc:
                print("   %-22s gagal: %s" % (cs, exc))
                continue
            out = BASE / ("build-%s-%s.html" % (slug, cs))
            out.write_text(build_page(slug, game_name, c, url), encoding="utf-8")
            ok += 1
            time.sleep(0.35)
        print("%-10s %d/%d build dibuat" % (slug, ok, len(chars)))
        total += ok

    print("\ntotal: %d halaman build" % total)


if __name__ == "__main__":
    main()