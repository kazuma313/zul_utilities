import json

def documents_to_custom_json(documents, key_mapping=None, return_dict=False):
    """
    Konversi dengan mapping key yang customizable
    Output dijamin berupa valid JSON string atau Python object
    """
    if key_mapping is None:
        key_mapping = {"page_content": "page_content"}
    
    docs_list = []
    
    for doc in documents:
        doc_dict = {}
        
        # Set page_content dengan nama key yang diinginkan
        content_key = key_mapping.get("page_content", "page_content")
        doc_dict[content_key] = doc.page_content
        
        if hasattr(doc, 'metadata') and doc.metadata:
            for key, value in doc.metadata.items():
                # Cek jika ada mapping untuk key dari metadata
                new_key = key_mapping.get(key, key)
                
                # Hindari override content key
                if new_key != content_key:
                    doc_dict[new_key] = value
                else:
                    doc_dict[f"metadata_{new_key}"] = value
        
        docs_list.append(doc_dict)
    
    # Return Python object jika diminta (valid JSON-serializable object)
    if return_dict:
        # Validasi bahwa object bisa di-serialize ke JSON
        try:
            json.dumps(docs_list)  # Test serialization
            return docs_list
        except (TypeError, ValueError) as e:
            raise ValueError(f"Object is not JSON-serializable: {e}")
    
    # Return JSON string (default)
    try:
        json_string = json.dumps(docs_list, indent=2, ensure_ascii=False)
        
        # Validasi bahwa output adalah valid JSON dengan parse test
        json.loads(json_string)  # Will raise ValueError if invalid
        
        return json_string
    except (TypeError, ValueError) as e:
        raise ValueError(f"Error creating valid JSON: {e}")

# # Contoh penggunaan dengan mapping multiple keys
# key_mapping = {
#     "page_content": "text",  # page_content → text
#     "source": "url",         # source → url
#     "chapter": "section"     # chapter → section
# }

# json_output = documents_to_custom_json(documents, key_mapping)
# print("Dengan custom mapping:")
# print(json_output)
