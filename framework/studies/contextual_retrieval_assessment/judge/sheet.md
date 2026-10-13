# Judging sheet: 34 chunks x 3 contexts, labels shuffled per chunk

Score every context 1-5 on: faithful, situates, specific, form (see judge_sheet.py).

## Pc3GWaOWHLk#0  (Cara Coach Justin Menghadapi Ketidakpastian Hidup)
Section: Transcript

```text
Hola, saya Justinus Laksana. E selamat datang di kelas pakar Malaka. Kali ini saya ingin share pengalaman sebagai ee sebagai pria yang menikmati hidup dalam arti tidak tergantung oleh hal material dan immaterial. Caranya bagaimana? Jadi saya di usia 59 melihat banyak sekali Genzet, terutama Genzet milenial yang cepat banget down. Gua mau share aja ya. Gue itu dari umur 12 sampai 32 tahun besar di Belanda. Gue selalu bilang gue itu besar di jalanan, tapi jalanannya di Belanda, bukan di sini. Bedanya apa? Bedanya adalah lu diajarin sama teman-teman Belanda gue itu untuk independen, untuk enggak cengeng. Alhasil dari SMP, dari SMP, literally SMP itu gua semua ngurus sendiri. Kok gua tinggal kasih duit tanda tangan itu mau kursus ini mau ikut bola ikut ini ke mana-mana itu semua gua nyokapin enggak pernah gua ribetin dengan gaya seperti ini itu membuat gue mungkin lebih cepat dewasa daripada yang lain membuat mental gue lebih diterpa daripada anak-anak yang ee yang dimanja yang terlalu diprotect oleh orang tuanya.
```

- **A**: Ini adalah kutipan dari Justinus Laksana di video YouTube "Cara Coach Justin Menghadapi Ketidakpastian Hidup" yang menjelaskan pengalamannya membangun kemandirian sejak remaja dengan dukungan teman-temannya di Belanda.
- **B**: Justinus Laksana membuka sesi kelas pakar MALAKA dengan menceritakan pengalamannya tumbuh di Belanda yang membentuk mentalnya menjadi mandiri dan tidak tergantung.
- **C**: Chunk ini adalah pembuka video Malaka yang diucapkan oleh Justinus Laksana, berbicara tentang pengalaman membangun kemandirian sejak remaja di Belanda hingga menghadapi tantangan hidup di Indonesia.

## Pc3GWaOWHLk#3  (Cara Coach Justin Menghadapi Ketidakpastian Hidup)
Section: Transcript

```text
Nanti pelan-pelan alam ini yang akan ngatur lu ke mana. Whatever tantangan lu, yang dibuild itu mental. Bukan lu kerja di IT, lu kerja jadi dokter, lu kerja sebagai jualan tahu atau apa, enggak. Itu hanya produk and produk. Produk itu bisa berbeda. Kalau lu punya mindset yang benar, apapun lu bisa lakukan. Waktu gua datang, gue jualan kertas. Emang gua orang tanya, "Emang kok suka jualan kertas?" Enggak. Karena gua butuh job untuk survive. Jadi mau jualan kertas pun gua ladenin, gua pelajari cara e kertas, produk kertas itu seperti apa. Yang penting lu bisa jualan atau enggak? Jualan itu kan meyakinkan orang. Meyakinkan pada saat lu bisa meyakinkan gimana, lu bisa meyakinkan lu harus menguasai yang namanya komunikasi. Gua enggak pernah kuliah komunikasi, gua kuliah political sains. Tapi di dalam political sains diajarin cara berdiskusi seperti apa. Nah, ini yang gua gunakan untuk meyakinkan klien biar gua bisa jualan banyak, biar gua bisa tetap dapat job, biar gua bisa dapat gaji tiap bulan, biar gua bisa hidup karena gua harus survive di sini.
```

- **A**: Chunk ini menjelaskan tentang pentingnya mindset dan komunikasi dalam menghadapi tantangan hidup, serta contoh pengalaman Justinus Laksana menjual kertas untuk bertahan hidup di Indonesia.
- **B**: Ini adalah bagian dari video oleh Justinus Laksana dalam Kelas Pakar MALAKA yang membahas pentingnya mental dan mindset kuat dalam menghadapi berbagai tantangan hidup, khususnya bagaimana cara bertahan hidup dengan sumber daya terbatas.
- **C**: Chunk ini bercerita tentang cara Justinus Laksana membangun mental kuat untuk beradaptasi dengan tantangan hidup, dengan contoh menjual kertas sebagai cara survive. Fokus pada pentingnya mindset dan komunikasi daripada kekayaan.

## Pc3GWaOWHLk#6  (Cara Coach Justin Menghadapi Ketidakpastian Hidup)
Section: Transcript

```text
Itu jauh lebih penting dari hanya sekedar duit. Jadi kalau lu mau maju, modal itu bukan duit. Modal itu hal-hal yang lain yang enggak bisa dipegang. Itu jauh lebih penting agar lu bisa maju di mana pun lu berada. Mungkin lu pada suatu lu dapat penawaran untuk kerja atau sekolah di luar negeri, beasiswa terus dapat apa semua bisa terjadi. Nah, kalau lu punya modal mental mindset itu you will survive dan lu akan sukses. Kok bisa 10 orang terkaya mayoritas do semua di dunia? Ya, ya karena itu mereka punya mental. Jadi, jangan pikir lu lulusan Harvard lu langsung jadi hebat. Enggak. It doesn't work like that. Tapi satu-satunya mental yang lu tidak dapat dari sekolah manaun atau dari keluarga manaun itu harus bangun sendiri, harus bentuk sendiri. Dan membentuk mental itu proses go up and down, ups and down. Belajar dari kesalahan.

Jangan takut bikin kesalahan. Belajar dari kesalahan itu membuat lu jadi kuat. Oke, jangan kelamaan entar habis bahannya. Thanks for watching.
```

- **A**: Dalam video Justinus Laksana, chunk ini menjelaskan pentingnya mental dan mindset dalam keberhasilan, serta mengingatkan bahwa keberhasilan tidak hanya bergantung pada pendidikan atau uang.
- **B**: ini berisi penjelasan tentang pentingnya mental dan mindset dibandingkan duit untuk kesuksesan, disampaikan oleh Justinus Laksana dalam kelas pakar MALAKA.
- **C**: Ini adalah bagian akhir dari video oleh Justinus Laksana di Kelas Pakar MALAKA, yang berisi nasihat penting tentang kekuatan mental dan mindset sebagai modal utama untuk meraih kesuksesan, terlepas dari latar belakang atau sumber daya yang dimiliki.

## 6c14acc799cc#2  (Menyimpan dan mencari vektor di Milvus)
Section: Menyimpan dan mencari vektor di Milvus > Menyiapkan helper dan file config

```text
```json title="milvus_config.json"
    {
        "connection": {
            "uri": "http://localhost",
            "port": 19530,
            "db_name": "default"
        },
        "collections": [
            {
                "collection_name": "my_collection",
                "shards_num": 2,
                "description": "My first collection",
                "milvus_schema": {
                    "auto_id": true,
                    "enable_dynamic_field": true,
                    "fields": [
                        {
                            "field_name": "id",
                            "datatype": "VARCHAR",
                            "max_length": 128,
                            "is_primary": true
                        },
                        {
                            "field_name": "embedding",
                            "datatype": "FLOAT_VECTOR",
                            "dim": 768
                        }
                    ],
                    "functions": []
                },
                "indexes": [
                    {
                        "field_name": "embedding",
                        "index_name": "emb_idx",
                        "index_type": "HNSW",
                        "metric_type": "COSINE",
                        "params": {
                            "M": 16,
                            "efConstruction": 200
                        }
                    }
                ]
            }
        ]
    }
