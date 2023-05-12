import json
import logging
import sys
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


def create_exit_message(account_name):
    exit_msg = {
        'action': 'exit',
        'time': time.time(),
        'user': account_name
    }
    return exit_msg


@logs
def create_message(sock, sender):
    to_user = input('Введите получателя сообщения: ')
    message = input('Введите сообщение: ')
    dict_message = {
        'action': 'message',
        'time': time.time(),
        'sender': sender,
        'destination': to_user,
        'message_text': message
    }
    return dict_message


@logs
def process_ans(message):
    if 'response' in message:
        if message['response'] == 200:
            return '200 : OK'
        return f'400 : {message["error"]}'
    raise ValueError


@logs
def message_from_server(s, account_name):
    while True:
        try:
            msg = get_message(s)
            if 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg \
                    and 'destination' in msg and 'message_text' in msg and msg['destination'] == account_name:
                print(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
                client_logger.info(f'Получено сообщение от пользователя {msg["sender"]}: {msg["message_text"]}')
            else:
                client_logger.error(f'Получено некорректное сообщение с сервера: {msg}')
        except:
            server_logger.critical(f'Потеряно соединение с сервером.')
            break


def client_commands(s, account_name):
    print('Отправить сообщение (send), выйти (exit)')
    while True:
        command = input('Введите команду: ')
        if command == 'send':
            try:
                send_message(s, create_message(s, account_name))
                client_logger.info(f'Сообщение  от пользователя {account_name} успешно отправлено')
            except:
                client_logger.critical('Потеряно соединение с сервером.')
                sys.exit(1)

        elif command == 'exit':
            send_message(s, create_exit_message(account_name))
            print('Завершение соединения.')
            time.sleep(1)
            break
        else:
            print('Что то пошло не так, попробуйте еще раз!')


# Server
@logs
def process_client_message(msg, msg_list, client, clients_list, names):
    server_logger.debug(f'Разбор сообщения от клиента : {msg}')
    if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
            'user' in msg:
        if msg['user']['account_name'] not in names.keys():
            names[msg['user']['account_name']] = client
            send_message(client, {'response': 200})
        else:
            send_message(client, {'response': 400, 'error': 'Имя пользователя уже занято.'})
            clients_list.remove(client)
            client.close()
        return

    elif 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg and \
            'destination' in msg and 'message_text' in msg:
        msg_list.append(msg)
        return
    elif 'action' in msg and msg['action'] == 'exit' and 'user' in msg:
        clients_list.remove(names[msg['user']])
        names[msg['user']].close()
        del names[msg['user']]
        return
    else:
        send_message(client, {
            'response': 400,
            'error': 'Bad Request'
        })
        return


@logs
def message_to_client(msg, names, listen_socks):
    if msg['destination'] in names and names[msg['destination']] in listen_socks:
        send_message(names[msg['destination']], msg)
        server_logger.info(f'Отправлено сообщение пользователю {msg["destination"]} от пользователя {msg["sender"]}.')
    else:
        client_logger.error(f'Отправка сообщения невозможна.')

