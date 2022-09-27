
import json
def data_to_bytes(data, data_type:str):
    """data_type only 'text', 'json', 'object' """


    if data_type == "text":
        data_for_send = bytes(data, encoding='utf-8')

    elif data_type == "json":
        data_for_send = bytes(json.dumps(data), encoding="utf-8")

    else:
        data_for_send = None

    return data_for_send

def data_from_bytes(bytes_data, data_type:str):

    if data_type == "text":

        return str(bytes_data, encoding='utf-8')

    elif data_type == "json":
        return json.loads(str(bytes_data, encoding='utf-8'))

def data_for_send(data, data_type):

    bytes_data = data_to_bytes(data, data_type)

    headers = {"type":data_type,
               "len": len(bytes_data)}

    return headers, bytes_data

