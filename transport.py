import binascii
import hashlib
import hmac
import json
import logging
import sys
import threading
import time
from socket import socket, AF_INET, SOCK_STREAM

from PyQt5.QtCore import QObject, pyqtSignal

import log.client_log_config
from utils import send_message, get_message

client_logger = logging.getLogger('client')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, account_name, password, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.account_name = account_name
        self.password = password
        self.s = None
        self.keys = keys
        self.connection_init(port, ip_address)

        try:
            users_list = self.clients_list_request()
        except:
            client_logger.error('Ошибка запроса списка известных пользователей.')
        else:
            database.add_users(users_list)

        try:
            contacts_list = self.contacts_list_request()
        except:
            client_logger.error('Ошибка запроса списка контактов.')
        else:
            for contact in contacts_list:
                database.add_contact(contact)

        # Флаг продолжения работы транспорта.
        self.running = True

    def connection_init(self, server_address, server_port):
        try:
            self.s = socket(AF_INET, SOCK_STREAM)
            self.s.settimeout(5)
            self.s.connect((server_address, server_port))
        except ConnectionRefusedError:
            client_logger.error('Неудачная попытка подключения к серверу!')
            sys.exit(1)

        passwd_bytes = self.password.encode('utf-8')
        salt = self.account_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')

        try:
            with socket_lock:
                msg = self.create_presence(pubkey)
                send_message(self.s, msg)
                ans = get_message(self.s)
                client_logger.debug(f'Server response = {ans}.')
                if 'response' in ans:
                    if ans['response'] == 400:
                        print(f'400 : {msg["error"]}')
                    elif ans['response'] == 511:
                        ans_data = ans['data']
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = {'response': 511, 'data': binascii.b2a_base64(
                            digest).decode('ascii')}
                        send_message(self.s, my_ans)
                        self.process_ans(get_message(self.s))

        except (OSError, json.JSONDecodeError):
            client_logger.critical('Потеряно соединение с сервером!')
            sys.exit(1)

    def create_presence(self, pubkey):
        presense = {
            'action': 'presence',
            'time': time.time(),
            'type': 'status',
            'user': {
                'account_name': self.account_name,
                'status': 'Yep, I am here!',
                'public_key': pubkey
            }
        }
        return presense

    def process_ans(self, msg):
        if 'response' in msg:
            if msg['response'] == 200:
                return
            elif msg['response'] == 400:
                print(f'400 : {msg["error"]}')
            elif msg['response'] == 205:
                self.clients_list_request()
                self.contacts_list_request()
                self.message_205.emit()
            else:
                client_logger.debug(f'Принят неизвестный код подтверждения {msg["response"]}')

        elif 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg and \
                'destination' in msg and 'message_text' in msg and msg['destination'] == self.account_name:
            client_logger.debug(f'Получено сообщение от пользователя {msg["sender"]}:{msg["message_text"]}')
            self.new_message.emit(msg)

    def contacts_list_request(self):
        req = {
            'action': 'get_contacts',
            'time': time.time(),
            'user': self.account_name
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if 'response' in ans and ans['response'] == 202:
            return ans['alert']
        else:
            client_logger.error('Не удалось обновить список контактов.')

    def clients_list_request(self):
        req = {
            'action': 'clients_request',
            'time': time.time(),
            'user': self.account_name,
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if 'response' in ans and ans['response'] == 202:
            return ans['alert']
        else:
            client_logger.error('Не удалось обновить список пользователей.')

    def key_request(self, user):
        client_logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            'action': 'public_key_request',
            'time': time.time(),
            'account_name': user,
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if 'response' in ans and ans['response'] == 511:
            return ans['data']
        else:
            client_logger.error(f'Не удалось получить ключ собеседника{user}.')

    def add_contact(self, contact):
        req = {
            'action': 'add_contact',
            'time': time.time(),
            'user': self.account_name,
            'contact': contact
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if 'response' in ans and ans['response'] == 200:
            pass
        else:
            raise ValueError
        print('Удачное создание контакта.')

    def delete_contact(self, contact):
        req = {
            'action': 'delete_contact',
            'time': time.time(),
            'user': self.account_name,
            'contact': contact
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if 'response' in ans and ans['response'] == 200:
            pass
        else:
            raise ValueError
        print('Удачное удаление контакта')

    # Функция закрытия соединения, отправляет сообщение о выходе.
    def transport_shutdown(self):
        self.running = False
        exit_msg = {
            'action': 'exit',
            'time': time.time(),
            'user': self.account_name
        }

        with socket_lock:
            try:
                send_message(self.s, exit_msg)
            except OSError:
                pass
        client_logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def send_message_to_server(self, to_user, message):
        dict_message = {
            'action': 'message',
            'time': time.time(),
            'sender': self.account_name,
            'destination': to_user,
            'message_text': message
        }
        with socket_lock:
            send_message(self.s, dict_message)
            self.process_ans(get_message(self.s))
            client_logger.info(f'Отправлено сообщение для пользователя {to_user}')

    def run(self):
        client_logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.s.settimeout(0.5)
                    message = get_message(self.s)
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.s.settimeout(5)
            if message:
                client_logger.debug(f'Принято сообщение с сервера: {message}')
                self.process_ans(message)