```

- **A**: Chunk ini adalah konfigurasi file milvus_config.json yang digunakan untuk menyiapkan collection di Milvus dengan skema dan indeks yang diperlukan.
- **B**: Bagian ini menjelaskan konfigurasi awal collection my_collection di Milvus, termasuk skema field seperti id dan embedding, serta indeks HNSW untuk pencarian vektor yang efisien.
- **C**: Dokumen Menyimpan dan mencari vektor di Milvus. Chunk ini berisi konfigurasi awal untuk membuat collection Milvus dengan nama my_collection dan skema field serta indeks yang diperlukan.

## 6c14acc799cc#5  (Menyimpan dan mencari vektor di Milvus)
Section: Menyimpan dan mencari vektor di Milvus > Mencari vektor termirip

```text
1. Ubah teks query menjadi vektor dengan model yang sama:

    ```python
    query_vector = embedding.encode("dokumen").flatten().tolist()
    ```

2. Cari vektor yang paling mirip dengan `search`:

    ```python
    hits = milvus.search(
        collection_name="my_collection",
        query_vectors=[query_vector],
        anns_field="embedding",
        limit=5,
        output_fields=["id"],
    )
    ```

    `query_vectors` berupa daftar, jadi kamu bisa mengirim beberapa query sekaligus. Hasilnya adalah satu daftar hasil untuk setiap query, dalam format `pymilvus`.

3. Untuk mempersempit pencarian, tambahkan argumen kata kunci lain. Argumen itu diteruskan ke `MilvusClient.search`. Contoh berikut menambah filter:

    ```python
    hits = milvus.search(
        collection_name="my_collection",
        query_vectors=[query_vector],
        anns_field="embedding",
        limit=5,
        filter='kategori == "peraturan"',
    )
    ```
```

- **A**: Dokumen menjelaskan cara mencari vektor termirip menggunakan MilvusHelper, termasuk contoh kode dan penjelasan penggunaan filter untuk mempersempit pencarian.
- **B**: Chunk ini berada di bagian 'Mencari vektor termirip' dari dokumen 'Menyimpan dan mencari vektor di Milvus'. Chunk menjelaskan cara mengubah teks query menjadi vektor dan menggunakan search untuk menemukan vektor termirip dengan filter.
- **C**: Chunk ini berasal dari bagian "Mencari vektor termirip" pada dokumen "Menyimpan dan mencari vektor di Milvus". Bagian ini menjelaskan cara melakukan pencarian vektor yang mirip dengan Milvus, termasuk cara mengirim query dan menambahkan filter.

## 6c14acc799cc#8  (Menyimpan dan mencari vektor di Milvus)
Section: Menyimpan dan mencari vektor di Milvus > Menyiapkan collection untuk BM25

```text
Milvus bisa membuat vektor sparse BM25 dari sebuah field teks. Bagian ini menyiapkan collection yang menyimpan vektor dense dan vektor sparse sekaligus, sebagai dasar hybrid search.

1. Tulis config dengan tiga hal: field teks yang memakai `enable_analyzer`, field bertipe `SPARSE_FLOAT_VECTOR`, dan satu entri `functions` yang menghubungkan keduanya:
```

- **A**: Dokumen Menyimpan dan mencari vektor di Milvus. Chunk ini menjelaskan persiapan collection untuk pencarian hybrid dengan vektor dense dan sparse BM25.
- **B**: Ini adalah bagian dari dokumentasi tentang menyiapkan collection Milvus untuk pencarian hybrid dengan BM25. Bagian ini menjelaskan cara mengkonfigurasi collection yang menyimpan vektor dense dan sparse sekaligus.
- **C**: Dokumen 'Menyimpan dan mencari vektor di Milvus' menjelaskan cara membuat collection Milvus yang mendukung pencarian hybrid dengan vektor dense dan sparse. Chunk ini berbicara tentang persiapan konfigurasi untuk mengintegrasikan BM25 dalam sistem.

## 6c14acc799cc#11  (Menyimpan dan mencari vektor di Milvus)
Section: Menyimpan dan mencari vektor di Milvus > Memeriksa hasilnya

```text
Untuk memastikan collection sudah dibuat dan terisi, cetak daftar collection dan statistiknya:

```python
print(milvus.list_collections())
print(milvus.get_collection_stats("my_collection"))
```

Baris pertama mencetak daftar yang memuat nama collection dari config, misalnya `my_collection`. Baris kedua mencetak dict statistik dari Milvus. Kunci `row_count` di dict itu berisi jumlah baris.

Helper menulis log lewat modul `logging`, tetapi tidak mengatur ke mana log itu pergi. Untuk melihat log koneksi, pembuatan collection, dan setiap operasi, aktifkan logging di awal program:

```python
import logging

logging.basicConfig(level=logging.INFO)
```
```

- **A**: ini berada di bagian 'Memeriksa hasilnya' dari dokumen 'Menyimpan dan mencari vektor di Milvus'. Chunk ini menjelaskan cara memeriksa koleksi dan statistiknya serta mengaktifkan logging.
- **B**: Dokumen Menyimpan dan mencari vektor di Milvus. Chunk ini menjelaskan cara memeriksa apakah collection sudah dibuat dan terisi dengan data, serta cara mengaktifkan logging untuk melacak operasi.
- **C**: Chunk ini berasal dari bagian "Memeriksa hasilnya" pada dokumen "Menyimpan dan mencari vektor di Milvus". Bagian ini menjelaskan cara memverifikasi keberhasilan pembuatan dan pengisian collection Milvus.

## 99d6393011a5#1  (Membuat mind map)
Section: Membuat mind map > Membuat mind map dari outline

```text
1. Tulis outline di file Markdown. Judul `#` menjadi pusat peta, butir tanpa indentasi menjadi cabang utama, dan butir yang menjorok dua spasi menjadi rinciannya:

    ```markdown title="fotosintesis-mindmap.md"
    # Fotosintesis
    - Bahan
      - Cahaya matahari
      - Air
      - Karbon dioksida
    - Reaksi terang
      - Membran tilakoid
      - ATP dan NADPH
    - Siklus Calvin
      - Fiksasi karbon
      - Glukosa
    ```

2. Jalankan skrip skill pada file itu:

    ```shell
    uv run python scripts/build_mindmap.py fotosintesis-mindmap.md -o fotosintesis.html --also svg
    ```

    Skrip menjawab dengan satu baris hasil dan lokasi file yang ditulisnya:

    ```text
    OK: created C:\proyek\fotosintesis.html (11 nodes, 3 branches, depth 2, 1196x230 px, theme=rainbow)
    SVG: C:\proyek\fotosintesis.svg
    ```

3. Buka file HTML itu di browser. Halamannya berjalan tanpa internet, bisa digeser dan diperbesar, dan punya tombol **Save PNG**.

Skrip memperbaiki sendiri outline yang bentuknya kurang rapi, lalu mencantumkan setiap perbaikan di bawah `AUTO-FIXED / WARNINGS`. Baca daftar itu: jika sebuah perbaikan mengubah maksud petamu, ubah outline-nya dan jalankan lagi perintahnya.
```

- **A**: Chunk ini berasal dari bagian "Membuat mind map dari outline" dalam dokumen tentang cara membuat mind map menggunakan skill mind_map. Bagian ini menjelaskan langkah-langkah untuk mengubah outline Markdown menjadi mind map dengan skrip build_mindmap.py.
- **B**: Chunk ini berada di bagian 'Membuat mind map dari outline' dalam dokumen 'Membuat mind map'. Chunk ini menjelaskan cara menulis outline dalam Markdown dan menjalankan skrip untuk membuat mind map dari file tersebut.
- **C**: Dokumen Membuat mind map menjelaskan cara membuat mind map dari outline dengan contoh fotosintesis dan langkah-langkahnya.

## 99d6393011a5#4  (Membuat mind map)
Section: Membuat mind map > Memilih model lokal

```text
Pakai `gemma3:4b` kecuali kamu punya alasan lain. Angka berikut diukur di laptop dengan GPU RTX 3060 6 GB dan Ollama 0.32.6:

