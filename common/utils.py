import json

from common.decorators import logs


@logs
def get_message(client):
    """
    Функция приёма сообщений от удалённых компьютеров.
    Принимает сообщения JSON, декодирует полученное сообщение
    и проверяет что получен словарь.
    """
    encoded_response = client.recv(10240)
    json_response = encoded_response.decode('utf-8')
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@logs
def send_message(s, msg):
    """
    Функция отправки словарей через сокет.
    Кодирует словарь в формат JSON и отправляет через сокет.
    """
    js_message = json.dumps(msg)
    encoded_message = js_message.encode('utf-8')
    s.send(encoded_message)
