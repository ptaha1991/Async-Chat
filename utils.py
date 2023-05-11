import json
import logging
import time

from decorator import logs

import log.client_log_config
import log.server_log_config

client_logger = logging.getLogger('client')
server_logger = logging.getLogger('server')


@logs
def get_message(client):
    encoded_response = client.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode('utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        raise ValueError
    raise ValueError


@logs
def send_message(s, msg):
    js_message = json.dumps(msg)
    encoded_message = js_message.encode('utf-8')
    s.send(encoded_message)


# Client
@logs
def create_presence(account_name='User'):
    presense = {
        'action': 'presence',
        'time': time.time(),
        'type': 'status',
        'user': {
            'account_name': account_name,
            'status': 'Yep, I am here!'
        }
    }
    return presense


@logs
def process_ans(message):
    if 'response' in message:
        if message['response'] == 200:
            return '200 : OK'
        return f'400 : {message["error"]}'
    raise ValueError


@logs
def message_from_server(msg):
    if 'action' in msg and msg['action'] == 'message' and 'time' in msg and \
            'sender' in msg and 'message_text' in msg:
        print(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
        client_logger.info(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
    else:
        client_logger.error(f'Получено некорректное сообщение с сервера: {msg}')


@logs
def create_message(sock, sender='User'):
    message = input('Введите сообщение: ')
    dict_message = {
        'action': 'message',
        'time': time.time(),
        'sender': sender,
        'message_text': message
    }
    return dict_message


# Server
@logs
def process_client_message(msg, msg_list, client):
    server_logger.debug(f'Разбор сообщения от клиента : {msg}')
    if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
            'user' in msg and msg['user']['account_name'] == 'User':
        send_message(client, {'response': 200})
        return
    elif 'action' in msg and msg['action'] == 'message' and 'time' in msg and \
            "message_text" in msg:
        msg_list.append((msg['sender'], msg['message_text']))
        return
    else:
        send_message(client, {
            'response': 400,
            'error': 'Bad Request'
        })
        return
