import json
import time

from decorator import logs


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


# Server
@logs
def process_client_message(msg):
    if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
            'user' in msg and msg['user']['account_name'] == 'User':
        return {'response': 200}
    return {
        'response': 400,
        'error': 'Bad Request'
    }