| Model | Satu topik | Dokumen 5.000 karakter | Dokumen 13.700 karakter | Catatan |
|---|---|---|---|---|
| `gemma3:4b` | 8 sampai 10 detik | 10 sampai 24 detik | 16 sampai 98 detik | 16 dari 16 percobaan menghasilkan peta. Muat seluruhnya di GPU 6 GB. |
| `qwen3:4b` | 159 sampai 224 detik | 942 detik, lalu jatuh ke outline aturan | tidak dijalankan | Selalu menalar sebelum menjawab, dan dengan konteks 16k tidak lagi muat di GPU 6 GB. Tidak cocok untuk dokumen. |
| `qwen3:8b` | 87 detik | 181 detik | 389 detik | Diukur di CPU saat GPU tidak aktif, jadi waktunya tidak sebanding. |

Skrip memeriksa setiap jawaban model sebelum menggambarnya. Jika jawabannya bukan outline yang layak, skrip mencoba sekali lagi, lalu menyusun outline bertahap: nama cabang dulu, kemudian dua sampai empat butir untuk tiap cabang.
```

- **A**: Dokumen Membuat mind map. Chunk ini menjelaskan pemilihan model lokal untuk membuat mind map, termasuk performa model berdasarkan pengukuran tertentu.
- **B**: Ini adalah bagian dari dokumentasi tentang cara membuat mind map menggunakan skill mind_map. Bagian ini menjelaskan perbandingan performa beberapa model lokal seperti gemma3:4b dan qwen3:4b dalam menghasilkan peta dari topik atau dokumen.
- **C**: Chunk ini berada di bagian 'Memilih model lokal' dari dokumen 'Membuat mind map'. Isi tabel dan penjelasan mengenai kecepatan dan kinerja model lokal untuk membuat mind map.

## 99d6393011a5#7  (Membuat mind map)
Section: Membuat mind map > Memilih format keluaran

```text
Ekstensi pada `-o` menentukan formatnya, dan `--also` menambah format lain:

| Format | Dipakai untuk | Kebutuhan |
|---|---|---|
| `.html` | Dibuka di browser, digeser, dan diperbesar. | Python saja |
| `.svg` | Ditempel sebagai gambar di dokumen atau slide. | Python saja |
| `.mmd` | Ditempel di dalam blok kode `mermaid`, misalnya di README GitHub. | Python saja |
| `.png`, `.pdf` | Dikirim sebagai gambar atau dicetak. | Edge, Chrome, atau Chromium |
```

- **A**: Chunk ini berada di bagian 'Memilih format keluaran' dari dokumen 'Membuat mind map'. Chunk menjelaskan ekstensi file dan kebutuhan untuk setiap format keluaran yang didukung.
- **B**: Ini adalah bagian dari dokumentasi tentang cara membuat mind map menggunakan skill mind_map. Bagian ini menjelaskan berbagai format keluaran yang dapat dipilih saat menghasilkan mind map, seperti HTML, SVG, dan PNG.
- **C**: Dokumen Membuat mind map menjelaskan format keluaran yang didukung, seperti HTML, SVG, MMD, PNG, dan PDF, beserta kebutuhan dan penggunaannya.

## gqCEJ1McXCQ#1  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Masih kerokan masih. Jadi saya tuh masih kerokan ee ini masih kerokan karena bermanfaat untuk relaksasi otot terutama di bagian leher sama bahu. Karena kerjaan saya itu kan ngadap laptop sama handphone sama ngetik. Jadi biasa tension di otot-otot leher. Untuk cara merelaksasinya biasa saya beli alat rokokan yang kayak gini itu belakangnya kita pakai buat ini lumayan enak gitu. Tapi kalau misal kerokaya terlalu berlebihan akan menyebabkan iritasi pada kulit. Oh bukan mati Pak. itu yang bilang kerokan jangan tidur entar mati lu. Ayo ada banyak enggak? Banyak nih sekali tanya susah nih ya. Kerokan kerokan pada waktu tidur tuh sebenarnya enggak masalah. Kenapa kok bisa mati? Mungkin kerokannya tuh terlalu kencang sehingga memicu aktivasi di sini tuh.
```

- **A**: Chunk ini berisi penjelasan tentang manfaat dan risiko kerokan untuk relaksasi otot leher dan bahu, serta penjelasan mengapa kerokan terlalu kencang bisa menyebabkan mati.
- **B**: Ini adalah bagian dari video Tirta PengPengPeng yang menjelaskan tentang penggunaan kerokan untuk relaksasi otot. Bagian ini membahas potensi risiko jika kerokan dilakukan terlalu keras dan dampaknya pada pembuluh darah.
- **C**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan manfaat dan risiko kerokan untuk relaksasi otot, serta peringatan tentang penggunaan yang berlebihan.

## gqCEJ1McXCQ#4  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Pertanyaan pertama. Kedua dong. Yang kedua. Aduh yang mana tadi ya? Aduh aduh enaknya. Aduh aduh aduh. Pak demam tinggi bisa merusak sel otak secara permanen. Oh jawabannya jawabannya ini fakta sebenarnya. ee tubuh kita tuh sensitif dengan suhu. Terlalu dingin bermasalah, terlalu tinggi bermasalah. Suhu normal kita tuh sebenarnya di antara 36,5 sampai 37,5 ya. Dan ketika demam tinggi mencapai lebih dari 40 derajat itu bisa terjadi kerusakan pada selak. Itu benar. Dan ciri khasnya adalah akan terjadi kejang. Nah, ketika terjadi kejang sebagai manifestasi suhu tubuh terlalu tinggi itu otomatis sel-sel di otak tidak akan mendapatkan suplai oksigen tepat waktu dan akhirnya menyebabkan kerusakan.
```

- **A**: Chunk ini berisi penjelasan tentang dampak demam tinggi di atas 40 derajat pada otak, termasuk kerusakan sel otak dan kejang yang terjadi. Chunk ini terletak di bagian video yang menjawab pertanyaan netizen tentang fakta kesehatan.
- **B**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan fakta bahwa demam tinggi dapat merusak sel otak dan menyebabkan kejang jika suhu tubuh melebihi 40 derajat.
- **C**: Ini adalah bagian dari video Tirta PengPengPeng yang membahas fakta kesehatan. Bagian ini menjelaskan dampak demam tinggi terhadap otak dan pentingnya menjaga suhu tubuh normal.

## gqCEJ1McXCQ#7  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
simpatisnya naik karena fight and fly parasimpatisnya ngimbangin otomatis enzim pencernaan jadi keluar jadinya crossing. Nah, ini dua hal yang mengakibatkan kenapa kok bagi olahraga itu disuruh ngising dulu kosongkan isi perut supaya ketika pas olahraga apalagi interval bisa jadi ngising di tengah-tengah sesi. Itu sering terjadi. Lagi nge-gym tiba-tiba belat ngising ya. Lagi lari tiba-tiba belet ngising dan enggak enak loh lari sambil nahanek itu karena apa? Sakit perutnya. Dan bisa jadi nanti taimu kecer-kecer. Iya. Laki-lari prel prel kopetan kopetan kopet. Next. Kenapa sekarang makin banyak anak muda yang terkena hipertensi dan apa langkah penanganan paling efektif selain bergantung pada obat-obatan?
```

- **A**: Chunk ini menjelaskan mekanisme tubuh saat olahraga yang menyebabkan rasa ingin BAB dan mengapa anak muda rentan hipertensi karena gaya hidup dan genetik.
- **B**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan alasan mengapa olahraga membuat ingin BAB dan penyebab meningkatnya hipertensi pada anak muda.
- **C**: Ini adalah bagian dari video Tirta PengPengPeng yang membahas tentang alasan seseorang ingin buang air besar saat berolahraga. Bagian ini menjelaskan mekanisme fisiologis tubuh dan dampaknya terhadap sistem pencernaan.

