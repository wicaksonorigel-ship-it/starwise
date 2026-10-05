# -*- coding: utf-8 -*-
"""Generator halaman anime Starwise.

Sumber data:
  _anime_img.json     -> poster + trailer untuk anime yang sedang tayang
  _muse_playlists.json -> playlist YouTube dari channel Muse Asia

Jalankan: python build_anime.py
"""
import json
import pathlib
import re

BASE = pathlib.Path(__file__).parent
ANIME = json.loads((BASE / "_anime_img.json").read_text(encoding="utf-8"))
PLAYLISTS = json.loads((BASE / "_muse_playlists.json").read_text(encoding="utf-8"))

# Status tayang: Fall 2026 (Crunchyroll / Anime Trending lineup)
META = {
    "apothecary": {
        "air": "2 Oktober 2026",
        "platform": "Netflix, Crunchyroll",
        "studio": "OLM",
        "desc": ("Maomao Courtney bekerja sebagai apoteker di istana. Season 3 "
                 "melanjutkan kasus lingkungan dan politik yang lebih rumit."),
    },
    "tougenanki": {
        "air": "2 Oktober 2026",
        "platform": "Crunchyroll",
        "studio": "Studio Hibari",
        "desc": ("Kagari, seorang Executioner muda, menjadi anggota Replace Table. "
                 "Cerita penuh konflik antara yokai dan manusia."),
    },
    "blackclover": {
        "air": "3 Oktober 2026",
        "platform": "Crunchyroll",
        "studio": "Pierrot",
        "desc": ("Asta dan Charmy kembali untuk season 2, dengan aksi yang lebih "
                 "intens dan masa depan Magic Kingdom yang mulai Terbuka."),
    },
    "overgeared": {
        "air": "27 September 2026",
        "platform": "Crunchyroll",
        "studio": "Studio N",
        "desc": ("Proto Korea, samurai muda dengan kemampuan tak terbatas, "
                 "tiba di dunia MMO yang penuh guild dan quest."),
    },
    "rayearth": {
        "air": "Oktober 2026",
        "platform": "Crunchyroll",
        "studio": "Sunrise",
        "desc": ("Celine, Hikaru, dan Fu harus menyatukan pasukan Toumashia "
                 "untuk melindungi dunia dari NX."),
    },
    "frieren2": {
        "air": "Oktober 2026",
        "platform": "Crunchyroll",
        "studio": "Madhouse",
        "desc": ("Perjalanan Frieren dan teman-temannya memasuki fase baru "
                 "setelah arc sebelumnya selesai."),
    },
}

ORDER = ["apothecary", "tougenanki", "blackclover", "overgeared", "rayearth", "frieren2"]

PLATFORMS = [
    ("https://www.crunchyroll.com/", "Crunchyroll",
     "Pustaka anime terbesar dan paling cepat rilis episode. "
     "Banyak judul di halaman ini tayang di sini."),
    ("https://www.netflix.com/", "Netflix",
     "Menyediakan sebagian judul musiman, termasuk The Apothecary Diaries season 3."),
    ("https://www.disneyplus.com/", "Disney+ Hotstar",
     "Menyediakan beberapa judul anime musiman, tergantung wilayah."),
    ("https://www.youtube.com/@MuseAsia", "YouTube official",
     "Channel resmi yang mengunggah episode gratis. Playlist di bawah "
     "diambil dari channel ini."),
]

NAV = '''      <nav class="main-nav">
        <a href="index.html">Home</a>
        <a href="games.html">Games</a>
        <a href="anime.html" class="active">Anime</a>
        <a href="movies.html">Film</a>
        <a href="news.html">Berita</a>
        <a href="database.html">Database</a>
        <a href="streaming.html">Streaming</a>
        <a href="download.html">Download</a>
      </nav>'''

ALLOWED = set("—–’‘“”…°×→§✓∞")


