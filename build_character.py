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


def download_image(url, dest):
    """Unduh gambar ke dest, return True jika berhasil."""
    if not url:
        return False
    if dest.exists() and dest.stat().st_size > 1000:
        return True
    try:
        req = urllib.request.Request(url, headers=UA)
        data = urllib.request.urlopen(req, timeout=30).read()
        if len(data) < 500:
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def parse_skills(h):
    """Ambil skill: nama, tipe, deskripsi. Return list of dict.

    Setiap game pakai layout berbeda:
      HSR      : <p class="skill-name">Nama</p> + <p class="skill-type"> + skill-with-coloring
      ZZZ      : <p class="skill-name">Nama</p> + skill-info > skill-description
      ZZZ v2   : <div class="skill-title"><p class="skill-name">Nama</p>... + <a class="skill-description">Deskripsi
      WuWa     : <p class="ww-skill-name">Nama</p> + <p class="ww-skill-desc">Deskripsi
      Endfield : <p class="skill-name">Nama</p> + <div class="skill-description">
      NTE      : <p class="skill-name">Nama</p> + <div class="skill-with-coloring">
    """
    skills = []

    def clean(s):
        s = re.sub(r'<!--.*?-->', '', s, flags=re.S)   # hilangkan HTML comment
        s = re.sub(r'<[^>]+>', '', s)
        s = html.unescape(s).strip()
        return re.sub(r'\s+', ' ', s)

    # Ambil semua skill-name (boleh ada HTML comment di dalamnya)
    name_pat = re.compile(
        r'<p class="skill-name">(.*?)</p>', re.S)
    for m in name_pat.finditer(h):
        name_raw = m.group(1)
        # hapus HTML comment & tag di dalam nama
        name = clean(name_raw)

        i = m.end()
        stype = ""
        desc = ""

        # ---- TIPE ----
        t = re.search(
            r'<p class="skill-type">.*?<span class="type">([^<]+)</span>',
            h[i:i + 2000], re.S)
        if t:
            stype = clean(t.group(1))

        # ---- DESKRIPSI ----
        zz = re.search(
            r'<div class="skill-title">.*?<p class="skill-name">[^<]+</p>'
            r'.*?</div>\s*<div class="skill-info">.*?skill-description">(.*?)</div>',
            html.unescape(h[i:i + 30000]), re.S)
        if zz:
            desc = clean(zz.group(1))
        else:
            # skill-with-coloring (HSR)
            cur = re.search(
                r'<div class="skill-with-coloring[^"]*">(.*?)</div>',
                h[i:i + 20000], re.S)
            if cur:
                desc = clean(cur.group(1))
            else:
                # Endfield: <div class="skill-description">
                for pat in [
                    r'<div class="skill-description">(.*?)</div>',
                    r'<p class="description">(.*?)</p>',
                    r'<div class="desc">(.*?)</div>',
                    r'<p class="skill-desc">(.*?)</p>',
                ]:
                    cur = re.search(pat, html.unescape(h[i:i + 30000]), re.S)
                    if cur:
                        desc = clean(cur.group(1))
                        break
                else:
                    # ZZZ v2: <a class="skill-description">
                    zz2 = re.search(
                        r'<div class="skill-info">.*?skill-description">(.*?)</div>',
                        html.unescape(h[i:i + 30000]), re.S)
                    if zz2:
                        desc = clean(zz2.group(1))
                    else:
                        # WuWa: <p class="ww-skill-desc">
                        ww = re.search(
                            r'<p class="ww-skill-desc">(.*?)</p>',
                            html.unescape(h[i:i + 30000]), re.S)
                        if ww:
                            desc = clean(ww.group(1))

        skills.append({"name": name, "type": stype, "desc": desc[:500]})
    return skills[:8]


