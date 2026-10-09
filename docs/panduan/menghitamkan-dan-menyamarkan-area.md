# Menghitamkan dan menyamarkan area

Modul `zul.computer_vision.masks` menyembunyikan bagian frame dengan dua cara:

- **Menghitamkan area sebelum deteksi.** Orang di area yang dihitamkan tidak pernah terdeteksi, jadi tidak ikut dihitung. Misalnya lantai mal di seberang toko, atau semua yang ada di luar area yang kamu ukur.
- **Menyamarkan kotak di frame hasil.** Blur dan pixelate menyamarkan isi kotak, misalnya wajah atau badan orang, sebelum videonya dibagikan.

**Sebelum mulai:** install Zul dengan extra `vision`:

```shell
pip install "zul[vision] @ git+https://github.com/kazuma313/zul_utilities.git"
```

Contoh di halaman ini memakai frame buatan berwarna gradasi, supaya area yang dihitamkan atau disamarkan terlihat jelas.

## Menghitamkan area sebelum deteksi

1. Buat masker sekali, sebelum perulangan frame. `polygon_mask` menerima daftar poligon dan ukuran frame:

    ```python title="masker_area.py"
    import cv2
    import numpy as np

    from zul.computer_vision import masks

    frame = np.zeros((360, 640, 3), dtype=np.uint8)
    frame[:, :, 0] = np.linspace(60, 220, 640).astype(np.uint8)
    frame[:, :, 1] = np.linspace(220, 60, 360).astype(np.uint8)[:, None]

    measured = [[120, 40], [520, 40], [600, 320], [40, 320]]
    mask = masks.polygon_mask([measured], width=640, height=360, keep_inside=True)

    cv2.imwrite("masker_area.png", masks.apply_mask(frame, mask))
    ```

    ![Frame gradasi yang hanya terlihat di dalam sebuah trapesium; semua di luarnya hitam](../assets/computer-vision/masker_area.png)

    Dengan `keep_inside=True`, semua di luar poligon dihitamkan. Dengan `keep_inside=False`, bawaannya, isi poligon yang dihitamkan.

2. Di setiap frame, hitamkan area itu sebelum frame masuk ke model:

    ```python
    prepared, scale = standardise_frame(masks.apply_mask(frame, mask))
    people = detect(model, prepared).rescale(scale)
    ```

    `apply_mask` mengembalikan salinan, jadi `frame` asli tetap utuh untuk digambar dan disimpan.

3. Jika ada lebih dari satu masker, misalnya area yang diukur dan area yang diabaikan, gabungkan keduanya sekali di awal:

    ```python
    mask = masks.combine_masks(
        masks.polygon_mask(measured, width, height, keep_inside=True),
        masks.polygon_mask(ignored, width, height),
    )
    ```

    Dengan satu masker gabungan, setiap frame cukup satu operasi. `combine_masks` melewati masker `None`, misalnya dari `polygon_mask` tanpa poligon.

Masker diterapkan ke frame yang masuk ke model, bukan ke kotak hasil deteksi. Karena itu, orang di area yang dihitamkan tidak pernah punya kotak, tidak masuk ke tracker, dan tidak bisa terhitung dua kali.

## Menyamarkan kotak

`blur_boxes` mengaburkan isi setiap kotak, dan `pixelate_boxes` mengubahnya menjadi blok-blok besar. Keduanya mengubah frame langsung:

```python title="samarkan_kotak.py"
import cv2
import numpy as np

from zul.computer_vision import masks

frame = np.zeros((360, 640, 3), dtype=np.uint8)
frame[:, :, 0] = np.linspace(60, 220, 640).astype(np.uint8)
frame[:, :, 1] = np.linspace(220, 60, 360).astype(np.uint8)[:, None]
for x in (90, 390):
    cv2.putText(frame, "WAJAH", (x, 190), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (255, 255, 255), 4)

masks.blur_boxes(frame, np.array([[70, 120, 290, 230]]), kernel=31)
masks.pixelate_boxes(frame, np.array([[370, 120, 590, 230]]), pixel_size=16)

cv2.imwrite("samarkan_kotak.png", frame)
```

![Dua tulisan WAJAH di frame gradasi: yang kiri kabur, yang kanan berupa blok-blok besar](../assets/computer-vision/samarkan_kotak.png)

`kernel` yang lebih besar membuat blur lebih kabur, dan `pixel_size` yang lebih besar membuat bloknya lebih besar. Bagian kotak di luar tepi frame dipotong lebih dulu, jadi kotak di tepi frame tidak menyebabkan error.

## Menyamarkan wajah dari keypoint pose

Untuk menyamarkan wajah saja, ambil kotak di sekeliling keypoint wajah dengan `pose.face_box`, lalu perlebar kotaknya sedikit:

```python
from zul.computer_vision import masks, pose

for xy, conf in zip(people.keypoints_xy, people.keypoints_conf):
    face = pose.face_box(xy, conf)
    if face is not None:
        masks.blur_boxes(annotated, [face + [-15, -15, 15, 15]])
```

`face_box` mengembalikan `None` jika kurang dari dua keypoint wajah terlihat, misalnya orang yang membelakangi kamera. Untuk menyamarkan seluruh badan, pakai `masks.blur_boxes(annotated, people.xyxy)`.

Samarkan frame hasil, setelah deteksi. Frame yang disamarkan sebelum deteksi membuat model kehilangan wajah dan keypoint yang ia butuhkan.

## Halaman terkait

- [Mendeteksi dan melacak orang](mendeteksi-dan-melacak-orang.md) untuk perulangan frame tempat masker dipakai.
- [Cara kerja Computer Vision](../konsep/cara-kerja-computer-vision.md#masker-dan-ukuran-input) untuk alasan menghitamkan area sebelum deteksi.
- [Referensi Computer Vision](../referensi/computer-vision.md#masks) untuk semua parameter masker, blur, dan pixelate.
