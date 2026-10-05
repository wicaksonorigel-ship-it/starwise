# -*- coding: utf-8 -*-
"""Generator halaman panduan Starwise.

Layout meniru struktur wiki game (sidebar quick access, guide box, tabel data,
daftar isi dengan ikon) tapi seluruh isi berbahasa Indonesia.

Usage: python build_guide.py _data_genshin.json [...]
"""
import json
import pathlib
import sys

BASE = pathlib.Path(__file__).parent
ALLOWED = set("—–’‘“”…°×→§✓✔")

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

ICO = {
    "syarat": "&#9881;", "gacha": "&#127922;", "echo": "&#128269;",
    "battle": "&#9876;", "sumber": "&#127793;", "harian": "&#128197;",
    "efisiensi": "&#9889;", "mistakes": "&#10060;", "tentang": "&#8505;",
    "sistem": "&#9881;", "kombat": "&#9876;", "combat": "&#9876;",
    "referensi": "&#128250;", "urutan": "&#127916;", "tips": "&#128161;",
    "platform": "&#128187;", "pemula": "&#127968;",
}

SUMICO = {
    "Developer": "&#127959;", "Genre": "&#127918;", "Rilis": "&#128337;",
    "Platform": "&#128187;", "Model": "&#127918;", "Studio": "&#127909;",
    "Mulai": "&#128337;", "Website resmi": "&#127760;",
}


def check_clean(data, where):
    bad = sorted({c for c in json.dumps(data, ensure_ascii=False)
                  if ord(c) > 127 and c not in ALLOWED})
    if bad:
        raise SystemExit("KARAKTER ANEH di %s: %r" % (where, bad))


HEAD = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} &mdash; Starwise</title>
  <meta name="description" content="{desc}">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="logo">Starwise</a>
{nav}
      <button class="menu-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </header>

  <main class="container guide-layout">

    <aside class="guide-side">
      <div class="side-box side-logo">
        <img src="{logo}" alt="{short}" loading="eager" decoding="async">
        <div class="side-logo-meta">
          <strong>{short}</strong>
          <span>{genre}</span>
        </div>
      </div>

      <nav class="side-box" aria-label="Daftar isi panduan">
        <h2 class="side-title">Daftar Isi</h2>
        <ul class="side-toc">
{toc}
        </ul>
      </nav>

      <div class="side-box">
        <h2 class="side-title">Pintasan</h2>
        <div class="quick-grid">
{quick}
        </div>
      </div>

      <div class="side-box">
        <h2 class="side-title">Lanjut ke</h2>
        <div class="quick-grid">
          <a href="{stream}" class="qbox">
            <span class="qbox-ico">&#9654;</span>
            <span class="qbox-label">Video streaming</span>
          </a>
          <a href="database.html" class="qbox">
            <span class="qbox-ico">&#128190;</span>
            <span class="qbox-label">Database game</span>
          </a>
          <a href="games.html" class="qbox">
            <span class="qbox-ico">&#127918;</span>
            <span class="qbox-label">Semua game</span>
          </a>
          <a href="download.html" class="qbox">
            <span class="qbox-ico">&#128214;</span>
            <span class="qbox-label">Panduan lain</span>
          </a>
        </div>
      </div>
    </aside>

    <article class="guide-main">

      <nav class="breadcrumb" aria-label="Navigasi">
        <a href="games.html">Games</a>
        <span class="crumb-sep">/</span>
        <span class="crumb-cur">{short}</span>
      </nav>

      <header class="guide-head">
        <h1>{title}</h1>
        <p class="guide-lead">{lead}</p>
      </header>

      <div class="guide-hero">
        <img src="{wall}" alt="Wallpaper {short}" loading="lazy" decoding="async">
      </div>

      <section class="guide-box">
        <h2 class="section-title">&#128196; Ringkasan Cepat</h2>
        <div class="summary-grid">
{summary}
        </div>
      </section>

      <section class="guide-block">
        <h2 class="section-title">&#128220; Informasi Dasar</h2>
        <div class="db-table-wrapper">
          <table class="db-table">
            <tbody>
{info}
            </tbody>
          </table>
        </div>
      </section>

{sections}

      <p class="review-infobreak">Catatan: angka pity, jadwal, dan mekanisme di halaman ini bisa berubah setelah patch. Cek pengumuman resmi bila perlu informasi paling mutakhir.</p>

    </article>
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
"""

SEC = """      <section class="guide-block" id="{anchor}">
        <h2 class="section-title">{ico} {head}</h2>
{paras}
        <ul class="tip-list">
{bullets}
        </ul>
      </section>"""

SUMTPL = """          <div class="sum-item">
            <span class="sum-ico">{ico}</span>
            <div>
              <strong>{label}</strong>
              <span>{value}</span>
            </div>
          </div>"""


def build(data):
    check_clean(data, data.get("file", "?"))
    short = data["title"].replace("Panduan ", "")

    toc = "\n".join(
        '          <li><a href="#%s"><span class="side-ico">%s</span>%s</a></li>'
        % (s["anchor"], ICO.get(s["anchor"], "&#8226;"), s["head"])
        for s in data["sections"])

    quick = "\n".join(
        '          <a href="#%s" class="qbox">\n'
        '            <span class="qbox-ico">%s</span>\n'
        '            <span class="qbox-label">%s</span>\n'
        '          </a>' % (s["anchor"], ICO.get(s["anchor"], "&#8226;"), s["head"])
        for s in data["sections"])

    info = "\n".join(
        '              <tr><th scope="row">%s</th><td>%s</td></tr>' % (k, v)
        for k, v in data["info"])

    summary = "\n".join(
        SUMTPL.format(ico=SUMICO.get(k, "&#8226;"), label=k, value=v)
        for k, v in data["info"])

    secs = []
    for s in data["sections"]:
        paras = "\n".join("        <p>%s</p>" % x for x in s["paras"])
        bullets = "\n".join("          <li>%s</li>" % x for x in s["bullets"])
        secs.append(SEC.format(anchor=s["anchor"], head=s["head"],
                               ico=ICO.get(s["anchor"], "&#8226;"),
                               paras=paras, bullets=bullets))

    return HEAD.format(
        title=data["title"], desc=data["desc"], nav=NAV, short=short,
        logo=data.get("logo", ""),
        wall=data.get("wallpaper", data.get("logo", "")),
        genre=data.get("genre", ""), lead=data.get("lead", ""),
        stream=data["stream"], info=info, toc=toc, quick=quick,
        summary=summary, sections="\n\n".join(secs))


def main():
    for arg in sys.argv[1:]:
        src = BASE / arg
        data = json.loads(src.read_text(encoding="utf-8"))
        out = BASE / data["file"]
        out.write_text(build(data), encoding="utf-8")
        print("OK %-34s %5d bytes  %d sections"
              % (data["file"], out.stat().st_size, len(data["sections"])))


if __name__ == "__main__":
    main()