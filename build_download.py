# -*- coding: utf-8 -*-
"""Build download.html dari _download_games.json.

Setiap game punya:
  slug : kode game
  name : nama publisher / developer
  dev  : nama game
  icons: daftar gambar (logo publisher, wallpaper, character)
  links: daftar {label, url} sumber resmi

Jalankan: python build_download.py
Output: download.html (penuh)
"""
import json
import pathlib

BASE = pathlib.Path(__file__).parent
GAMES = json.loads((BASE / "_download_games.json").read_text(encoding="utf-8"))


def build_download():
    sections = []

    # ---- Section 1: Wallpaper Resmi per Game ----
    section1 = {
        "icon": "img/section-wallpaper.png",
        "title": "&#128444; Wallpaper Resmi per Game",
        "intro": (
            "Semua wallpaper di bawah milik masing-masing publisher. Klik untuk membuka galeri resmi "
            "mereka, lalu unduh langsung dari sana supaya resolutionsnya tetap HD dan usage-nya sesuai "
            "hak cipta."
        ),
        "cards": [],
    }

    # ---- Section 2: Marvel dan Film ----
    section2 = {
        "icon": "img/section-mcu.png",
        "title": "&#127916; Marvel dan Film",
        "intro": (
            "Materi visual MCU: poster, artwork, behind the scene, dan galeri resmi dari Marvel Studios."
            " Download langsung dari situs resmi atau platform streaming legal."
        ),
        "cards": [],
    }

    # ---- Section 4: Panduan Gratis ----
    section4 = {
        "icon": "img/section-guide.png",
        "title": "&#128214; Panduan Gratis",
        "intro": (
            "Semua panduan Starwise ditulis sendiri dan gratis dibaca langsung di halaman ini, "
            "tanpa perlu unduh file."
        ),
        "cards": [],
    }

    # ---- Section 5: Platform Streaming Legal ----
    section5 = {
        "icon": "img/section-stream.png",
        "title": "&#127916; Platform Streaming Legal",
        "intro": (
            "Tonton anime dan film lewat layanan berbayar ini. Hindari situs streaming ilegal."
        ),
        "cards": [],
    }

    for g in GAMES:
        slug = g["slug"]
        name = g["name"]
        dev = g["dev"]
        icons = g["icons"]
        links = g["links"]

        # pilih 1 gambar: logo publisher bila ada, lain Kali juka ada thumbnail video
        img = icons[0] if icons else "img/placeholder.jpg"

        # tips otomatis
        tips = []
        if "youtube" in slug:
            tips.append("Channel YouTube resmi memuat character PV, key visual, dan materi resmi.")
        elif slug in ("hsr", "sss", "zzz", "nte"):
            tips.append("HoYoLab memuat poster karakter, wallpaper, dan artwork event.")
        elif slug == "wuthering":
            tips.append("Steam Workshop berisi wallpaper yang diunggah langsung oleh pemain.")
        elif slug == "endfield":
            tips.append("Channel YouTube resmi memuat character PV dan key visual.")
        tips_html = "".join("<li>%s</li>" % t for t in tips)

        # link
        links_html = "".join(
            '<a href="{url}" target="_blank" rel="noopener">{label} &rarr;</a>'.format(**l)
            for l in links
        )

        # kategori
        category = "Game" if slug != "marvel" else "Marvel"

        card = """
      <article class="source-card">
        <div class="source-head">
          <img src="{img}" alt="{name}" loading="lazy" decoding="async">
          <div>
            <h3>{name}</h3>
            <p class="source-dev">{dev}</p>
          </div>
        </div>
        <ul class="tip-list">
          {tips}
        </ul>
        <div class="source-links">
{links}
        </div>
      </article>""".format(
            img=img, name=name, dev=dev, tips=tips_html, links=links_html
        )

        # map ke section yang tepat
        if slug == "marvel":
            section2["cards"].append(card)
        elif slug == "wuthering":
            section1["cards"].append(card)
        elif slug == "genshin":
            section1["cards"].append(card)
        elif slug == "hsr":
            section1["cards"].append(card)
        elif slug == "zzz":
            section1["cards"].append(card)
        elif slug == "endfield":
            section1["cards"].append(card)
        elif slug == "nte":
            section1["cards"].append(card)
        elif slug == "marvel":
            section2["cards"].append(card)
        else:
            section1["cards"].append(card)

    return sections, section1, section2, section4, section5


if __name__ == "__main__":
    sections, s1, s2, s4, s5 = build_download()
    print("Generator download siap")
    for s in sections:
        print("  Section:", s["title"])
    print("  cards section1:", len(s1["cards"]))
    print("  cards section2:", len(s2["cards"]))