## gqCEJ1McXCQ#10  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Jadi ubah gaya hidup, rajin olahraga, tidur teratur dan kurangi stres kerja. H lah saya sif malam resiko. Makanya kalau dilihat di sini yang tensinya tinggi Danil, saya Dori, Andika ini tensinya tinggi malah Adit yang tensinya rendah. Kerjanya kan fisik. Oh cleaning service. Hakim juga tensinya rendah. Motoran. Motoran. Yes. Terus dulu. Iya. Yang tensinya tinggi bapakmu komen punya anak kayak kamu kan anak satu hobinya kayak gini. Next nih Pak tadi masih berhubungan sama rokok dan kopi. Kenapa orang yang merupakan manan rokok itu ngopinya lebih kencang? Oh saya contohnya. Jadi kenapa orang mantan perokok kopinya lebih kencang? Salah satu impact dari nikotin dia adalah membuat ketergantungan dan efek sampingnya adalah dia membuat aktivitas secara simpatis naik dan membuat jantung itu jadi terdependable sama nikotin. Oke.
```

- **A**: Chunk ini berisi penjelasan tentang faktor gaya hidup yang memengaruhi tekanan darah, seperti konsumsi rokok dan kopi, serta contoh kasus dari penggunaan tekanan darah pada anak muda. Dari video Tirta PengPengPeng tentang mitos dan fakta kesehatan.
- **B**: Ini adalah bagian dari penjelasan Tirta PengPengPeng tentang faktor-faktor yang menyebabkan tekanan darah tinggi, termasuk pentingnya gaya hidup sehat dan pengaruh rokok serta kopi terhadap kesehatan jantung.
- **C**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan hubungan antara gaya hidup, stres kerja, dan tekanan darah, serta efek nikotin pada kebiasaan minum kopi.

## gqCEJ1McXCQ#13  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Akibatnya kalau sarafnya terganggu karena kurang energi terjadinya diabetes neuropati. Orangnya gampang kesemutan, gampang baal di daerah kaki. Kalau terganggu di retina jadinya diabetes retinopati. Terganggunya penglihatan dikarenakan kadar gula terlalu tinggi sehingga si mata atau retina tidak mendapatkan energi. Diabetes retinopati. Kalau terjadinya di pembusukan, nah itu jadi nekrosis. Jadi ada luka terbuka gara-gara gula darahnya terlalu tinggi, proses penyembuhannya jadi terhambat, lukanya jadi basah, basah-basah benyanya, timbul bakteri mikroorganism, jadinya membusuk dan harus diamputasi. Jadi betul, diabetes tidak terkontrol itu bisa menyebar dan merusak semua organ tubuh yang akhirnya merusak pada ginjal. Karena akhirnya ginjal gagal menjalankan fungsinya untuk menyaring gula dan akhirnya membuat sel-sel nefron pada ginjal jadi rusak. Ah, itu benar.
```

- **A**: Ini adalah bagian dari penjelasan Tirta PengPengPeng tentang dampak diabetes yang tidak terkontrol. Bagian ini menjelaskan bagaimana diabetes dapat merusak saraf dan mata, serta menyebabkan komplikasi serius seperti amputasi.
- **B**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan dampak diabetes tidak terkontrol pada organ tubuh, seperti neuropati, retinopati, dan kerusakan ginjal.
- **C**: Chunk ini menjelaskan dampak diabetes tidak terkontrol pada organ tubuh, khususnya neuropati, retinopati, nekrosis, dan kerusakan ginjal akibat gula darah tinggi.

## gqCEJ1McXCQ#16  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Nah, ini pertanyaannya keren-keren nih. Saya minta Chiki eh keripik tempe. Chiki aja. Chiki chiki chiki chiki ciki ciki ciki cik. Bukan endorse. Saya memang suka makan ini. Ini makan angin. Jangan ditiru sering-sering. Bukti bahwa saya manusia biasa. Yes. Nah, bukan tawon tapi olahraga. Anjir. Bukan tawon. Mulai. Oke. Pertanyaannya adalah anak yang terlalu pro. Jadi gini. Hm. Ee si ini suara sendalnya kedengaran ini pasti istriku lewat suara sendal itu lewat. Nah. Nah. Ah gitu. Jadi pada dasarnya yang kalian harus tahu ee anak itu kan ketika lahir dia tidak mendapatkan imunitas dari ibunya. IGG ya. Aku lupa IG apa ya imunoglobulin G apa IGM ya? Ig yang dari ibunya dan dengan kolostrum ASI pertama dari ibu itu akan memberikan antibodi tambahan supaya si anak ini akan tahan dengan memiliki pertahanan yang mirip dengan ibunya. Nah, tetapi anak ini kan butuh paparan dengan mikroorganism yang ada.
```

- **A**: Dalam video Tirta PengPengPeng, chunk ini membahas pentingnya paparan mikroorganisme untuk meningkatkan imunitas anak dan membahas mitos tentang imunisasi serta peran ASI dalam pemberian antibodi.
- **B**: Ini adalah bagian dari video Tirta PengPengPeng yang membahas tentang sistem imun anak dan pentingnya paparan terhadap mikroorganisme alami. Bagian ini menjelaskan bagaimana imunitas anak terbentuk melalui interaksi dengan lingkungan.
- **C**: Chunk ini berisi penjelasan tentang imunitas anak yang diperoleh dari ibu melalui kolostrum ASI dan pentingnya paparan mikroorganisme untuk pembentukan imunitas alami. Dokumen ini berasal dari video YouTube Tirta PengPengPeng yang membahas mitos dan fakta kesehatan.

## gqCEJ1McXCQ#19  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Tapi harus bersih. Nah, nomor dua contoh paling simpel anak intervese indoor. Ini kejadian banget di anakku. Anakku setiap pulang sekolah itu selalu flu. Lucunya setiap masuk rumah main di luar dia enggak flu. Setiap pulang sekolah itu flu. Tahu enggak? Kena setiap pulang jadi 2 bulan sekali pasti flu. Apa yang menyebabkan anakmu flu menurutmu? Kenapa tiap dia pulang dari sekolah rentan flu diobati di rumah 4 hari sembuh lagi? Karena Iya, betul sekali. Pintar. Jadi yang membuat anak kecil rentan sakit itu rata-rata adalah AC yang enggak bersih. AC itu memutarkan sirkulasi udara terus-menerus tidak dibersihkan. Akhirnya mikroorganism memutar di situ. Cendela enggak pernah dibuka, udara enggak pernah terganti. Yang akhirnya bakteri dan virus tersebut menjadi mutasi dan akhirnya menginfeksi superflu dan akhirnya gantian per anak kena terus.
```

- **A**: Chunk ini berisi penjelasan tentang penyebab anak kecil rentan flu akibat AC tidak bersih, dengan contoh anak yang sering sakit setelah pulang sekolah. Dokumen ini berasal dari video edukasi kesehatan oleh Tirta PengPengPeng.
- **B**: Dalam video ini, Tirta PengPengPeng menjelaskan mengenai pentingnya paparan lingkungan alami untuk meningkatkan kekebalan tubuh anak-anak dan membahas risiko penyakit akibat AC yang tidak terawat.
- **C**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan hubungan antara AC kotor dan penyebab flu pada anak, serta pentingnya menjaga kebersihan udara dan sirkulasi untuk mencegah penyebaran mikroorganisme.