def guard(text, where):
    bad = sorted({c for c in text if ord(c) > 127 and c not in ALLOWED})
    if bad:
        raise SystemExit("KARAKTER ANEH di %s: %r" % (where, bad))


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def slug(title):
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def hero_cards():
    out = []
    for key in ORDER:
        a = ANIME[key]
        m = META[key]
        out.append(
            '        <article class="anime-card">\n'
            '          <a href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener">\n'
            '            <span class="anime-thumb">\n'
            '              <img src="%s" alt="%s" loading="lazy" decoding="async">\n'
            '              <span class="anime-flag">Sedang Tayang</span>\n'
            '            </span>\n'
            '            <span class="anime-body">\n'
            '              <h3>%s</h3>\n'
            '              <span class="anime-genre">%s</span>\n'
            '              <p>%s</p>\n'
            '              <span class="anime-facts">\n'
            '                <span><b>Studio</b> %s</span>\n'
            '                <span><b>Tayang</b> %s</span>\n'
            '              </span>\n'
            '              <span class="cat-link">Tonton trailer &rarr;</span>\n'
            '            </span>\n'
            '          </a>\n'
            '        </article>'
            % (a["vid"], a["src"], esc(a["title"]), esc(a["title"]),
               esc(a["genre"]), esc(m["desc"]), esc(m["studio"]), esc(m["air"])))
    return "\n".join(out)


def table_rows():
    out = []
    for key in ORDER:
        a = ANIME[key]
        m = META[key]
        out.append(
            '              <tr>\n'
            '                <td><strong>%s</strong></td>\n'
            '                <td>%s</td>\n'
            '                <td>%s</td>\n'
            '                <td>%s</td>\n'
            '                <td>%s</td>\n'
            '                <td><a href="https://www.youtube.com/watch?v=%s" '
            'target="_blank" rel="noopener" class="video-link">Trailer</a></td>\n'
            '              </tr>'
            % (esc(a["title"]), esc(a["genre"]), esc(m["studio"]),
               esc(m["air"]), esc(m["platform"]), a["vid"]))
    return "\n".join(out)


def playlist_cards():
    """Kartu playlist. Video di channel ini mematikan embed (Error 153),
    jadi kartu ini membuka playlist di YouTube, bukan memutar iframe."""
    out = []
    for p in PLAYLISTS:
        if not p.get("videos"):
            continue
        title = p["title"].replace("[English Sub]", "").strip()
        out.append(
            '        <a class="pl-card" target="_blank" rel="noopener"\n'
            '           href="https://www.youtube.com/playlist?list=%s">\n'
            '          <span class="pl-thumb">\n'
            '            <img src="%s" alt="%s" loading="lazy" decoding="async">\n'
            '            <span class="pl-count">%d episode</span>\n'
            '            <span class="pl-play" aria-hidden="true">&#9654;</span>\n'
            '          </span>\n'
            '          <span class="pl-body">\n'
            '            <strong>%s</strong>\n'
            '            <span class="pl-desc">Episode lengkap dengan subtitle Inggris,\n'
            '            diunggah resmi oleh Muse Asia.</span>\n'
            '            <span class="pl-link">Buka di YouTube &rarr;</span>\n'
            '          </span>\n'
            '        </a>'
            % (p["pid"], p["thumb"], esc(title), p["count"], esc(title)))
    return "\n".join(out)


def trailer_block():
    """Trailer resmi. Pola ini sama dengan halaman streaming yang sudah
    terbukti bisa diputar, jadi embed diaktifkan."""
    items = []
    for key in ORDER:
        a = ANIME[key]
        items.append(
            '        <div class="video-card">\n'
            '          <div class="video-thumb">\n'
            '            <iframe src="https://www.youtube.com/embed/%s"\n'
            '                    title="Trailer %s" loading="lazy"\n'
            '                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"\n'
            '                    allowfullscreen\n'
            '                    style="position:absolute; inset:0; width:100%%; height:100%%; border:none;">\n'
            '          </div>\n'
            '          <div class="video-body">\n'
            '            <h3>%s</h3>\n'
            '            <p>%s</p>\n'
            '            <a href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener"\n'
            '               class="video-link">Tonton di YouTube</a>\n'
            '          </div>\n'
            '        </div>'
            % (a["vid"], esc(a["title"]), esc(a["title"]), esc(a["genre"]), a["vid"]))
    return "\n".join(items)


