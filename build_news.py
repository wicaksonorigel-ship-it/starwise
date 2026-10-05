# -*- coding: utf-8 -*-
"""Generator halaman berita Starwise.

Menarik berita terkini per game dari Google News RSS, menyaring yang relevan,
lalu menulis news.html. Jalankan ulang berkala untuk menyegarkan:

    python build_news.py
"""
import datetime
import html as H
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

BASE = pathlib.Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120"}

GAMES = [
    ("Wuthering Waves", "Wuthering Waves", "ww"),
    ("Genshin Impact", "Genshin Impact", "gi"),
    ("Honkai: Star Rail", "Honkai Star Rail", "hsr"),
    ("Zenless Zone Zero", "Zenless Zone Zero", "zzz"),
    ("Arknights: Endfield", "Arknights Endfield", "endfield"),
    ("Neverness to Everness", "Neverness to Everness", "nte"),
    ("Marvel", "Marvel Studios", "marvel"),
]

CHANNELS = [
    ("ww", "@WutheringWaves", "Wuthering Waves", "Kuro Games", "Trailer, Resonator showcase, gameplay"),
    ("gi", "@GenshinImpact", "Genshin Impact", "HoYoverse", "Trailer karakter, anniversary, event"),
    ("hsr", "@HonkaiStarRail", "Honkai: Star Rail", "HoYoverse", "Character trailer, event preview"),
    ("zzz", "@ZZZ_Official", "Zenless Zone Zero", "HoYoverse", "Character demo, story video"),
    ("endfield", "@arknightsendfieldEN", "Arknights: Endfield", "Gryphline", "Cutscene, update info"),
    ("nte", "@NTE_Official", "Neverness to Everness", "Perfect World", "Combat showcase, character PV"),
    ("marvel", "@marvel", "Marvel Entertainment", "Marvel Studios", "Trailer film MCU, special look"),
    ("muse", "@MuseIndonesia", "Muse Indonesia", "Channel anime Indonesia", "Anime recap dan mw"),
]

MARVEL_RE = re.compile(
    r"marvel|avengers|doomsday|spider-?man|thanos|multiverse|iron ?man", re.I)

RELEVANT_RE = re.compile(
    r"\b(version|ver\.|patch|update|release|launch|rilis|announce|trailer|teaser|character|"
    r"banner|wish|convene|warp|gacha|event|code|livestream|live stream|guide|tier|build|"
    r"review|rating|ps5|playstation|xbox|switch|mobile|dlc|collab|collaboration|roadmap|"
    r"schedule|maintenance|compensation|reveal|confirmed|rumor|leak|datamine|playable|"
    r"demo|beta|spinoff|sequel|ending|story|plot)\b", re.I)

NOISE_RE = re.compile(
    r"\b(box office|grossing|surpass|highest-?grossing|avatar \(2009\)|"
    r"passed away|obituary|retrospective|best deals|black friday|prime day|"
    r"discount|deals of the|where to (buy|watch))\b", re.I)

# Sumber aggregator yang tidak informatif sebagai atribusi.
GENERIC_SRC_RE = re.compile(
    r"^(youtube|facebook|twitter|x\.com|instagram|reddit|tiktok|weibo|zhihu)$", re.I)

# Berita merchandise (figure, merch, physical product) bukan berita patch.
MERCH_RE = re.compile(
    r"\b(figma|figure|action figure|s\.h\.figma|prototype|merch|merchandise|"
    r"blok prototype|kotak plastik|goods)\b", re.I)

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
         "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

MAX_AGE_DAYS = 45
PER_GAME = 12


def fetch(query):
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote('"%s"' % query)
           + "&hl=en-US&gl=US&ceid=US:en")
    req = urllib.request.Request(url, headers=UA)
    root = ET.fromstring(urllib.request.urlopen(req, timeout=25).read())
    out = []
    for item in root.findall(".//item"):
        src = item.find("source")
        pub = item.findtext("pubDate") or ""
        try:
            ts = parsedate_to_datetime(pub).timestamp()
        except Exception:
            ts = 0
        desc = item.findtext("description") or ""
        desc = re.sub(r"<[^>]+>", "", H.unescape(desc))[:200]
        out.append({
            "title": item.findtext("title") or "",
            "src": src.text if src is not None else "",
            "ts": ts,
            "link": item.findtext("link") or "",
            "desc": desc,
        })
    return out


