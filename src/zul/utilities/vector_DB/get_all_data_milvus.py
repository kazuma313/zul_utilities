"""
GET DATA ALL DATA FROM MILVUS COLLECTION
"""


# def filter_data(datas):
#     store_data= []
#     for data in datas:
#         judul_peraturan = data['metadata'].get('judul_peraturan')
#         fields_outside = {k: v for k, v in data.items() if k != 'metadata'}
#         fields_outside["judul_peraturan"] = judul_peraturan
#         store_data.append(fields_outside)
#     return store_data


# results = []
# batch_size = 1024  # any value up to 16384 is fine

# milvus_lis = MilvusHelperLis(
#         collection_name=CONFIG_MILVUS_LIS['collection_name_v2']
#     )

# iterator = milvus_lis.client.query_iterator(
#     collection_name=CONFIG_MILVUS_LIS['collection_name_v2'],
#     batch_size=batch_size,
#     filter="judul != ''",
#     output_fields=OUTPUT_FIELD,
# )

# try:
#     while True:
#         batch = iterator.next()
#         if not batch:
#             break

#         filtered_batch = filter_data(batch)
#         results += filtered_batch

# finally:
#     iterator.close()

# print(f"Total results retrieved: {len(results)}")
