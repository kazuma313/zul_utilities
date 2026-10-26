## Apa yang berubah

<!-- Satu tujuan saja. Sebut file atau modul yang disentuh. -->

## Kenapa

<!-- Masalah yang diselesaikan. Tautkan issue jika ada. -->

## Cara menguji

<!-- Perintah yang bisa dijalankan reviewer, dan hasil yang diharapkan. -->

## Bantuan AI

- [ ] Saya tidak memakai code assistant.
- [ ] Saya memakai code assistant.
  - Alat dan model:
  - Bagian yang dibantu:
  - Yang saya periksa sendiri:

## Hasil pemeriksa

<!-- Tempel keluaran asli, bukan ringkasan dari ingatan. -->

```text
uv run pytest
uv run black --check framework docs/tools
uv run ruff check framework docs/tools
uv run python framework/scripts/comment_style.py
uv run mkdocs build --strict
```

## Daftar periksa

- [ ] Pull request ini punya satu tujuan, dan perubahannya di bawah 400 baris di luar test dan dokumentasi.
- [ ] Ada test untuk perubahan ini. Untuk bug, test itu gagal sebelum perbaikan.
- [ ] Tidak ada library pihak ketiga yang diimpor di luar `framework/src/zul/adapters/`.
- [ ] Tidak ada dependency baru, atau lisensinya sudah diperiksa dan bukan AGPL atau GPL.
- [ ] Tidak ada API key, token, video, bobot model, atau file besar.
- [ ] Dokumentasi diperbarui dan sudah dicocokkan dengan kode.
- [ ] Tidak ada perubahan di `research/`, `.github/`, atau `uv.lock` yang tidak dijelaskan.
- [ ] Tidak ada format ulang atau pemindahan file yang tidak berkaitan.