def collect():
    cutoff = (datetime.datetime.now(datetime.timezone.utc).timestamp()
              - MAX_AGE_DAYS * 86400)
    items = []
    for label, query, _ in GAMES:
        for it in fetch(query):
            if label == "Marvel" and not MARVEL_RE.search(it["title"]):
                continue
            if it["ts"] < cutoff:
                continue
            blob = it["title"] + " " + it["desc"]
            if NOISE_RE.search(blob) or not RELEVANT_RE.search(it["title"]):
                continue
            if GENERIC_SRC_RE.match(it["src"].strip()):
                continue
            if MERCH_RE.search(it["title"]):
                continue
            it["game"] = label
            items.append(it)

    seen, uniq = set(), []
    for it in sorted(items, key=lambda x: x["ts"], reverse=True):
        key = re.sub(r"\W+", "", it["title"].lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(it)
    return uniq


def fmt_date(ts):
    dt = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
    return "%d %s %d" % (dt.day, BULAN[dt.month - 1], dt.year)


def news_row(it):
    desc = re.sub(r"\s+", " ", it["desc"]).strip()
    return (
        '          <a class="news-row" href="%s" target="_blank" rel="noopener">\n'
        '            <span class="news-row-body">\n'
        '              <strong>%s</strong>\n'
        '              <span class="news-row-desc">%s</span>\n'
        '              <span class="news-row-meta">%s &middot; %s</span>\n'
        '            </span>\n'
        '          </a>'
        % (H.escape(it["link"]), H.escape(it["title"]), H.escape(desc),
           H.escape(it["src"] or "Sumber tidak diketahui"), fmt_date(it["ts"])))


def channel_card(key, handle, name, dev, desc):
    return (
        '        <article class="channel-card">\n'
        '          <a href="https://www.youtube.com/%s" target="_blank" rel="noopener">\n'
        '            <span class="channel-avatar"><img src="img/yt-%s.jpg" alt="%s" loading="lazy" decoding="async"></span>\n'
        '            <span class="channel-meta">\n'
        '              <strong>%s</strong>\n'
        '              <span class="channel-dev">%s</span>\n'
        '              <span class="channel-desc">%s</span>\n'
        '              <span class="channel-link">Buka channel &rarr;</span>\n'
        '            </span>\n'
        '          </a>\n'
        '        </article>'
        % (handle, key, H.escape(name), H.escape(name), H.escape(dev), H.escape(desc)))


def build(items):
    sections = []
    for label, _, key in GAMES:
        group = [i for i in items if i["game"] == label][:PER_GAME]
        if not group:
            continue
        slug = "berita-" + re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
        rows = "\n".join(news_row(i) for i in group)
        sections.append(
            '    <section class="section" id="%s">\n'
            '      <header class="section-head">\n'
            '        <h2 class="section-title">'
            '<img class="section-logo" src="img/yt-%s.jpg" alt="">'
            '<span class="section-title-text">%s</span></h2>\n'
            '        <span class="news-count">%d berita</span>\n'
            '      </header>\n'
            '      <div class="news-list" data-game="%s">\n%s\n      </div>\n'
            '    </section>'
            % (slug, key, H.escape(label), len(group), H.escape(label), rows))

    channels = "\n".join(channel_card(*c) for c in CHANNELS)

    total = sum(s.count('class="news-row"') for s in sections)
    newest = max((i["ts"] for i in items), default=0)
    updated = fmt_date(newest) if newest else "-"

    html = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Berita &mdash; Starwise</title>
  <meta name="description" content="Berita terkini per game: patch, karakter baru, event, dan pengumuman resmi dari berbagai sumber.">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="logo">Starwise</a>
      <nav class="main-nav">
        <a href="index.html">Home</a>
        <a href="games.html">Games</a>
        <a href="anime.html">Anime</a>
        <a href="movies.html">Film</a>
        <a href="news.html" class="active">Berita</a>
        <a href="database.html">Database</a>
        <a href="streaming.html">Streaming</a>
        <a href="download.html">Download</a>
      </nav>
      <button class="menu-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </header>

  <main class="container">

    <nav class="breadcrumb" aria-label="Navigasi">
      <a href="index.html">Home</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">Berita</span>
    </nav>

    <div class="page-header">
      <h1>Berita Terkini</h1>
      <p class="page-sub">Patch, karakter baru, event, dan pengumuman resmi tiap game.</p>
    </div>

    <section class="section news-status">
      <div class="status-bar">
        <span class="status-item"><b>%(total)d</b> berita</span>
        <span class="status-item">Terbaru: <b>%(updated)s</b></span>
        <span class="status-item">Rentang: <b>%(days)d hari terakhir</b></span>
        <button id="news-refresh" class="btn btn-small" type="button">Muat berita terbaru</button>
        <span id="news-status" class="status-note"></span>
      </div>

      <div class="filter-bar" style="margin-top:14px">
        <label for="news-game" class="filter-label">Filter game</label>
        <select id="news-game" class="filter-input">
          <option value="">Semua game</option>
%(options)s
        </select>
        <span id="news-shown" class="filter-count"></span>
      </div>
    </section>

%(sections)s

    <section class="section">
      <h2 class="section-title">&#9654; Channel YouTube Resmi</h2>
      <p class="section-intro">Channel resmi tiap publisher. Thumbnail diambil langsung dari channel YouTube masing-masing.</p>
      <div class="channel-grid">
%(channels)s
      </div>
    </section>

    <p class="review-infobreak">
      Berita di halaman ini diambil dari Google News RSS dan Dialihkan ke artikel asli
      tiap penerbit saat kamu klik. Starwise tidak meng-host ulang isi artikel tersebut.
    </p>

  </main>

  <footer class="site-footer">
    <div class="container footer-inner">
      <p>&copy; 2025 Starwise. Game, Anime &amp; Film.</p>
      <p>Konten untuk tujuan informasi &amp; hiburan.</p>
    </div>
  </footer>

  <script src="js/news.js"></script>
  <script src="js/main.js"></script>
</body>
</html>
"""
    options = "\n".join(
        '          <option value="%s">%s</option>' % (H.escape(label), H.escape(label))
        for label, _, _ in GAMES)

    return html % {
        "total": total,
        "updated": updated,
        "days": MAX_AGE_DAYS,
        "options": options,
        "sections": "\n\n".join(sections),
        "channels": channels,
    }


def main():
    try:
        items = collect()
    except Exception as exc:
        print("Gagal mengambil berita: %s" % exc)
        items = json.loads((BASE / "_news_raw.json").read_text(encoding="utf-8")) \
            if (BASE / "_news_raw.json").exists() else []

    out = BASE / "news.html"
    out.write_text(build(items), encoding="utf-8")
    (BASE / "_news_raw.json").write_text(
        json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    print("OK news.html  %d bytes  %d berita"
          % (out.stat().st_size, out.read_text(encoding="utf-8").count('class="news-row"')))


if __name__ == "__main__":
    main()