def build():
    sections = []
    for key in ORDER:
        a = ANIME[key]
        m = META[key]
        sections.append(
            '        <a class="genre-chip" href="#anime-%s">\n'
            '          <strong>%s</strong>\n'
            '          <span>%s</span>\n'
            '        </a>'
            % (slug(a["title"]), esc(a["title"]), esc(a["genre"])))

    platforms = "\n".join(
        '        <a href="%s" target="_blank" rel="noopener" class="card">\n'
        '          <div class="card-body">\n'
        '            <h3>%s</h3>\n'
        '            <p>%s</p>\n'
        '          </div>\n'
        '        </a>' % (u, esc(t), esc(d)) for u, t, d in PLATFORMS)

    total_ep = sum(p["count"] for p in PLAYLISTS if p.get("videos"))

    html = """<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Anime &mdash; Starwise</title>
  <meta name="description" content="Anime musim ini, playlist episode resmi di YouTube, dan panduan platform streaming legal.">
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

  <main class="container">

    <nav class="breadcrumb" aria-label="Navigasi">
      <a href="index.html">Home</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">Anime</span>
    </nav>

    <div class="page-header">
      <h1>Anime</h1>
      <p class="page-sub">Anime yang sedang tayang, playlist episode resmi, dan tempat menonton legal.</p>
    </div>

    <section class="section anime-hero-strip">
      <div class="stat-row">
        <div class="stat"><b>{n_anime}</b><span>Sedang tayang</span></div>
        <div class="stat"><b>{n_pl}</b><span>Playlist</span></div>
        <div class="stat"><b>{n_ep}</b><span>Episode</span></div>
        <div class="stat"><b>{n_plat}</b><span>Platform legal</span></div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128293; Sedang Tayang</h2>
      <p class="section-intro">Lineup musim gugur 2026. Trailer diambil dari kanal resmi tiap studio.</p>
      <div class="anime-grid">
{hero_cards}
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128218; Daftar Anime</h2>
      <p class="section-intro">Detail studio, jadwal tayang, dan platform legal untuk tiap judul.</p>
      <div class="db-table-wrapper">
        <table class="db-table">
          <thead>
            <tr>
              <th>Judul</th>
              <th>Genre</th>
              <th>Studio</th>
              <th>Mulai Tayang</th>
              <th>Platform Legal</th>
              <th>Trailer</th>
            </tr>
          </thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#9654; Trailer Resmi</h2>
      <p class="section-intro">
        Trailer dari kanal resmi tiap studio. Video di-embed langsung dari YouTube.
      </p>
      <div class="video-grid">
{trailers}
      </div>
    </section>

    <section class="section" id="playlist">
      <h2 class="section-title">&#127916; Playlist Episode Lengkap</h2>
      <p class="section-intro">
        Playlist dari channel resmi Muse Asia. Chanel ini mematikan fitur embed,
        jadi setiap kartu membuka playlist di tab YouTube.
      </p>
      <div class="pl-grid">
{playlist_cards}
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128161; Platform Legal</h2>
      <p class="section-intro">Tonton anime lewat layanan berbayar berikut. Hindari situs streaming ilegal.</p>
      <div class="card-grid">
{platforms}
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128218; Tips Menonton</h2>
      <ul class="tip-list">
        <li><strong>Ikuti urutan release.</strong> Kalau baru mulai sebuah seri, ikuti urutan tayang aslinya. Urutan episode tidak selalu sama dengan urutan cerita.</li>
        <li><strong>Pakai fitur tontonan kali kedua.</strong> Banyak layanan menyediakan speed lebih cepat tanpa mengulang sesi login.</li>
        <li><strong>Hindari situs ilegal.</strong> Selain kualitas buruk, situs seperti itu juga berisiko bagi perangkatmu.</li>
        <li><strong>Perhatikan studio animasi.</strong> Studio yang sama biasanya konsisten kualitasnya, berguna kalau ingin rekomendasi serupa.</li>
        <li><strong>Cek satu genre dulu.</strong> Kalau kamu konsisten pada satu genre selama beberapa judul, kamu akan lebih cepat menemukan anime yang benar-benar kamu nikmati.</li>
      </ul>
    </section>

    <p class="review-infobreak">
      Jadwal tayang bisa berubah sewaktu-waktu. Cek pengumuman resmi studio atau
      layanan streaming untuk informasi paling mutakhir.
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
""".format(
        nav=NAV,
        n_anime=len(ORDER),
        n_pl=len([p for p in PLAYLISTS if p.get("videos")]),
        n_ep=total_ep,
        n_plat=len(PLATFORMS),
        hero_cards=hero_cards(),
        rows=table_rows(),
        playlist_cards=playlist_cards(),
        trailers=trailer_block(),
        platforms=platforms,
    )

    guard(html, "anime.html")
    return html


def main():
    out = BASE / "anime.html"
    out.write_text(build(), encoding="utf-8")
    text = out.read_text(encoding="utf-8")
    print("OK anime.html  %d bytes  %d anime, %d playlist, %d episode"
          % (out.stat().st_size,
             text.count('class="anime-card"'),
             text.count('class="pl-card"'),
             sum(p["count"] for p in PLAYLISTS if p.get("videos"))))


if __name__ == "__main__":
    main()