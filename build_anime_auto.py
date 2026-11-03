
# -*- coding: utf-8 -*-
"""Auto-update halaman anime Starwise.

Fungsi:
  1. Update playlist data dari YouTube channel (MuseAsia)
  2. Reset embed status untuk cek video baru
  3. Rebuild anime.html

Jalankan: python build_anime_auto.py
"""
import json
import pathlib
import subprocess
import urllib.request
import ssl
import re
import time

BASE = pathlib.Path(__file__).parent
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120"}
ctx = ssl.create_default_context()

def fetch_channel_videos(handle, max_results=20):
    """Ambil video terbaru dari YouTube channel"""
    url = f"https://www.youtube.com/@{handle}/videos?view=0&sort=dd"
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=20, context=ctx) as r:
            html = r.read().decode(errors="ignore")
        
        videos = []
        # Pattern: ambil videoId dan title dari videoRenderer
        for m in re.finditer(r'"videoRenderer":\{[^}]*"videoId":"([^"]+)"[^}]*"title":\{[^}]*"simpleText":"([^"]+)"', html):
            vid = m.group(1)
            title = m.group(2)
            if len(title) > 3 and "YouTube" not in title:
                videos.append({"videoId": vid, "title": title[:120]})
        return videos
    except Exception as e:
        print(f"  Error fetching @'{handle}': {e}")
        return []

def check_embed(vid):
    """Cek apakah video bisa di-embed via oEmbed API"""
    oembed = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    try:
        req = urllib.request.Request(oembed, headers=UA)
        with urllib.request.urlopen(req, timeout=10, context=ctx) as r:
            data = json.loads(r.read().decode())
            return data.get("is_embeddable", True)
    except Exception:
        return False

def get_existing_playlist_ids():
    """Dapatkan ID playlist yang sudah ada"""
    path = BASE / "_muse_playlists.json"
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {p.get("pid", "") for p in data}

def update_playlist_data():
    """Update playlist data dari channel YouTube"""
    # Baca playlist yang sudah ada
    path = BASE / "_muse_playlists.json"
    if not path.exists():
        print("  Tidak ada file _muse_playlists.json")
        return
    
    playlists = json.loads(path.read_text(encoding="utf-8"))
    existing_pids = get_existing_playlist_ids()
    
    # Cari playlist yang baru
    print(f"  Playlist yang ada: {len(existing_pids)}")
    
    # Update embed status untuk semua video yang ada
    embed_path = BASE / "_embed_status.json"
    embed = json.loads(embed_path.read_text(encoding="utf-8")) if embed_path.exists() else {}
    
    # Cek embed status untuk semua video playlist
    updated = 0
    for p in playlists:
        for vid in p.get("videos", []):
            if vid not in embed:
                embed[vid] = check_embed(vid)
                updated += 1
                time.sleep(0.3)
    
    embed_path.write_text(json.dumps(embed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  Update embed status: {updated} video")
    
    # Hitung total video baru
    total_videos = sum(len(p.get("videos", [])) for p in playlists)
    print(f"  Total video dalam playlist: {total_videos}")
    
    # Hitung embedable vs non-embeddable
    embeddable = sum(1 for v in embed.values() if v)
    non_embeddable = len(embed) - embeddable
    print(f"  Embedable: {embeddable}, Non-embeddable: {non_embeddable}")

def rebuild_anime_html():
    """Rebuild anime.html"""
    r = subprocess.run(["python", "build_anime.py"], capture_output=True, text=True, cwd=BASE)
    print("  Build anime.html:", r.stdout.strip(), r.stderr.strip())
    if r.returncode != 0:
        print("  ERROR: Build failed!")

if __name__ == "__main__":
    print("=== Auto-update Anime Starwise ===")
    update_playlist_data()
    rebuild_anime_html()
    print("=== Selesai ===")
