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

from common.utils import send_message, get_message

client_logger = logging.getLogger('client_module')
socket_lock = threading.Lock()


class ClientTransport(threading.Thread, QObject):
    """
    Класс реализующий транспортную подсистему клиентского модуля.
    Отвечает за взаимодействие с сервером.
    """
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, account_name,
                 password, keys):
        threading.Thread.__init__(self)
        QObject.__init__(self)

        self.database = database
        self.account_name = account_name
        self.password = password
        self.s = None
        self.keys = keys
        self.connection_init(port, ip_address)

        try:
            self.clients_list_request()
            self.contacts_list_request()
        except OSError as err:
            if err.errno:
                client_logger.critical('Потеряно соединение с сервером.')
            client_logger.error(
                'Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            client_logger.critical('Потеряно соединение с сервером.')

        # Флаг продолжения работы транспорта.
        self.running = True

    def connection_init(self, server_address, server_port):
        """Метод отвечающий за установку соединения с сервером."""
        try:
            self.s = socket(AF_INET, SOCK_STREAM)
            self.s.settimeout(5)
            self.s.connect((server_address, server_port))
        except ConnectionRefusedError:
            client_logger.error('Неудачная попытка подключения к серверу!')
            sys.exit(1)

        # Запускаем процедуру авторизации. Получаем хэш пароля.
        passwd_bytes = self.password.encode('utf-8')
        salt = self.account_name.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')

        with socket_lock:
            try:
                msg = self.create_presence(pubkey)
                send_message(self.s, msg)
                ans = get_message(self.s)
                client_logger.debug(f'Server response = {ans}.')
                if 'response' in ans:
                    if ans['response'] == 400:
                        print(f'400 : {msg["error"]}')
                    elif ans['response'] == 511:
                        ans_data = ans['data']
                        hash = hmac.new(
                            passwd_hash_string,
                            ans_data.encode('utf-8'),
                            'MD5')
                        digest = hash.digest()
                        my_ans = {'response': 511,
                                  'data': binascii.b2a_base64(digest)
                                  .decode('ascii')}
                        send_message(self.s, my_ans)
                        self.process_ans(get_message(self.s))

            except (OSError, json.JSONDecodeError):
                client_logger.critical('Потеряно соединение с сервером!')
                sys.exit(1)

    def create_presence(self, pubkey):
        """Метод возвращающий сообщение о присутствии"""
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
        """Метод обработчик поступающих сообщений с сервера."""
        if 'response' in msg:
            if msg['response'] == 200:
                return
            elif msg['response'] == 400:
                print(f'400 : {msg["error"]}')
            elif msg['response'] == 205:
                self.database.contacts_clear()
                self.clients_list_request()
                self.contacts_list_request()
                self.message_205.emit()
            else:
                client_logger.debug(
                    f'Принят неизвестный код подтверждения {msg["response"]}')

        elif 'action' in msg and msg['action'] == 'message' and 'time' in msg \
                and 'sender' in msg and 'destination' in msg and \
                'message_text' in msg and \
                msg['destination'] == self.account_name:
            client_logger.debug(
                f'Получено сообщение от пользователя '
                f'{msg["sender"]}:{msg["message_text"]}')
            self.new_message.emit(msg)

    def contacts_list_request(self):
        """Метод обновляющий список контактов с сервера."""
        req = {
            'action': 'get_contacts',
            'time': time.time(),
            'user': self.account_name
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
            client_logger.debug(
                f'Принято ответ с сервера с контакт листом: {ans}')
        if 'response' in ans and ans['response'] == 202:
            for contact in ans['alert']:
                self.database.add_contact(contact)
        else:
            client_logger.error('Не удалось обновить список контактов.')

    def clients_list_request(self):
        """Метод обновляющий список пользователей с сервера."""
        req = {
            'action': 'clients_request',
            'time': time.time(),
            'user': self.account_name,
        }
        with socket_lock:
            send_message(self.s, req)
            ans = get_message(self.s)
        if 'response' in ans and ans['response'] == 202:
            self.database.add_users(ans['alert'])
        else:
            client_logger.error('Не удалось обновить список пользователей.')

    def key_request(self, user):
        """Метод запрашивающий с сервера публичный ключ пользователя."""
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
        """Метод отправляющий на сервер сведения о добавлении контакта."""
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
        """Метод отправляющий на сервер сведения об удалении контакта."""
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

    def transport_shutdown(self):
        """Метод уведомляющий сервер о завершении работы клиента."""
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
        """Метод отправляющий на сервер сообщения для пользователя."""
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
            client_logger.info(
                f'Отправлено сообщение для пользователя {to_user}')

    def run(self):
        """Метод содержащий основной цикл работы транспортного потока."""
        client_logger.debug('Запущен процесс - приёмник сообщений с сервера.')
        while self.running:
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.s.settimeout(0.5)
                    message = get_message(self.s)
                except OSError as err:
                    if err.errno:
                        client_logger.critical(
                            'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                except (ConnectionError,
                        ConnectionAbortedError,
                        ConnectionResetError,
                        json.JSONDecodeError,
                        TypeError):
                    client_logger.debug('Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                finally:
                    self.s.settimeout(5)
            if message:
                client_logger.debug(f'Принято сообщение с сервера: {message}')
                self.process_ans(message)