## gqCEJ1McXCQ#22  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Pak Deni itu makan daging sapi atau daging seafood, udang, belut yang proteinnya tinggi, baru makan dikit aja 100 gram besoknya sakit. Gotraatritis. Berarti yang jelek dari Pak Deni adalah sistem pada ginjal dan hati. Tak suruh saya enggak mau. Jadi di masa depan kemungkinan Pak Deni memiliki masalah pada ginjal dan hati. Kemungkinan batu ginjal sama gagal hati. Cara ngecek pasien tuh sesimpel itu. Kalau dia enggak bandel, dia tinggal check up, cek fungsi ginjal, cek fungsi hati, cek total darah. Logikanya kalau asam uratnya di atas 8 atau 10, berarti kemungkinan akan ada batu ginjal dari urat, asam urat, kristal asam urat dan akan mengganggu fungsi hep. Jadi harusnya SGPT-nya, SGPT-nya akan naik dan kemungkinan kalau ini naik semua, kalau fungsi hati naik, logikanya trigliceridnya akan naik, kolesterol akan naik. Sudah kemungkinan kalau ini naik berarti tensinya harusnya 180.
```

- **A**: Ini adalah bagian dari video Tirta PengPengPeng yang menjelaskan tentang asam urat dan hubungannya dengan kesehatan ginjal serta hati. Bagian ini membahas bagaimana konsumsi protein berlebihan dapat memicu masalah pada organ tersebut.
- **B**: Chunk ini berisi penjelasan tentang kasus Pak Deni yang mengalami masalah ginjal dan hati akibat asam urat tinggi, serta cara pemeriksaan fungsi organ tersebut.
- **C**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan hubungan antara konsumsi protein berlebihan, asam urat, dan risiko gangguan ginjal serta hati pada Pak Deni.

## gqCEJ1McXCQ#25  (#suaratirta BONGKAR MITOS & FAKTA KESEHATAN DARI PERTANYAAN NETIZEN)
Section: Transcript

```text
Jadi buat untuk orang tua yang usianya mendekati lansia dan kalian mau suplementasi perlu tidaknya kalian suplementasi itu harus check up dan check up itu dilakukan harusnya sejak umur 25. Setelah umur 35 harus rutin setahun sekali. Kalau 25 sampai 30 mungkin 2 tahun sekali. 30 35 setahun sekali. 35 sampai 40 setahun bisa dua kali. 40 sampai 55 teruskan setahun dua kali. Setahun dua kali. sehingga kita tahu sampai mana organ kita tuh nasibnya gimana. Apakah jelas itu? Nah, contoh saya, contoh saya sendiri saya sendiri ini ternyata recovery-nya jelek, kualitas tidurnya buruk ya. Padahal saya sudah ngerasa pola tidurnya teratur. Ternyata dikarenakan aktivitas fisik ditambah dengan kerjaan yang stresnya level tinggi sehingga membuat saya tuh fatik.
```

- **A**: Dalam video Tirta PengPengPeng, chunk ini menjelaskan pentingnya pemeriksaan kesehatan rutin untuk menentukan kebutuhan suplemen, disertai contoh pribadi Tirta tentang kualitas tidur dan kelelahan.
- **B**: Ini adalah bagian dari penjelasan Tirta PengPengPeng mengenai pentingnya pemeriksaan kesehatan secara berkala untuk menentukan kebutuhan suplementasi, terutama bagi orang dewasa yang mendekati usia lansia. Bagian ini membahas jadwal rutin check-up berdasarkan usia.
- **C**: Dokter Tirta menjelaskan pentingnya check up sejak usia 25 untuk orang tua mendekati lansia yang ingin suplementasi. Chunk ini membahas jadwal rutin pemeriksaan organ dan penyebab kualitas tidur buruk akibat aktivitas fisik dan stres.

## Qft-J2LG0NM#1  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:00:00 Intro dan Teaser

```text
Hai Kejo. Welcome to unscripted. Halo. Akhirnya akhirnya diundang. Jangan gitu dong. Udah pasti undang keju. Tinggal tunggu waktu aja. Iya. Thank you, thank you, thank you. Oke, em gua penasaran deh. Langsung aja ya kita gas ke pertanyaan pertama karena kan mungkin teman-teman di sini tahu Kejo itu sebagai trader kripto. Cuman mungkin banyak yang kita, gua sendiri pribadi juga jarang bahas kayak gimana sih tiba-tiba kok bisa nyampai sini dan nyampai sesuai sini. Nah, ceritanya Kejo itu sebenarnya kayak gimana sih dulunya sebelum trading? Sebelum trading? Waduh, aku ingat lagi waktu sebelum ee waktu awal-awal terutama tahun eh tahun lalu ya, kita tuh pernah ketemu di Alpha Traders. Heeh. Dan itu aku nobody lah as just a traders
```

- **A**: ini berada di bagian intro dari video YouTube 'Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya' yang dibawakan oleh KJo. Chunk ini menjelaskan awal mula Kejo sebelum beralih ke trading.
- **B**: Ini adalah bagian pengantar dari video YouTube oleh Theresa Learns yang mewawancarai Kejo, seorang trader kripto yang menceritakan awal mula perjalanannya sebelum menjadi trader, dimulai dengan latar belakangnya sebagai programmer.
- **C**: Chunk ini merupakan bagian awal pembukaan wawancara dalam video YouTube Theresa Learns dengan KJo, di mana KJo menyampaikan latar belakangnya sebelum menjadi trader crypto.

## Qft-J2LG0NM#4  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:01:30 Awal Mula Masuk Crypto

```text
Heeh. Ternyata pas 2021 tiba-tiba ramai lagi lihat portofolio lumayan lah dari belasan juta 20-an juta jadi ratusan juta waktu gitu sama Bitcoin sih sama beberapa ada sempat aku masukin ke crypto-crypto koin kecil gitu. Oke kayaknya waktu itu BCH deh waktu itu aku masukin juga. Oke. Jadi itu yang benar-benar ee sebenarnya lebih kayak tiba-tiba jadi investor ya. Iya. Tiba-tiba jadi investor. Nah, cuman kalau dibilang traders mungkin sebenarnya bukan pas 2021. 2021 tuh riding the wave aja lah ya karena waktu itu kan hampir masuk ke mana aja naik gitu tapi justru jadi traders itu pas ee pas teraluna iya ya crash baris kayak mau masuk ini ini ini ini enggak bakal bisa terbang akhirnya mulai belajar di features gimana supaya bisa trading tapi ee di event di market be itu bisa cuan yaitu dengan short gitu jadi waktu itu aku mulai merapikan ee ee gameplay.
```

- **A**: Dalam video ini, KJo menjelaskan bagaimana ia beralih dari investor awal Bitcoin pada tahun 2017 hingga menjadi seorang trader yang lebih disiplin pada tahun 2024.
- **B**: KJo menceritakan perjalanan menjadi investor crypto sejak 2017, termasuk pengalaman masuk ke Bitcoin dan beberapa koin kecil, serta transisi menjadi trader setelah pasar crash 2021.
- **C**: KJo menjelaskan bagaimana ia tiba-tiba menjadi investor di 2021 dengan portofolio ratusan juta rupiah, lalu beralih ke trading dengan strategi short saat pasar crash.

## Qft-J2LG0NM#7  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:05:30 Dari Investor Jadi Trader

```text
Iya kurang lebih gitu. Emm aku lihat kontennya Kejo yang kemarin nih sebelum yang pas benar-benar Bitcoin itu naik lagi. Heeh. Emm ini tanggal berapa nih kita sekarang? 9. Tanggal 9 ya. Em kita kan baru mungkin du 2 3 minggu lagi 2 3 minggu lalu yang pas Coin Fest itu tiba-tiba naik gitu kan. Dan K Jo sendiri punya conviction kalau Bitcoin itu tuh ada bottomnya itu udah di R0.000-an udah enggak nyari R30.000, R.000, Rp50.000 itu enggak. Nah, itu tuh kayak insight-inside seperti itu. Conviction-nya tuh dapat dari mana sih? Mungkin lebih tepatnya gini, teman-temanku padahal banyak yang ngomong, "Wah, ini makro, news, dan lain-lain jelek kan." Sebenarnya bagi aku tuh aku dulu setuju banget fundamental itu penting. Sebenarnya sampai sekarang juga penting gitu loh.
```

- **A**: KJo membahas keyakinannya terhadap bottom Bitcoin dan cara ia mengabaikan noise berita untuk fokus pada analisis teknikal dalam trading.
- **B**: Dalam video ini, Theresa Learns mewawancarai KJo mengenai transisinya dari investor menjadi trader crypto. Bagian ini menjelaskan bagaimana KJo mengembangkan 'conviction' Bitcoin dengan fokus pada *price action* dan mengabaikan berita atau ‘noise’.
- **C**: Chunk ini berasal dari bagian 'Dari Investor Jadi Trader' di video KJo. Isi chunk membahas conviction KJo tentang bottom Bitcoin dan mengapa ia menganggap berita sebagai noise.

## Qft-J2LG0NM#10  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:08:30 Conviction Bitcoin

```text
tarik dari low to high itu berada di R9.000. Ada juga kalau enggak salah support dari trendline itu juga ada. Terus BTC ETF itu around 57.000 juga. He turunnya sori 57.000 R kan dia sempat break out dari all time high-nya 2021 dar ke 69.000 kalau enggak salah. Habis itu retrah. Retrest-nya itu di 57.000. Jadi aku lihat kurang lebih ada 4 atau 5 parameter conviction aku ini arahnya sudah di area bottom. Iya. Mungkin orang bilang, "Oh, mungkin bakal ke 50.000 atau ke 40.000 atau Rp50.000 lah atau R5.000." Oke. Kemarin sempat R57.000. 57.000 ke 55 seberapa jauh sih persentasenya? 57 ke 50.000 berapa jauh sih? Okelah mungkin 10% ya. Lebih better kan daripada kamu cicil Bitcoin di 100.000 H atau di Rp1.000 gitu, Kang. Kalau R10.000 atau R.000 R itu kan udah anggaplah sekarang udah jauhnya 50% nih.
```

- **A**: Dalam video ini, KJo menjelaskan bagaimana ia menggunakan analisis teknikal dan parameter untuk menentukan saat yang tepat untuk membeli Bitcoin, khususnya dengan fokus pada 'conviction Bitcoin' dan mengabaikan berita.
- **B**: KJo menjelaskan analisis teknikal Bitcoin dengan fokus pada parameter conviction yang menunjukkan posisi di area bottom, serta perbandingan risiko-reward untuk pengambilan opportunity di harga 57.000.
- **C**: KJo membahas analisis teknikal Bitcoin, menyoroti parameter conviction dan area bottom berdasarkan price action serta support resistance.

## Qft-J2LG0NM#13  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:08:30 Conviction Bitcoin

```text
Pas BTC turun ke 74.000 sampai 76.000 last year karena masalah tarif. Heeh. Ya, itu kan pertama karena si Trump bilang tarif gitu kan. Semua negara kena hampir semua ee semua negara kena and then turunlah sampai dari 109.000 turun ke 74.000. Tiba-tiba ee di situ sebenarnya yang ku tarik itu adalah fibo 0,618. Itu Fibonacci 0,618. Makanya itulah kejo start dari situ cuannya banyak. Nah, di saat itu yang aku tahun lalu tuh aku cuman profit lebih dari e kurang lebih 30% dari portofolio aku. Aku udah bersyukur banget karena itu very very bad news ya semuanya ya kayak tarif lu nih tarifnya seberapa panjang nih dan ini impact-nya ke global semua artinya masalah logistik masalah apapun itu bakal kena semua. Heeh.

