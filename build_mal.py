# -*- coding: utf-8 -*-
"""Tambah daftar MyAnimeList ke anime.html.

Mengambil 4 daftar dari MyAnimeList (Top Airing, Top Upcoming,
Top by Popularity) lalu menyisipkannya sebagai section baru di anime.html.

Jalankan: python build_mal.py
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

LISTS = [
    ("airing", "Top Airing", "Sedang tayang paling banyak diikuti"),
    ("upcoming", "Top Upcoming", "Yang paling ditunggu"),
    ("bypopularity", "Top Populer", "Paling banyak ditonton di MyAnimeList"),
]

PER_LIST = 12
START_ID = "mal-lists"


def fetch(kind):
    url = "https://myanimelist.net/topanime.php"
    if kind in ("airing", "upcoming"):
        url += "?type=" + kind
    html_ = urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=28).read().decode("utf-8", "ignore")

    rows = re.findall(r'<tr class="ranking-list">(.*?)</tr>', html_, re.S)
    out = []
    for r in rows:
        t = re.search(
            r'<h3[^>]*class="[^"]*anime_ranking_h3[^"]*"[^>]*>.*?'
            r'<a href="([^"]+)"[^>]*>(.*?)</a>', r, re.S)
        if not t:
            continue
        link, title = t.group(1), re.sub(r"<[^>]+>", "", t.group(2)).strip()
        img = re.search(
            r'data-src="(https://cdn\.myanimelist\.net/r/[^"]+?images/anime/[^"]+)"', r)
        info = re.search(r'<div class="information[^"]*">(.*?)</div>', r, re.S)
        text = re.sub(r"<[^>]+>", " ", info.group(1)) if info else ""
        text = re.sub(r"\s+", " ", text).strip()
        # MAL: gambar 50x70 -> ambil versi lebih besar
        full = (img.group(1).replace("/r/50x70/", "/r/220x310/").replace("/r/100x140/", "/r/220x310/")
                if img else "")
        if not full:
            m2 = re.search(r'data-srcset="https://cdn\.myanimelist\.net/r/(\d+x\d+)/([^"]+?)\s', r)
            if m2:
                full = "https://cdn.myanimelist.net/r/%s/%s" % (m2.group(1), m2.group(2))
        out.append({"title": title, "link": link, "img": full, "info": text})
        if len(out) >= PER_LIST:
            break
    return out


def esc(s):
    return html.escape(s, quote=True)


def section(kind, label, desc, items):
    cards = []
    for a in items:
        thumb = ('<img src="%s" alt="" loading="lazy" decoding="async">' % esc(a["img"])) \
            if a["img"] else '<span class="mal-noimg">&#128250;</span>'
        cards.append(
            '        <a class="mal-card" href="%s" target="_blank" rel="noopener">\n'
            '          <span class="mal-poster">%s</span>\n'
            '          <span class="mal-body">\n'
            '            <strong>%s</strong>\n'
            '            <span class="mal-info">%s</span>\n'
            '          </span>\n'
            '        </a>'
            % (esc(a["link"]), thumb, esc(a["title"]), esc(a["info"])))
    return (
        '    <section class="section" id="%s-%s">\n'
        '      <header class="section-head">\n'
        '        <h2 class="section-title">%s</h2>\n'
        '        <a class="section-more" target="_blank" rel="noopener" '
        'href="https://myanimelist.net/topanime.php%s">Lihat di MAL &rarr;</a>\n'
        '      </header>\n'
        '      <p class="section-intro">%s</p>\n'
        '      <div class="mal-grid">\n%s\n      </div>\n'
        '    </section>'
        % (START_ID, kind, esc(label),
           ("?type=" + kind) if kind in ("airing", "upcoming") else "",
           esc(desc), "\n".join(cards)))


def build():
    blocks = []
    for kind, label, desc in LISTS:
        try:
            items = fetch(kind)
        except Exception as exc:
            print("Gagal ambil %s: %s" % (kind, exc))
            continue
        if not items:
            continue
        blocks.append(section(kind, label, desc, items))
        print("@%-14s %d anime" % (kind, len(items)))
        time.sleep(0.8)

    if not blocks:
        return None

    nav_tab = (
        '        <a href="anime.html#%s-airing" class="cat-card">\n'
        '          <div class="cat-card-body">\n'
        '            <h3>&#128250; Daftar MAL</h3>\n'
        '            <p>Top anime sedang tayang, paling ditunggu, dan paling populer '
        'menurut MyAnimeList.</p>\n'
        '          </div>\n'
        '        </a>\n' % START_ID)

    return "\n\n".join(blocks), nav_tab


def main():
    result = build()
    if not result:
        print("Tidak ada data MAL yang berhasil diambil.")
        return
    blocks, nav_tab = result

    f = BASE / "anime.html"
    txt = f.read_text(encoding="utf-8")

    # Sisipkan di SEBELUM section playlist supaya MAL tidak terdorong
    # ke bawah halaman setiap kali auto-update jalan.
    marker = '    <section class="section" id="playlist">'
    i = txt.find(marker)
    if i < 0:
        # fallback: sisipkan sebelum catatan penutup
        marker = '    <p class="review-infobreak">'
        i = txt.find(marker)
    if i < 0:
        print('Penanda sisip tidak ditemukan; dilewati.')
        return

    if 'id="mal-lists-' in txt:
        # Hapus section MAL dari run sebelumnya supaya bisa di-ganti.
        # Regex tahan spasi/indentasi: section yang disisipkan sebelumnya
        # bisa menempel tanpa indentasi, jadi jangan andalkan spasi.
        cleaned, n_removed = re.subn(
            r'\n\n[ \t]*<section class="section" id="mal-lists-[^"]+">'
            r'.*?</section>(?=\n)', "", txt, flags=re.S)
        if n_removed:
            txt = cleaned
            print("Section MAL lama dihapus: %d" % n_removed)
        else:
            print("PERINGATAN: section MAL tidak terhapus; data mungkin ganda.")
    else:
        # Sisipkan tab navigasi sekali saja.
        anchor_nav = ('      <div class="card-grid">\n'
                      '        <a href="https://www.crunchyroll.com/"')
        if anchor_nav in txt:
            txt = txt.replace(anchor_nav, nav_tab + anchor_nav, 1)

    i = txt.find(marker)
    txt = txt[:i] + blocks + "\n\n" + txt[i:]

    f.write_text(txt, encoding="utf-8")
    (BASE / "_mal_raw.json").write_text(
        json.dumps(blocks, ensure_ascii=False, indent=1), encoding="utf-8")
    n_sections = len(re.findall(r'id="mal-lists-', txt))
    n_cards = txt.count('class="mal-card"')
    print("anime.html diperbarui: %d section, %d card, %d byte"
          % (n_sections, n_cards, f.stat().st_size))


if __name__ == "__main__":
    main()
