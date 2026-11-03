# -*- coding: utf-8 -*-
"""Auto-update halaman streaming Starwise.

Menarik video terbaru dari kanal resmi tiap game dan menulis ulang
halaman streaming-<game>.html. Video yang sudah ada tidak dihapus;
yang baru saja ditambahkan di bagian atas.

Jalankan: python build_streaming.py
"""
import json
import pathlib
import re
import time
import urllib.request

BASE = pathlib.Path(__file__).parent
UA = {"User-Agent":
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120"}

# slug -> (channel handle, judul halaman, subjudul)
CHANNELS = {
    "wuthering": ("WutheringWaves", "Wuthering Waves",
                  "Video trailer, showcase, dan gameplay resmi."),
    "genshin": ("GenshinImpact", "Genshin Impact",
                "Character trailer, anniversary video, dan konten resmi."),
    "zzz": ("ZZZ_Official", "Zenless Zone Zero",
            "Character demo, story video, dan konten resmi."),
    "hsr": ("HonkaiStarRail", "Honkai: Star Rail",
            "Character trailer, event preview, dan konten resmi."),
    "nte": ("NTE_Official", "Neverness to Everness",
            "Combat showcase, character PV, dan opening animation."),
    "endfield": ("arknightsendfieldEN", "Arknights: Endfield",
                 "Cutscene, version update info, dan konten resmi."),
    "marvel": ("marvel", "Film & Marvel",
               "Trailer film MCU, special look, dan konten Marvel Entertainment."),
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

MAX_PER_GAME = 24


def fetch(handle):
    """Ambil video dari tab featured. Judul diambil dari metadata lockup."""
    for tab in ("featured", "videos"):
        try:
            url = "https://www.youtube.com/@%s/%s" % (handle, tab)
            html = urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=25).read().decode("utf-8", "ignore")
        except Exception:
            continue

        found = {}
        for m in re.finditer(r'"videoId":"([\w-]{11})"', html):
            vid = m.group(1)
            if vid in found:
                continue
            seg = html[max(0, m.start() - 3000):m.start() + 3000]
            t = re.search(r'"title":\{"runs":\[\{"text":"(.*?)"', seg)
            if not t:
                continue
            title = t.group(1)
            # buang judul yang cuma label kategori (mis. "Shorts", "Official Trailers")
            if len(title) < 6 or title.lower() in (
                    "shorts", "trailers", "official trailers", "live",
                    "playlists", "community", "channels", "home"):
                continue
            if '"isUpcoming"' in seg and 'premiere' in title.lower():
                continue
            found[vid] = title
            if len(found) >= MAX_PER_GAME * 2:
                break
        if found:
            return found
    return {}


def existing_videos(slug):
    """Baca video ID yang sudah ada di halaman."""
    f = BASE / ("streaming-%s.html" % slug)
    if not f.exists():
        return []
    txt = f.read_text(encoding="utf-8")
    return list(dict.fromkeys(re.findall(
        r'youtube\.com/embed/([\w-]{11})', txt)))


def video_card(vid, title):
    safe = (title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))
    return '''      <div class="video-card">
        <div class="video-thumb">
          <iframe src="https://www.youtube.com/embed/%s"
                  title="%s" loading="lazy"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowfullscreen
                  style="position:absolute; inset:0; width:100%%; height:100%%; border:none;"></iframe>
        </div>
        <div class="video-body">
          <h3>%s</h3>
          <p>Dari kanal resmi</p>
          <a href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener" class="video-link">&#9654; Tonton di YouTube</a>
        </div>
      </div>''' % (vid, safe, safe, vid)


def build_page(slug, handle, heading, sub, videos):
    existing = existing_videos(slug)
    # Video yang sudah pernah tampil SELALU dipertahankan (jangan sampai hilang).
    # Video baru dari kanal resmi ditambahkan di atasnya.
    fresh = [v for v in videos.keys() if v not in existing]
    merged = fresh + list(existing)
    ordered = []
    for v in merged:
        if v not in ordered:
            ordered.append(v)
    ordered = ordered[:MAX_PER_GAME]

    cards = "\n\n".join(
        video_card(v, videos.get(v, "Video resmi")) for v in ordered)

    n_new = len([v for v in videos if v not in existing])

    html = '''<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Streaming &#8212; %s &#8212; Starwise</title>
  <meta name="description" content="%s">
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

    <nav class="breadcrumb" aria-label="Navigasi streaming">
      <a href="streaming.html">&larr; Semua Kategori</a>
      <span class="crumb-sep">/</span>
      <span class="crumb-cur">%s</span>
      <span class="video-count">%d video</span>
    </nav>

    <div class="page-header">
      <h1>&#127918; %s</h1>
      <p class="page-sub"><strong>%d video</strong> di halaman ini. %s</p>
    </div>

    <div class="video-grid">

%s

    </div>

    <p class="review-infobreak" style="text-align:center; font-size:0.82rem; color:var(--fg-muted);">
      &#9888;&#65039; Semua video diembed dari YouTube. Klik link untuk tonton di YouTube.
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
''' % (heading, sub, NAV, heading, len(ordered), heading, len(ordered), sub, cards)

    return html, n_new, len(ordered)


def main():
    report = {}
    for slug, (handle, heading, sub) in CHANNELS.items():
        try:
            videos = fetch(handle)
        except Exception as exc:
            print("Gagal ambil @%s: %s" % (handle, exc))
            continue
        if not videos:
            print("Tidak ada video dari @%s" % handle)
            continue
        html, n_new, total = build_page(slug, handle, heading, sub, videos)
        (BASE / ("streaming-%s.html" % slug)).write_text(html, encoding="utf-8")
        report[slug] = {"handle": handle, "new": n_new, "total": total,
                        "found": len(videos)}
        print("@%-20s baru=%-3d total=%-3d (ditemukan %d)"
              % (handle, n_new, total, len(videos)))
        time.sleep(0.6)

    (BASE / "_streaming_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    total_new = sum(r["new"] for r in report.values())
    print("\nSelesai. Video baru: %d" % total_new)


if __name__ == "__main__":
    main()