Nah, yang aku pikirkan waktu itu intinya fokusnya ya sudahudah by technical nanti kita trading atau kita paku pakai SL plus. Tapi tiba-tiba dia kan bilang, "Oke, tarif ee dipause gitu kan naiklah kurang lebih sampai ke Rp80.000-an gitu." Tapi kalau kamu tahu di tahun
```

- **A**: KJo membahas penurunan harga Bitcoin akibat masalah tarif dan strategi trading berdasarkan Fibonacci, serta keuntungan yang diperoleh dari situasi tersebut.
- **B**: Ini adalah bagian dari wawancara dengan KJo tentang strategi trading kripto, khususnya analisis teknikal dan cara mengelola risiko. Bagian ini menjelaskan bagaimana Kejo bereaksi terhadap berita tarif yang memengaruhi harga Bitcoin.
- **C**: KJo menjelaskan bagaimana ia memanfaatkan teknikal saat Bitcoin turun ke 74.000 akibat masalah tarif, dengan profit 30% dari portofolio meski ada berita buruk global.

## Qft-J2LG0NM#16  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:12:30 Berita Itu Cuma Noise

```text
Oke. Kalau by technical sebenarnya mungkin kita belum ada higher low. Heeh. Tapi kan orang-orang bilang kan bulan depan the bottom Oktober katanya kan. Oke. Tapi sebenarnya aku enggak pernah mau bilang atau berapa hari bottom dan lain-lain. Kan kalau kita ngomongin beberapa hari bottom pun mereka lihatnya by year atau by month. Dan month itu kan effectnya kan ya mungkin di area sekarang pun bisa ternyata bottom-nya karena pakai time frame lebih besar sehingga ee apa candle-candle-nya jadi kecil gitu kan. I. Nah, tapi pada dasarnya kalau aku pribadi lebih ee baik lagi di teknikal memang pada dasarnya ketika kita coinvest kemarin kan naik dari 62.000 naik sampai tiba-tiba ke Rp80.000 79.000 gitu itu naik 24% loh satu candle a week.
```

- **A**: Dalam video ini, KJo menjelaskan pendekatannya dalam menganalisis pasar crypto dengan fokus pada indikator teknikal dan mengabaikan berita yang dianggap ‘noise’. Bagian ini membahas tentang pergerakan harga Bitcoin dari level tertentu hingga mencapai titik tertinggi.
- **B**: KJo menjelaskan bahwa teknikal lebih penting daripada prediksi waktu bottom, dengan contoh kenaikan BTC dari 62.000 ke 79.000 dalam satu minggu.
- **C**: KJo membahas analisis teknikal dan cara mengabaikan berita sebagai noise, menjelaskan pergerakan harga Bitcoin dan strategi trading berdasarkan pola teknikal.

## Qft-J2LG0NM#19  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:17:30 Ambil Opportunity di Depan Mata

```text
Rp50.000 justru kalau kalian expecting bottom-nya itu di Q4 itu hancur. Bisa aja ternyata bottom-nya di tahun depan, bisa aja malah 2 tahun lagi karena trennya udah patah. Nah, justru kalau kalian bilang atau teman-teman yang banyak yang bilang eh kita Q4 should be the bottom, please respect. Jangan jebol patah trend karena patah ya kita tahulah patah trend berarti shiftingnya ke be gitu kan. I nah jadi beya jadi malah ada istilah extend be market katanya kan. Betul gitu. Jadi kalau aku pribadi emm apakah bakal ada eh bottom lagi? Pada dasarnya aku kan trading ya. Jadi kalau aku kan tadi sempat bilang kita di sebelum record aku sebenarnya expecting one more swing high di mana pun itu mungkin di BTC di 82 atau 84 gitu kan karena BTC tetap harus breakout 82 84 untuk bisa keluar dari zona be ini ya. Nah, jadi dan itu aku harus lihat juga pokoknya swing high sekali lagi aku lihat kalau dia masih enggak mampu break out 84 als yang aku open seminggu 2 minggu terakhir ini aku bakal TP.
```

- **A**: KJo menjelaskan strategi tradingnya saat market berada di zona bearish dengan fokus pada swing high dan breakout 82-84 untuk menghindari patah trend.
- **B**: KJo membahas strategi trading dan harapan bottom pasar, menekankan pentingnya mengambil peluang saat ini dan memantau swing high di BTC untuk keluar dari zona bear market.
- **C**: Dalam video ini, KJo membahas analisis pasar kripto dan strategi trading-nya. Bagian ini menjelaskan pandangannya tentang ekspektasi bottom pasar dan pentingnya mengikuti tren serta *breakout* harga.

## Qft-J2LG0NM#22  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:17:30 Ambil Opportunity di Depan Mata

```text
Oke, ya. Jadi, kalau orang bilang enggak ada rugi, itu salah satu rugi yang cukup besar. Cuman ya kalau di portofolio kan di grup ya aku kan punya satu akun ee khusus 1$ 1.000 gitu kan. Itu kemarin sempat sebelum-sebelumnya aku 1.000 jadi 10.000 1000.000 jadi 10.000. Aku kayaknya ada en lima lima kali aku share portofolio di grup dan mana anak pada ikut itu 1.000 jadi 10.000. He. Tapi jujur pas di Julai itu lebih berat banget. Julai Juni. Juni di Juni gitu itu portfolio 1000 jadi 200 300 tapi sekarang sudah jadi 6.000 7.000. Iya. Jadi aku memang waktu itu terlalu greedy karena in that time market tuh terlihat sangat oke bagi aku. So ris-nya aku lebih gedein. Ternyata tidak sesuai. Cut loss entry eh ambil position lagi. Habis itu sekarangah jadi 6000 7.000. Jadi sebenarnya balik lagi ke risk managementen sih, cuma waktu itu ya kalau ngomongin the biggest loss yang pernah aku lewatin tuh itu juga sempat aku masukin ke eh podcast eh overpost itu ya itu 500.000-an.

