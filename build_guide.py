# -*- coding: utf-8 -*-
"""Generator halaman panduan Starwise.

Usage: python build_guide.py _data_xxx.json [...]
Membaca file JSON panduan dan menulis halaman HTML-nya.
"""
import json
import sys
import pathlib

BASE = pathlib.Path(__file__).parent

TPL = """<!DOCTYPE html>
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
      <nav class="main-nav">
        <a href="index.html">Home</a>
        <a href="games.html">Games</a>
        <a href="anime.html">Anime</a>
        <a href="movies.html">Film</a>
        <a href="news.html">Berita</a>
        <a href="database.html">Database</a>
        <a href="streaming.html">Streaming</a>
        <a href="download.html">Download</a>
      </nav>
      <button class="menu-toggle" aria-label="Toggle menu">&#9776;</button>
    </div>
  </header>

  <main class="container">

    <nav class="breadcrumb" aria-label="Navigasi">
      <a href="games.html">Games</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">{short}</span>
    </nav>

    <div class="page-header">
      <h1>{title}</h1>
      <p class="page-sub">Wiki panduan Starwise: gameplay, tips, dan strategi.</p>
    </div>

    <section class="section">
      <h2 class="section-title">&#128220; Informasi Dasar</h2>
      <div class="db-table-wrapper">
        <table class="db-table">
          <tbody>
{info}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128203; Daftar Isi</h2>
      <ul class="guide-toc">
{toc}
      </ul>
    </section>

{sections}

    <section class="section">
      <h2 class="section-title">&#128250; Lanjutkan</h2>
      <div class="card-grid">
        <a href="{stream}" class="card">
          <div class="card-body">
            <h3>&#9654; Video Streaming</h3>
            <p>Tonton trailer, character demo, dan gameplay resmi.</p>
          </div>
        </a>
        <a href="database.html" class="card">
          <div class="card-body">
            <h3>&#128190; Database</h3>
            <p>Link website resmi dan data singkat setiap game.</p>
          </div>
        </a>
      </div>
    </section>

    <p class="review-infobreak">Catatan: angka pity dan mekanisme di halaman ini bisa berubah setelah patch. Cek pengumuman resmi bila perlu informasi paling mutakhir.</p>

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

SEC = """    <section class="section" id="{anchor}">
      <h2 class="section-title">{head}</h2>
{paras}
      <ul class="tip-list">
{bullets}
      </ul>
    </section>"""

ALLOWED = set("—–’‘“”…°×→")


def check_clean(data, where):
    bad = sorted({c for c in json.dumps(data, ensure_ascii=False)
                  if ord(c) > 127 and c not in ALLOWED})
    if bad:
        raise SystemExit("KARAKTER ANEH di %s: %r" % (where, bad))


def build(data):
    check_clean(data, data.get("file", "?"))
    info = "\n".join(
        '          <tr><th scope="row">%s</th><td>%s</td></tr>' % (k, v)
        for k, v in data["info"])
    toc = "\n".join(
        '          <li><a href="#%s">%s</a></li>' % (s["anchor"], s["head"])
        for s in data["sections"])
    secs = []
    for s in data["sections"]:
        paras = "\n".join("        <p>%s</p>" % x for x in s["paras"])
        bullets = "\n".join("          <li>%s</li>" % x for x in s["bullets"])
        secs.append(SEC.format(anchor=s["anchor"], head=s["head"],
                               paras=paras, bullets=bullets))
    return TPL.format(
        title=data["title"], desc=data["desc"],
        short=data["title"].replace("Panduan ", ""),
        info=info, toc=toc, sections="\n\n".join(secs),
        stream=data["stream"])


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