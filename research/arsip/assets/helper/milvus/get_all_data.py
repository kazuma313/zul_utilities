from connections.milvus_connection_lis import MilvusHelperLis
from constants.config import CONFIG_MILVUS_LIS

milvus_lis = MilvusHelperLis(
        collection_name=CONFIG_MILVUS_LIS['collection_name_v2']
    )


OUTPUT_FIELD = [
    # "page_content",
    "metadata_text",
    "judul",
    "nomor",
    # "tentang",
    # "bab",
    # "deskripsi_bab",
    # "bagian",
    # "pasal",
    # "deskripsi_pasal",
    # "penjelasan_pasal",
    # "ayat",
    # "flag_corrupted",
    # "is_law_doc",
    "es_doc_id",
    # "kategori_document",
    # "chunk_index",
    # "ketentuan_peralihan",
    # "mengingat",
    "metadata"
]


def filter_data(datas):
    store_data= []
    for data in datas:
        judul_peraturan = data['metadata'].get('judul_peraturan')
        fields_outside = {k: v for k, v in data.items() if k != 'metadata'}
        fields_outside["judul_peraturan"] = judul_peraturan
        store_data.append(fields_outside)
    return store_data

results = []
batch_size = 1024  # any value up to 16384 is fine

iterator = milvus_lis.client.query_iterator(
    collection_name=CONFIG_MILVUS_LIS['collection_name_v2'],
    batch_size=batch_size,
    filter="judul != ''",
    output_fields=OUTPUT_FIELD,
)

try:
    while True:
        batch = iterator.next()
        if not batch:
            break

        filtered_batch = filter_data(batch)
        results += filtered_batch

finally:
    iterator.close()

print(f"Total results retrieved: {len(results)}")


# 2. Specify the filename
filename = "data_list_3.json"
import json

# 3. Open the file in write mode and dump the data
try:
    with open(filename, 'w') as json_file:
        json.dump(results, json_file, indent=4)
    print(f"Successfully saved list to {filename}")
except IOError as e:
    print(f"Error saving file: {e}")