def parse_team(h):
    """Ambil tim: nama karakter + icon URL. Return list of dict."""
    team = []
    # cari section Teams/Synergy
    for kw in ['Synergy', 'Teams', 'teams']:
        i = h.find(kw)
        if i < 0:
            continue
        seg = h[i:i + 6000]
        # pola: <img alt="Nama" ... src="...characters/slug_icon.webp">
        for m in re.finditer(
                r'<img alt="([^"]{2,30})"[^>]*src="([^"]*characters/[^"]*_icon[^"]*)"',
                seg):
            name = html.unescape(m.group(1).strip())
            icon = m.group(2)
            if name and not name.lower().startswith(('quantum', 'fire', 'ice', 'wind', 'lightning', 'physical', 'imaginary')):
                team.append({"name": name, "icon": icon})
        if team:
            break
    # dedupe
    seen = set()
    out = []
    for t in team:
        if t["name"] not in seen:
            seen.add(t["name"])
            out.append(t)
    return out[:6]


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
    out = {"weapon": [], "gear": [], "stats": [], "substats": [], "teams": [], "skills": [], "image": "", "slug": ""}

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

    # ---------- SKILL ----------
    out["skills"] = parse_skills(h)

    # ---------- TEAM ----------
    out["team"] = parse_team(h)

    # ---------- GAMBAR ----------
    full = re.findall(r'src="(https://cdn\.prydwen\.gg/images/[^"]*_full[^"]*)"', h)
    card = re.findall(r'src="(https://cdn\.prydwen\.gg/images/[^"]*_card[^"]*)"', h)
    out["img_full"] = full[0] if full else ""
    out["img_card"] = card[0] if card else ""

    # ---------- RINGKASAN ----------
    md = re.search(r'<meta name="description" content="([^"]+)"', h)
    out["summary"] = html.unescape(md.group(1))[:300] if md else ""

    return out


def fullimg_html(c):
    src = c.get("img_local") or c.get("img_full") or c.get("img_card") or ""
    if not src:
        return ""
    return ('    <div class="build-fullimg">\n'
            '      <img src="%s" alt="%s" loading="lazy">\n'
            '    </div>' % (esc(src), esc(c.get("name", ""))))


def skills_html(c):
    skills = c.get("skills", [])
    if not skills:
        return '<p class="build-empty">Data skill belum tersedia.</p>'
    rows = []
    for s in skills:
        rows.append(
            '        <div class="build-skill-card">\n'
            '          <div class="build-skill-head">\n'
            '            <span class="build-skill-type">%s</span>\n'
            '            <span class="build-skill-name">%s</span>\n'
            '          </div>\n'
            '          <p class="build-skill-desc">%s</p>\n'
            '        </div>' % (esc(s.get("type", "")), esc(s.get("name", "")), esc(s.get("desc", ""))))
    return "\n".join(rows)


def team_section(c):
    team = c.get("team", [])
    if not team:
        return ""
    chips = []
    for m in team:
        icon = m.get("icon_local") or m.get("icon", "")
        name = esc(m.get("name", ""))
        if icon:
            chips.append(
                '          <div class="build-team-card">\n'
                '            <img src="%s" alt="%s" loading="lazy">\n'
                '            <span>%s</span>\n'
                '          </div>' % (esc(icon), name, name))
        else:
            chips.append(
                '          <div class="build-team-card">\n'
                '            <span>%s</span>\n'
                '          </div>' % name)
    return ('    <section class="section build-block" id="team">\n'
            '      <h2 class="section-title">&#128101; Tim yang Direkomendasikan</h2>\n'
            '      <p class="build-note">Karakter yang sering dipasangkan bersama %s.</p>\n'
            '      <div class="build-team-grid">\n%s\n      </div>\n'
            '    </section>' % (esc(c.get("name", "")), "\n".join(chips)))


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


def rank_list(items, label):
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
    img = c.get("img_full") or c.get("img_card") or c.get("local") or ""
    tier_url = "tierlist-%s.html" % slug
    guide_url = "guide-%s.html" % {
        "hsr": "honkai-star-rail", "zzz": "zenless-zone-zero",
        "wuthering": "wuthering-waves", "endfield": "arknights-endfield",
        "nte": "neverness-to-everness"}[slug]

    sh = skills_html(c)
    ts = team_section(c)

    return '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Build %(cname)s &#8212; %(gname)s &#8212; Starwise</title>
  <meta name="description" content="Build %(cname)s untuk %(gname)s: %(wlabel)s, %(glabel)s, dan stat utama.">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="logo">Starwise</a>
%(nav)s
      <button class="menu-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </header>

  <main class="container">

    <nav class="breadcrumb" aria-label="Navigasi">
      <a href="games.html">Games</a>
      <span class="crumb-sep">/</span>
      <a href="%(tier)s">Tier List</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">Build %(cname)s</span>
    </nav>

    <header class="build-head">
      <img class="build-avatar" src="%(img)s" alt="%(cname)s" loading="eager" decoding="async">
      <div>
        <h1>%(cname)s</h1>
        <p class="build-meta">%(meta)s</p>
        <div class="build-badges">
          <span class="tm-badge tm-tier">Tier %(tier)s</span>
          %(el)s
        </div>
      </div>
    </header>

    <p class="build-summary">%(summary)s</p>

    %(fullimg)s

    <nav class="page-nav">
      <a href="#skill">Skill</a>
      <a href="#weapon">%(wlabel)s</a>
      <a href="#gear">%(glabel)s</a>
      <a href="#stats">%(slabel)s</a>
      %(teamnav)s
    </nav>

    <section class="section build-block" id="skill">
      <h2 class="section-title">&#128269; Detail Skill</h2>
      <p class="build-note">Semua skill aktif dan pasif beserta efeknya.</p>
      <div class="build-skills">
