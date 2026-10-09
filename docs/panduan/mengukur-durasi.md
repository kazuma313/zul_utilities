# Mengukur durasi per orang

Modul `zul.computer_vision.timers` berisi dua timer yang mengubah hasil per frame menjadi catatan dengan awal, akhir, dan durasi:

- `ZoneTimer` mencatat berapa lama setiap orang berada di setiap zona.
- `ConditionTimer` mencatat berapa lama sebuah kondisi benar untuk setiap orang, misalnya "menghadap rak" atau "wajah terlihat", dan bisa dipisah per zona.

Kedua timer hanya menerima id track dan hasil uji per frame, jadi contoh di halaman ini memakai data buatan dan bisa dijalankan tanpa model. Keduanya hanya butuh instalasi dasar Zul.

Waktu selalu dalam detik dari awal video. Di video, `timestamp_s` datang dari [`read_frames`](mendeteksi-dan-melacak-orang.md).

## Mengukur lama di zona

`ZoneTimer` menerima indeks zona setiap orang per frame, misalnya dari `geometry.zone_membership`, dan mencatat satu kunjungan setiap kali seseorang masuk ke sebuah zona. Contoh berikut menjalankan satu orang selama 6 detik pada 10 frame per detik: 3 detik di `rak_a`, lalu pindah ke `rak_b`:

```python title="lama_di_zona.py"
from zul.computer_vision.report import RecordWriter
from zul.computer_vision.timers import ZoneTimer, ZoneVisit

visits = ZoneTimer(["rak_a", "rak_b"], grace_s=1.0)

for frame_number in range(60):
    timestamp_s = frame_number / 10
    zone = 0 if timestamp_s < 3 else 1
    visits.update(frame_number, timestamp_s, [1], [zone])
visits.close_all()

with RecordWriter("kunjungan.csv", ZoneVisit) as writer:
    writer.write(visits.completed)
```

Script itu menulis `kunjungan.csv`:

```text
visit_id,track_id,zone_index,zone_name,enter_frame,enter_time_s,exit_frame,exit_time_s
1,1,0,rak_a,0,0.0,29,2.9
2,1,1,rak_b,30,3.0,59,5.9
```

Sebuah kunjungan selesai dengan dua cara:

- Orang itu pindah ke zona lain. Kunjungan lama langsung ditutup.
- Orang itu tidak terlihat di zona selama `grace_s` detik. Waktu keluarnya adalah saat ia terakhir terlihat, bukan saat grace habis.

Selama jedanya lebih pendek dari `grace_s`, track yang hilang sebentar, misalnya tertutup orang lain, tetap satu kunjungan.

Untuk angka ringkasan per zona, pakai method berikut:

| Method | Isi |
|---|---|
| `visit_count(zona)` | Jumlah kunjungan ke zona itu. |
| `unique_visitors(zona)` | Jumlah orang berbeda yang pernah di zona itu. |
| `dwell_s(track_id, timestamp_s)` | Sudah berapa lama orang itu di zonanya sekarang, misalnya untuk label di layar. |
| `zone_of(track_id)` | Zona orang itu sekarang, atau `None`. |

## Mengukur lama sebuah kondisi

Berada di zona belum tentu berarti melakukan sesuatu di zona itu. `ConditionTimer` mengukur waktu saat sebuah kondisi benar. Contoh berikut mengukur seseorang yang berdiri di `rak_a` selama 8 detik, tetapi hanya menghadap raknya dari detik 1 sampai 5:

```python title="lama_kondisi.py"
from zul.computer_vision.timers import ConditionTimer

looking = ConditionTimer(minimum_s=3.0, frame_period_s=0.1, group_labels=["rak_a"])

for frame_number in range(80):
    timestamp_s = frame_number / 10
    facing = 1.0 <= timestamp_s < 5.0
    looking.update(frame_number, timestamp_s, [1], [facing], groups=[0])
looking.close_all()

for spell in looking.completed:
    print(spell.group_name, f"{spell.active_s:.1f}", f"{spell.span_s:.1f}")
```

