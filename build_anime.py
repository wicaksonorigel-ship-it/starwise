# -*- coding: utf-8 -*-
"""Generator halaman anime Starwise."""
import json
import pathlib

BASE = pathlib.Path(__file__).parent
A = json.loads((BASE / "_anime_img.json").read_text(encoding="utf-8"))

# status tayang berdasarkan pengumuman Fall 2026 (Crunchyroll / Anime Trending / GIGAZINE)
STATUS = {
    "apothecary": ("Ongoing", "2 Oktober 2026", "Netflix, Crunchyroll"),
    "blackclover": ("Ongoing", "3 Oktober 2026", "Crunchyroll"),
    "rayearth":    ("Ongoing", "Oktober 2026", "Crunchyroll"),
    "tougenanki":  ("Ongoing", "2 Oktober 2026", "Crunchyroll"),
    "overgeared":  ("Ongoing", "27 September 2026", "Crunchyroll"),
    "frieren2":    ("Ongoing", "Oktober 2026", "Crunchyroll"),
}

DESCR = {
    "apothecary": "Maomao Courtney bekerja sebagai apoteker dizynat istana. Season 3 melanjutkan kasus lingkungan dan politik yang lebih rumit.",
    "tougenanki": "Kagari, seorang compenserifi muda, menjadi anggota Replace Table. Cerita penuh konflik antara yokai dan manusia.",
    "blackclover": "Asta dan CharmyBlack kembali untuk season 2.IMA_ACTION dan masa depan Magic Kingdom.",
    "overgeared": "Proto Korea, samurai muda dengan kemampuan yang tak terbatas, tiba di duniaMMO penuhguild dan quest.",
    "rayearth":  "Celine, Hikaru, dan Fu harus menyatukan pasukan Toumashia untukProtect dunia dari NX.",
    "frieren2":  "Frieren dan party's perjalanan memasuki fase baru setelah arc sebelumnya selesai.",
}

ORDER = ["apothecary", "tougenanki", "blackclover", "overgeared", "rayearth", "frieren2"]

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

cards = "\n".join(f'''        <article class="anime-card">
          <a href="https://www.youtube.com/watch?v={A[k]['vid']}" target="_blank" rel="noopener" class="anime-card-link">
            <div class="anime-card-img">
              <img src="{A[k]['src']}" alt="{A[k]['title']}" loading="lazy" decoding="async">
              <span class="anime-rank">{STATUS[k][0]}</span>
            </div>
            <div class="anime-card-body">
              <h3>{A[k]['title']}</h3>
              <p class="anime-genre">{A[k]['genre']}</p>
              <p>{DESCR[k]}</p>
              <span class="cat-link">Tonton Trailer →</span>
            </div>
          </a>
        </article>''' for k in ORDER)

rows = "\n".join(f'''            <tr>
              <td><strong>{A[k]['title']}</strong></td>
              <td>{A[k]['genre']}</td>
              <td>{STATUS[k][0]}</td>
              <td>{STATUS[k][1]}</td>
              <td>{STATUS[k][2]}</td>
              <td><a href="https://www.youtube.com/watch?v={A[k]['vid']}" target="_blank" rel="noopener" class="video-link">Trailer</a></td>
            </tr>''' for k in ORDER)

HTML = f'''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Anime — Starwise</title>
  <meta name="description" content="Daftar anime musim ini: judul, genre, jadwal tayang, platform legal, dan trailer resmi.">
  <link rel="stylesheet" href="css/style.css">
</head>
<body>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="logo">Starwise</a>
{NAV}
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
      <p class="page-sub">Anime yang sedang tayang musim ini, lengkap dengan genre dan trailer resmi.</p>
    </div>

    <section class="section">
      <h2 class="section-title">&#128293; Sedang Tayang</h2>
      <p class="section-intro">Lineup musim gugur 2026. Trailer di bawah diambil dari channel resmi tiap anime.</p>
      <div class="anime-grid">
{cards}
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128203; Daftar Anime</h2>
      <p class="section-intro">Detail jadwal tayang dan platform legal untuk tiap judul.</p>
      <div class="db-table-wrapper">
        <table class="db-table">
          <thead>
            <tr>
              <th>Judul</th>
              <th>Genre</th>
              <th>Status</th>
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
      <h2 class="section-title">&#128161; Platform Legal</h2>
      <p class="section-intro">Tonton anime lewat layanan berbayar berikut. Hindari situs streaming ilegal.</p>
      <div class="card-grid">
        <div class="card">
          <div class="card-body">
            <h3>Crunchyroll</h3>
            <p>Pustaka anime terbesar dan paling cepat rilis episode. Banyak judul di halaman ini tayang di sini.</p>
          </div>
        </div>
        <div class="card">
          <div class="card-body">
            <h3>Netflix</h3>
            <p>Menyazon sebagian judul musiman, termasuk The Apothecary Diaries.</p>
          </div>
        </div>
        <div class="card">
          <div class="card-body">
            <h3>Disney+ Hotstar</h3>
            <p>Menyediakan beberapa judul anime secara musiman, tergantung wilayah.</p>
          </div>
        </div>
        <div class="card">
          <div class="card-body">
            <h3>YouTube Official</h3>
            <p>Banyak anime memposting trailer dan episode gratis di channel resminya. Trailer di atas berasal dari sini.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="section">
      <h2 class="section-title">&#128218; Cara Menonton dengan Baik</h2>
      <ul class="tip-list">
        <li><strong>Tonton sesuai urutan release.</strong> Kalau baru mulai sebuah seri, ikuti urutan tayang aslinya. Urutan episode tidak selalu sama dengan urutan cerita.</li>
        <li><strong>Tidak perlu nonton dua kali.</strong> Banyak anime sekarang menyediakan tontonan kali kedua dengan speed yang lebih cepat di layanan yang sama.</li>
        <li><strong>Baca Platform legal saja.</strong> Selain masalah kualitas, situs ilegal juga berisiko bagi perangkat kamu.</li>
        <li><strong>Perhatikan studio animasi.</strong> Studio yang sama biasanya konsisten dalam kualitas, berguna kalau kamu ingin rekomendasi serupa.</li>
        <li><strong>Urutkan berdasarkan genre dulu.</strong> Kalau bisa Integrity satu genre selama beberapa judul, kamu lebih cepat menemukan anime yang benar-benar kamu)nikmati.</li>
      </ul>
    </section>

    <p class="review-infobreak">Catatan: jadwal tayang bisa berubah sewaktu-waktu. Cek pengumuman resmi studio atau layanan streaming untuk informasi paling mutakhir.</p>

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
'''

(BASE / "anime.html").write_text(HTML, encoding="utf-8")
print("anime.html ditulis:", len(HTML), "bytes")