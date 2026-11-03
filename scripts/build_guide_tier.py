# -*- coding: utf-8 -*-
"""Sisipkan section tier list ke halaman panduan tiap game.

Membaca _tier_data.json (hasil build_tier.py) lalu menambahkan section
tier list ke guide-<game>.html. Kalau section sudah ada, diganti.

Jalankan setelah build_tier.py: python build_guide_tier.py
"""
import json
import pathlib
import re

import build_tier as bt

BASE = pathlib.Path(__file__).parent
MARK = 'id="tier-list"'

# urutan section yang enak dibaca: tier list diletakkan setelah section pertama
INSERT_AFTER = {
    "hsr": "gacha",
    "zzz": "gacha",
    "wuthering": "gacha",
    "genshin": "gacha",
    "endfield": "tentang",
    "nte": "tentang",
}


def load_data():
    f = BASE / "_tier_data.json"
    if not f.exists():
        print("_tier_data.json belum ada. Jalankan build_tier.py dulu.")
        return {}
    return json.loads(f.read_text(encoding="utf-8"))


def strip_old(txt):
    """Hapus section tier list lama (kalau ada) supaya tidak menumpuk."""
    return re.sub(
        r'\n*[ \t]*<section class="guide-block" id="tier-list">.*?</section>\n*',
        "\n\n", txt, flags=re.S)


def main():
    data = load_data()
    if not data:
        return

    for slug, tiers in data.items():
        guide = BASE / bt.GUIDE_MAP.get(slug, "")
        if not guide.exists():
            print("%-10s halaman panduan tidak ada" % slug)
            continue

        txt = guide.read_text(encoding="utf-8")
        n_before = txt.count(MARK)
        txt = strip_old(txt)

        section = bt.tier_section(tiers, slug)

        # titik sisip: setelah section tertentu
        anchor_id = INSERT_AFTER.get(slug, "gacha")
        pat = re.compile(
            r'(<section class="guide-block" id="%s">.*?</section>\n)' % anchor_id, re.S)
        m = pat.search(txt)

        if m:
            txt = txt[:m.end()] + "\n" + section + "\n" + txt[m.end():]
        else:
            # fallback: sebelum catatan penutup
            marker = '    <p class="review-infobreak">'
            i = txt.find(marker)
            if i < 0:
                print("%-10s titik sisip tidak ditemukan" % slug)
                continue
            txt = txt[:i] + section + "\n\n" + txt[i:]

        guide.write_text(txt, encoding="utf-8")
        n_char = sum(len(t["chars"]) for t in tiers)
        print("%-10s -> %-32s %d tier, %d char (lama: %d section)"
              % (slug, guide.name, len(tiers), n_char, n_before))


if __name__ == "__main__":
    main()