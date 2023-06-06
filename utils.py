import json

from decorator import logs


@logs
def get_message(client):
    encoded_response = client.recv(10240)
    json_response = encoded_response.decode('utf-8')
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@logs
def send_message(s, msg):
    js_message = json.dumps(msg)
    encoded_message = js_message.encode('utf-8')
    s.send(encoded_message)
