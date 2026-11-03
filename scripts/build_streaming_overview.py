# -*- coding: utf-8 -*-
"""Perbarui jumlah video di streaming.html (halaman overview).

Menjalankan build_streaming.py setelahnya supaya badge jumlah video
di kartu kategori selalu cocok dengan isi halamannya.

Jalankan: python build_streaming_overview.py
"""
import pathlib
import re

BASE = pathlib.Path(__file__).parent

# slug -> (judul kartu, keterangan, id video untuk thumbnail)
SLUGS = [
    ("wuthering", "Wuthering Waves", "Resonator showcase, trailer versi, dan gameplay."),
    ("genshin", "Genshin Impact", "Character trailer, anniversary video, dan konten resmi."),
    ("zzz", "Zenless Zone Zero", "Character demo, story video, dan konten update."),
    ("hsr", "Honkai: Star Rail", "Character trailer, event preview, dan konten resmi."),
    ("nte", "Neverness to Everness", "Combat showcase, character PV, dan opening animation."),
    ("endfield", "Arknights: Endfield", "Cutscene, version update info, dan konten resmi."),
    ("marvel", "Film & Marvel", "Trailer film MCU, special look, dan konten Marvel Entertainment."),
]


def count_for(slug):
    f = BASE / ("streaming-%s.html" % slug)
    if not f.exists():
        return 0
    return len(set(re.findall(
        r'youtube\.com/embed/([\w-]{11})', f.read_text(encoding="utf-8"))))


def thumb_for(slug):
    """Ambil satu video id dari halaman kategori sebagai sumber thumbnail."""
    f = BASE / ("streaming-%s.html" % slug)
    if not f.exists():
        return ""
    vids = re.findall(r'youtube\.com/embed/([\w-]{11})', f.read_text(encoding="utf-8"))
    return vids[0] if vids else ""


def main():
    f = BASE / "streaming.html"
    txt = f.read_text(encoding="utf-8")
    changed = 0

    for slug, title, desc in SLUGS:
        n = count_for(slug)
        vid = thumb_for(slug)
        if not n or not vid:
            print("%-12s dilewati (n=%d vid=%s)" % (slug, n, bool(vid)))
            continue

        # perbarui badge jumlah video
        pat = re.compile(
            r'(<a href="streaming-%s\.html" class="cat-card"[^>]*>.*?'
            r'<span class="cat-badge">)\d+( video)</span>' % slug, re.S)
        new_txt, cnt = pat.subn(
            lambda m: m.group(1) + str(n) + m.group(2) + "</span>", txt)
        if cnt:
            txt = new_txt
            changed += 1

        # perbarui thumbnail ke video terbaru
        pat2 = re.compile(
            r'(<a href="streaming-%s\.html" class="cat-card"[^>]*>.*?'
            r'<img src="https://img\.youtube\.com/vi/)[\w-]{11}(/maxresdefault\.jpg")' % slug,
            re.S)
        txt, cnt2 = pat2.subn(lambda m: m.group(1) + vid + m.group(2), txt)

    f.write_text(txt, encoding="utf-8")
    print("streaming.html diperbarui (%d badge)" % changed)


if __name__ == "__main__":
    main()