Oke. Dan ada enggak sih maksudnya kayak
```

- **A**: KJo membahas pengalaman cut loss Rp500 juta dan pembelajaran dari kegagalan manajemen risiko saat portofolio turun drastis dari Rp1.000 ke Rp200-300 dalam waktu singkat.
- **B**: Dalam video ini, KJo membahas pengalaman cut loss-nya yang signifikan, khususnya ketika portofolio grupnya mengalami penurunan. Bagian ini menjelaskan bagaimana ia belajar tentang manajemen risiko dan pentingnya persentase dalam trading.
- **C**: KJo membahas pengalaman cut loss Rp500 juta sebagai pembelajaran kedewasaan trader dan pentingnya risk management dalam trading crypto.

## Qft-J2LG0NM#25  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:22:00 Cut Loss Rp500 Juta

```text
Udah bersyukur, bro. Lu di bisnis mana sih yang gampang? Pertama bisnis ya. Trading pun juga enggak bisa begitu karena tidak setiap hari marketnya itu punya volume." H. He. Nah, tapi dalam 1 bulan lu pasti akan punya big event atau volume yang oke. Sama kayak ketika lu berbisnis, lu bikin ee di hotel nih, misalnya hotel di puncak. Emang Senin sampai Kamis rame enggak? Yang bikin nutupin itu adalah Kamis eh Jumat, Sabtu, Minggu itu dinutupin operasionalnya. Nah, terus yang aku pelajari tentang everyday itu ada operational cost yang harus kita keluarkan. itu adalah jata cut loss. Nah, makanya everyday gua bakal cari opportunity opportunity kayak gitu. Itu sebenarnya yang gua belajarin tentang cutl sih sebenarnya.
```

- **A**: KJo membahas pentingnya cut loss dalam trading, membandingkannya dengan bisnis hotel dan menjelaskan bahwa trading tidak selalu profitable setiap hari, tetapi perlu mencari peluang besar dalam jangka waktu tertentu.
- **B**: Dalam video ini, KJo menjelaskan pentingnya *cut loss* dalam trading kripto, menekankan bahwa profit tidak terjadi setiap hari dan biaya operasional harus dipertimbangkan seperti bisnis lainnya.
- **C**: Chunk ini berisi penjelasan KJo tentang pentingnya cut loss dalam trading dengan analogi bisnis hotel. Ia menjelaskan bahwa setiap hari tidak bisa profit pasti ada kebutuhan cut loss untuk menghindari kerugian besar.

## Qft-J2LG0NM#28  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:25:30 Kedewasaan Trader

```text
Jadi mulai jadi ee joki di kampus terus juga ngajar di kampus terus juga private les and then ngajar di komunitas gitu kan. Itu semua untuk dapetin income. Bahkan aku sampai magang di startup. He. Nah, tapi seing waktu ee termasuk pas COVID itu malah susah kan cari kerja, susah kerjaan. Ee orang-orang juga kayak ya banyak banget ee saingan gitu loh. Dan akhirnya waktu itu ramai tuh di trading kan. Nah, bas trading itu aku anggap sebagai peluang aja. Nah, bahkan enggak bukan karena di kripto aja ya. Sebenarnya aku waktu itu juga fokusnya ke AI juga. Maksudnya developing AI dan ngajar AI. Jadi pembicara di AI itu juga dapat income, dapat endorse misalnya gitu-gitu ya. Dulu kan juga aku masih terima endorse.
```

- **A**: Dalam video ini, KJo menjelaskan bagaimana ia beralih dari investor menjadi trader, termasuk pengalaman kerjanya sebagai joki di kampus dan mengajar untuk mendapatkan penghasilan tambahan.
- **B**: KJo menceritakan perjalanan mencari penghasilan sebelum terjun ke trading, termasuk mengajar dan magang di startup, serta menganggap trading sebagai peluang usai kesulitan mencari kerja saat pandemi.
- **C**: KJo menjelaskan bagaimana ia memulai karier dengan mengajar di kampus dan komunitas untuk mendapatkan pendapatan, bahkan magang di startup, sebelum beralih ke trading saat pasar ramai dan kesempatan di AI.

## Qft-J2LG0NM#31  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:29:00 Jangan Cinta Koin, Cinta Cuannya

```text
angka itu. Tapi memang mungkin aku sudah mati rasa ya dari sisi lihat sebuah angka itu sih. Karena selama itu enggak jadi di real life aku anggap uang itu tuh bukan uang. Jadi itu kayak skor games yang aku butuhkan. sekarang aku butuh skor yang lebih besar kayak gitu loh. Oke. Nah, gitu. Tapi di L so far untungnya semua itu terjaga dengan teknikal. Jadi tchnikal itu ee ego aku tuh masih bisa nurutin teknikal. H oh enough misalnya lihat by technical udah patah enough udah berarti ini udah kita harus tahu rezekiku cuman rezekiku cuman ini. Nah sama yang ngejagain aku selama itu ini itu adalah SL plus. So kalau ketika tiba-tiba dia terbang tapi kebanting jar kan otomatik lagi ke TP. Ya udah bersyukurnya situ gitu. Jadi aku selalu again aku enggak bisa sama e bisa ngajarin anak-anak kayak wah ini gimana supaya lihat angka tuh tidak tidak menjadi duit gitu. Tapi intinya ya udah intinya setiap orang punya rasa bersyukur yang beda-beda ya.
```

- **A**: Chunk ini berasal dari bagian 'Jangan Cinta Koin, Cinta Cuannya' di video KJo. Chunk ini menjelaskan bagaimana KJo memandang profit sebagai skor game dan pentingnya teknikal dalam mengelola risiko trading.
- **B**: KJo membahas cara memandang keuntungan dalam trading, menekankan bahwa uang bukan sekadar angka tapi skor yang perlu diukur. Ia menjelaskan pentingnya disiplin teknikal dan SL untuk mengelola risiko.
- **C**: Dalam video ini, KJo menjelaskan pentingnya tidak ‘mencintai’ mata uang kripto, melainkan fokus pada keuntungan yang dihasilkan melalui trading.

## Qft-J2LG0NM#34  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:29:00 Jangan Cinta Koin, Cinta Cuannya

```text
gameplay yang cocok untuk diri pribadi. Karena baik lagi ya itu lu harus punya gameplay. Kalau enggak punya gameplay lu harus punya sistem kerja. Sama kayak kita buat bisnis lu harus punya SOP, lu harus punya sistem kerja. Kalau enggak kualitasnya bakal tidak sesuai, tidak menghasilkan output yang cukup bagik gitu loh. Kayak gitu. Oke, gua pengin e bahas dikit dari sisi kayak tadi lu sempat bilang kalau pernah jadi pembicara AI. Nah, sekarang ini kan kita di era yang lumayan sangat AI native, AI forward, dan tadi e lu mention di tahun 2020-2021 aja udah ngomongin AI. Padahal kan itu sebelum jauh sebelumnya EV 2016 gua menang lomba AI dan gua ngajar BINUS juga AI. Kenapa kok bisa sih ngulik AI juga?
```

- **A**: (no context: names not in the document: AI-nya)
- **B**: Ini adalah bagian dari wawancara dengan KJo yang membahas tentang pentingnya memiliki strategi trading yang disesuaikan, mirip seperti membangun sistem kerja untuk bisnis, serta menekankan fokus pada keuntungan daripada aset kripto tertentu.
- **C**: KJo membahas pentingnya memiliki sistem kerja dan gameplay pribadi dalam trading, serta mengulas pengalamannya dengan AI sejak 2016.

## Qft-J2LG0NM#37  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:34:00 AI Native Developer ke Content Creator

```text
Iya, ujungnya duit. Nah, terus ya sama. Oh, gitu kan akhirnya kayak ee enggak sengaja jadi dosen tamu, terus jadi sering ngajar BINUS juga di AI. Terus akhirnya portofolio gua itu dilihat sama salah satu director atau salah satu perusahaan properti di Indonesia tiga besar. Kita build eh company juga lah waktu itu. Dan bahkan waktu itu masih 181. Hm. Dan itu kita bikin eh face recognition dan macam-macam di sana. dan itu training manual semua. He. Nah, pas COVID perusahaan itu enggak bisa jalan karena perusahaan itu bergerak di bidang ee intinya kita harus keluar aktivitas. Nah, kan pas COVID enggak bisa kan. Nah, akhirnya gua juga memutuskan untuk tidak di sana karena bisnisnya pending postpon. Nah, akhirnya gua jadilah content creator content creator AI waktu itu. Karena waktu itu juga ee chatbit GPT sudah mulai muncul. Nah, ya udah e jadi situ lumayan endors-nya juga income tambahan. And then gua build. Oh ya, gua juga dari dulu memang suka build e AI apps gitu kan. Dan aplikasi-aplikasi juga gua sering bikin.
```

- **A**: Chunk ini berasal dari bagian '00:34:00 AI Native Developer ke Content Creator' dalam video KJo. Isi chunk menjelaskan transisi KJo dari pembangun AI ke content creator, termasuk pengalaman di perusahaan properti dan penggunaan AI untuk analisis trading.
- **B**: KJo menceritakan perjalanan dari AI Native Developer ke content creator, termasuk pengalaman bekerja di perusahaan properti dan keputusan berhenti karena pandemi.
- **C**: Ini adalah bagian dari wawancara dengan KJo tentang bagaimana ia beralih menjadi content creator dan menggunakan AI setelah pengalaman membangun perusahaan dan proyek face recognition.

## Qft-J2LG0NM#40  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:34:00 AI Native Developer ke Content Creator

```text
Bahkan juga dengan modul misalnya gimana cara e risk managemennya kejo kayak gitu. Jadi semua update-an gua kayak istilahnya kan Bloomberg kan punya Bloomberg nih. Semua analis kirim kirim kirim kirim kirim gitu. Tapi kan enggak semua orang bisa ngolah datanya. Nah ini adalah analisnya ada kejo. Gua fitin ke kejo terminal. Oke kayak gitu. Nah nanti dia bakal collaboration dengan beberapa data yang ee apa namanya? news-nes itu dicolaborate kayak gitu sih. Oke, berarti untuk kayak member-member ini udah ada keju terminal ya yang mereka tuh bisa nanya secara real time juga based on data yang memang udah difit sama keju send keju sendiri gitu. Oke. Dan itu bisa 24 jam gitu. Oke. Menarik. Oke. Oke. Ini kayak lumayan menarik untuk implementasi AI dan trading ya. Karena kan mungkin sebelum itu nyari informasi segala macam itu kan agak susah dan agak scattered.
```

- **A**: Dalam wawancara dengan KJo, ia menjelaskan bagaimana AI digunakan untuk mengolah data dan memberikan analisis real-time dalam trading crypto, serta keunggulannya dibandingkan sumber informasi yang terdispersi.
- **B**: KJo menjelaskan bagaimana Kejo Terminal menggunakan AI untuk analisis real-time dan manajemen risiko, memproses data secara terstruktur untuk anggota Kejo Akademi.
- **C**: Dalam video ini, KJo menjelaskan Kejo Terminal, sebuah AI yang ia bangun untuk membantu analisis trading real-time, khususnya bagaimana ia mengolah data dan memberikan update kepada anggotanya.

## Qft-J2LG0NM#43  (Trader Sejati = Berani CUTLOSS, Cintain Cuannya Bukan Coin-nya #TheInn)
Section: Transcript > 00:40:00 AI Personal untuk Trading

```text
Ngapain lu pusing-pusing? Ya tentunya enggak 100% gua pegang sana semua pasti ada tangan kanan gua semua. Cuman gua enggak berharap dari bisnis itu gua income sangat-sangat luar biasa. dia positif aja gua sudah bersyukur. Tapi setidaknya yang paling penting adalah karyawan-karyawan atau orang-orang di dalam situ tuh bisa menafkahi orang-orang ee keluarganya mereka atau bisa untuk mereka hidup gitu. Udah enough udah itu gua udah bersyukur banget kok. Atau kalau bisa gua bisa membawa janjang karir mereka itu juga lebih dari cukup. Terus gua juga kepikiran dulu tuh gua ngerasa gua tuh pintar tapi gua enggak dapat kesempatan. Sehingga gua sekarang ketika gua punya resource, gua berpikir bahwa gua banyak nemu orang-orang pintar, tapi mereka enggak make it. Mereka cuman malah masih di bawah dan banyak problem dan maksudnya masih struggling lah. Gua berpikir bahwa kalau mereka pintar dan mereka jujur dan lain-lain untuk semua teman-teman gua dan itu udah gua lakuin dari kemarin-kemarin. gua kasih mereka resource like mungkin perusahaan maksudnya eh tempat gitu kan atau mungkin gua kasih modal karena ya karena again mereka punya value-nya. Tapi makanya gua mikir dari dulu tuh kayaknya banyak orang pintar tapi enggak punya ketemu kesempatan. Jadi gua mau coba memberi kesempatan karena gua punya resource tersebut. Jadi itu yang gua lakukan sekarang.
```

- **A**: Ini adalah bagian dari wawancara dengan KJo tentang pengembangan AI personal untuk trading, di mana ia membahas keinginannya untuk membantu orang lain yang memiliki potensi namun kekurangan kesempatan.
- **B**: KJo membahas tujuan hidup dan cara ia menggunakan kekayaan untuk membantu orang lain, serta gagasan memberi kesempatan kepada orang-orang berbakat yang masih mengalami kesulitan.
- **C**: KJo menjelaskan bagaimana ia menggunakan sumber daya yang dimilikinya untuk membantu orang pintar yang tidak punya kesempatan, dengan fokus pada keberhasilan hidup dan keberkahan melalui keberadaan karyawan.
