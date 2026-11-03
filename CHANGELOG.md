# Changelog

## Streaming (Halaman baru - Simpel & Rapi, Max 3 Video per Judul)

### Perubahan utama:
1. **Streaming halaman utama** (`pages/streaming.html`) - Sudah diupdate
   - Halaman kategori menggunakan `assets/img/logo-*.jpg`
   - Menu "Playlist Anime" hany 1 halaman, menampilkan 8 judul anime
   - Setiap judul: **max 3 video** (tidak seperti sebelumnya 12-24 video)
   - Tampilkan: judul + 3 thumbnail video + "Buka di YouTube" link

2. **Folder structure** - Diorganisir rapi:
   - `pages/` - Halaman frontend
   - `build/<game>/` - 266 halaman build per game
   - `data/` - _*.json
   - `scripts/` - build_*.py
   - `assets/` - img/, css/, js/

3. **Vercel clean URL rewrite** - `vercel.json` sekarang memetakan ke `/pages/`

### Build yang sudah terpush:
- 6 halaman streaming (per game) tetap menggunakan iframe
- 1 halaman streaming.html (halaman utama) - kategori + playlist max 3 video
- 266 halaman build terorganisir
- 11 script generator
- 21 file data JSON
- 1759 file assets (img, css, js)

### Fitur YouTube Playlist:
- 8 judul anime: Mushoku Tensei Full Series, Mushoku Tensei S3, BLACK TORCH, Draw This Then Die!, KAIJU GIRL CARAMELISE, BanG Dream! YUME∞MITA, Exiled Heavy Knight, World's Strongest Rearguard
- Setiap judul: 3 thumbnail terbaru + link playlist lengkap
- Halaman tetap cepat karena hanya 3 thumbnail per judul