%(sh)s
      </div>
    </section>

    <section class="section build-block" id="weapon">
      <h2 class="section-title">&#9876; %(wlabel)s Terbaik</h2>
      <p class="build-note">Diurutkan dari yang paling kuat. Persentase menunjukkan performa relatif terhadap pilihan terbaik.</p>
%(w)s
    </section>

    <section class="section build-block" id="gear">
      <h2 class="section-title">&#128142; %(glabel)s Terbaik</h2>
      <p class="build-note">Set terbaik untuk karakter ini, diurutkan berdasarkan prioritas.</p>
%(g)s
    </section>

    <section class="section build-block" id="stats">
      <h2 class="section-title">&#128202; %(slabel)s</h2>
      <p class="build-note">Stat yang dicari pada tiap slot.</p>
%(st)s
    </section>

    %(ts)s

    <section class="section">
      <h2 class="section-title">&#128279; Lanjutkan</h2>
      <div class="card-grid">
        <a href="%(tier)s" class="card">
          <div class="card-body"><h3>Tier List %(gname)s</h3><p>Lihat posisi karakter ini dan lainnya.</p></div>
        </a>
        <a href="%(guide)s" class="card">
          <div class="card-body"><h3>Panduan %(gname)s</h3><p>Pity, rotasi tim, dan tips farming.</p></div>
        </a>
        <a href="%(src)s" class="card" target="_blank" rel="noopener">
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
''' % {
        "cname": esc(c["name"]), "gname": esc(game_name),
        "wlabel": esc(labels["weapon"]), "glabel": esc(labels["gear"]),
        "slabel": esc(labels["stats"]),
        "nav": NAV, "tier": esc(tier_url), "guide": esc(guide_url),
        "img": esc(c.get("img_local") or img),
        "fullimg": fullimg_html(c), "meta": meta, "tier": esc(c.get("tier", "-")),
        "el": ('<span class="tm-badge tm-el">%s</span>' % esc(c["element"])) if c.get("element") else "",
        "summary": esc(c.get("summary", "")),
        "teamnav": '<a href="#team">Tim</a>' if c.get("team") else "",
        "w": rank_list(c.get("weapon"), labels["weapon"]),
        "g": rank_list(c.get("gear"), labels["gear"]),
        "st": stat_table(c.get("stats")),
        "sh": sh, "ts": ts, "src": esc(source_url),
    }


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


def update_tier_data_with_skills():
    """Parse skill dari Prydwen, save skills to _tier_data.json.

    Each character gets:
      c["skills"] = [{"name": ..., "type": ..., "desc": ...}, ...]
    """
    d = BASE / "_tier_data.json"
    if not d.exists():
        print("No _tier_data.json found — skipping skill update")
        return
    data = json.loads(d.read_text(encoding="utf-8"))
    for slug in GAMES:
        path = GAMES[slug][1]
        for t in data.get(slug, []):
            for c in t["chars"]:
                url = f"https://www.prydwen.gg/{path}/characters/{c['slug']}"
                h = ""
                try:
                    h = fetch(url)
                except Exception:
                    pass
                c["skills"] = parse_skills(h)
    d.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Updated _tier_data.json with skill data for {len(GAMES)} games")


def main():
    update_tier_data_with_skills()
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
            slug_file = cs.replace("/", "-")
            # download gambar full body
            img_url = c.get("img_full") or c.get("img_card") or ""
            if img_url:
                dest = IMG_DIR / slug / ("%s_full.webp" % cs)
                if download_image(img_url, dest):
                    c["img_local"] = "img/build/%s/%s_full.webp" % (slug, cs)
            # download ikon anggota tim
            for idx, m in enumerate(c.get("team", [])):
                ic = m.get("icon", "")
                if ic:
                    d2 = IMG_DIR / slug / ("team_%s_%d.webp" % (cs, idx))
                    if download_image(ic, d2):
                        m["icon_local"] = "img/build/%s/team_%s_%d.webp" % (slug, cs, idx)
            ok += 1
            time.sleep(0.35)
        print("%-10s %d/%d build dibuat" % (slug, ok, len(chars)))
        total += ok

    print("\ntotal: %d halaman build" % total)


if __name__ == "__main__":
    main()