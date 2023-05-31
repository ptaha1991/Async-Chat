import json
import logging
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
def create_presence(account_name):
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
def contacts_list_request(sock, username):
    req = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': username
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['alert']
    else:
        raise ValueError


@logs
def add_contact(sock, username, contact):
    req = {
        'action': 'add_contact',
        'time': time.time(),
        'user': username,
        'contact': contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise ValueError
    print('Удачное создание контакта.')


@logs
def delete_contact(sock, username, contact):
    req = {
        'action': 'delete_contact',
        'time': time.time(),
        'user': username,
        'contact': contact
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        raise ValueError
    print('Удачное удаление контакта')


@logs
def clients_list_request(sock, username):
    req = {
        'action': 'clients_request',
        'time': time.time(),
        'user': username,
    }
    send_message(sock, req)
    ans = get_message(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['alert']
    else:
        raise ValueError
