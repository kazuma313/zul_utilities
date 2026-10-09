"""
Computer vision untuk video: fungsi-fungsi kecil yang bisa dirangkai sendiri.

Gunanya:
    Setiap modul mengerjakan satu hal, misalnya teks di sudut frame, garis
    penghitung, atau poligon penghitung, dan tidak terikat pada satu kasus.
    Kamu merangkainya sendiri sesuai kebutuhan. Setiap nilai masuk lewat
    argumen, jadi tidak ada pengaturan global.

Modul dan extra yang dibutuhkan:
    geometry    titik jangkar kotak, poligon, zona, dan arah      tanpa extra
    pose        arah kepala dan badan dari keypoint COCO-17         tanpa extra
    zones       poligon penghitung dan garis penghitung             tanpa extra
    timers      lama di zona dan lama sebuah kondisi benar          tanpa extra
    distance    jarak dalam meter dan lama dua orang berdekatan     tanpa extra
    config      config dari YAML dan validasinya                    tanpa extra
    report      CSV dengan satu baris per catatan                   tanpa extra
    draw        teks, kotak, garis, poligon, jejak, dan heatmap     zul[vision]
    masks       menghitamkan area, blur, dan pixelate               zul[vision]
    video       membaca, menulis, dan mengukur kecepatan            zul[vision]
    tracking    ByteTrack: id yang sama di setiap frame             zul[tracking]
    detection   model RF-DETR: kotak orang dan keypoint pose        zul[detection]
    weights     mengunduh bobot model ke folder proyek              zul[detection]

Cara pakai:
    from zul.computer_vision import draw, zones

Paket ini tidak mengimpor modul apa pun saat diimpor, jadi modul yang
butuh OpenCV atau RF-DETR hanya dimuat ketika benar-benar dipakai.
"""