Script itu mencetak `rak_a 3.9 7.9`: orang itu terlihat di rak selama 7,9 detik (`span_s`) dan menghadapnya selama 3,9 detik (`active_s`).

Setiap pemanggilan `update` menerima dua daftar per baris:

- `active`: hasil kondisinya, misalnya dari [`pose.facing_zone_targets`](membaca-arah-hadap-dan-jarak.md).
- `groups`: opsional, misalnya indeks zona. Waktu dihitung terpisah per grup, dan baris dengan grup `-1` dilewati. Tanpa `groups`, setiap orang punya satu rentang.

Sebuah rentang hanya dicatat jika `active_s` mencapai `minimum_s`. Dengan `minimum_s=3.0`, orang yang hanya melirik rak selama 2 detik tidak dicatat.

## Mengatur jeda dan batas kredit

Track bisa hilang beberapa frame, misalnya saat orang tertutup orang lain. Dua parameter `ConditionTimer` menangani jeda itu:

| Parameter | Bawaan | Gunanya |
|---|---|---|
| `grace_s` | `1.0` | Rentang tetap terbuka selama track hilang paling lama sekian detik. |
| `frame_period_s` | `1/30` | Jarak waktu antar frame yang kamu proses, yaitu `stride / fps`. Menentukan batas kredit. |

Batas kredit adalah waktu terbanyak yang dihitung dari satu jeda antar pengamatan: `min(2 × frame_period_s, 0,25 × minimum_s)`. Dengan begitu, dua pengamatan berjarak 0,9 detik tidak dihitung sebagai 0,9 detik menghadap tanpa putus. Isi `frame_period_s` sesuai video, misalnya `3 / 30` jika kamu memproses satu dari setiap tiga frame video 30 fps. Alasan pemisahan grace dan batas kredit ada di [Cara kerja Computer Vision](../konsep/cara-kerja-computer-vision.md#grace-dan-batas-kredit).

## Membaca angka ringkasan

`ConditionTimer` punya method ringkasan untuk satu grup, atau untuk semua grup jika `group` tidak diisi:

| Method | Isi |
|---|---|
| `count(group)` | Jumlah rentang yang sudah dicatat. |
| `qualified(group)` | `count`, ditambah rentang terbuka yang sudah mencapai `minimum_s`. Cocok untuk angka di layar. |
| `people(group)` | Jumlah orang berbeda dengan rentang yang dicatat. |
| `seconds(group)` | Total `active_s` rentang yang dicatat. |
| `active_s(track_id, group)` | Waktu aktif rentang yang sedang terbuka, untuk label di layar. |
| `reached(track_id, group)` | Apakah orang itu sudah mencapai `minimum_s`. |

## Menyimpan catatan ke CSV

`RecordWriter` menulis catatan apa pun ke CSV, satu baris per catatan. Kolomnya bisa diambil dari kelas catatan, seperti `ZoneVisit` di [Mengukur lama di zona](#mengukur-lama-di-zona), atau kamu pilih sendiri, termasuk property seperti `span_s`:

```python
from zul.computer_vision.report import RecordWriter

columns = ["track_id", "group_name", "start_time_s", "active_s", "span_s"]

with RecordWriter("outputs/perhatian.csv", columns) as writer:
    for frame_number, timestamp_s, frame in read_frames(video_path):
        ...
        writer.write(
            looking.update(frame_number, timestamp_s, ids, facing, groups=membership)
        )
    writer.write(looking.close_all())
```

`update` mengembalikan rentang yang selesai di frame itu, jadi baris ditulis begitu kejadiannya selesai. File disimpan ke disk setelah setiap baris, jadi jika script berhenti di tengah, baris yang sudah ditulis tetap ada. Header tetap ditulis meski tidak ada kejadian.

## Halaman terkait

- [Menghitung dengan garis dan poligon](menghitung-dengan-garis-dan-poligon.md) untuk `zone_membership` dan penghitung lainnya.
- [Membaca arah hadap dan jarak](membaca-arah-hadap-dan-jarak.md) untuk kondisi seperti "menghadap rak".
- [Referensi Computer Vision](../referensi/computer-vision.md#timers) untuk semua parameter timer.
