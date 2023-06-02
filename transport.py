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
    new_message = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, account_name):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.account_name = account_name
        self.s = None
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

        try:
            with socket_lock:
                msg = self.create_presence()
                send_message(self.s, msg)
                answer = self.process_ans(get_message(self.s))
                client_logger.info(f'Принят ответ от сервера {answer}')
        except (OSError, json.JSONDecodeError):
            client_logger.critical('Потеряно соединение с сервером!')
            sys.exit(1)

    def create_presence(self):
        presense = {
            'action': 'presence',
            'time': time.time(),
            'type': 'status',
            'user': {
                'account_name': self.account_name,
                'status': 'Yep, I am here!'
            }
        }
        return presense

    def process_ans(self, msg):
        if 'response' in msg:
            if msg['response'] == 200:
                return '200 : OK'
            elif msg['response'] == 400:
                return f'400 : {msg["error"]}'
            else:
                client_logger.debug(f'Принят неизвестный код подтверждения {msg["response"]}')

        elif 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg and \
                'destination' in msg and 'message_text' in msg and msg['destination'] == self.account_name:
            self.database.save_message(msg['sender'], 'in', msg['message_text'])
            self.new_message.emit(msg['sender'])

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
            with socket_lock:
                try:
                    self.s.settimeout(0.5)
                    message = get_message(self.s)
                except OSError as err:
                    if err.errno:
                        client_logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    client_logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    client_logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_ans(message)
                finally:
                    self.s.settimeout(5)
