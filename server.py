import binascii
import configparser
import hmac
import json
import logging
import os
import sys
import threading

from argparse import ArgumentParser
from select import select
from socket import socket, AF_INET, SOCK_STREAM
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMessageBox

from common.decorators import logs, login_required
from common.descriptors import WrongPort, WrongAddress
from common.metaclasses import ServerVerifier
from common.utils import get_message, send_message
from server_module.server_database import ServerDatabase
from server_module.server_gui import MainWindow, gui_create_model, \
    ConfigWindow, HistoryWindow, AllClientsWindow, create_stat_model, \
    create_all_users_model, DelUserDialog, RegisterUser

server_logger = logging.getLogger('server_module')


@logs
def arg_parser(default_port, default_address):
    """Парсер аргументов командной строки."""
    parser = ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p
    return listen_address, listen_port


class Server(threading.Thread, metaclass=ServerVerifier):
    port = WrongPort()
    address = WrongAddress()

    def __init__(self, listen_address, listen_port, database):
        self.address = listen_address
        self.port = listen_port
        self.clients_list = []
        self.listen_sockets = None
        self.error_sockets = None
        self.names = dict()
        self.database = database
        super().__init__()

    def run(self):
        """Метод основной цикл потока Server."""
        self.init_socket()

        while True:
            try:
                client, client_address = self.s.accept()
            except OSError:
                pass
            else:
                server_logger.info(
                    f'Установлено соедение с ПК {client_address}')
                client.settimeout(5)
                self.clients_list.append(client)

            r = []
            try:
                if self.clients_list:
                    r, self.listen_sockets, self.error_sockets = select(
                        self.clients_list, self.clients_list, [], 0)
            except OSError:
                pass

            if r:
                for client_with_message in r:
                    try:
                        self.process_client_message(
                            get_message(client_with_message),
                            client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError):
                        server_logger.info(
                            f'Клиент {client_with_message.getpeername()} '
                            f'отключился от сервера.')
                        self.clients_list.remove(client_with_message)

    def init_socket(self):
        """Метод инициализатор сокета."""
        server_logger.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((self.address, self.port))
        s.settimeout(0.5)
        self.s = s
        s.listen(5)

    def remove_client(self, client):
        """
        Метод обработчик клиента с которым прервана связь.
        Ищет клиента и удаляет его из списков и базы:
        """
        server_logger.info(
            f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.client_logout(name)
                del self.names[name]
                break
        self.clients_list.remove(client)
        client.close()

    @login_required
    def process_client_message(self, msg, client):
        """Метод обработчик поступающих сообщений."""
        server_logger.debug(f'Разбор сообщения от клиента : {msg}')
        if 'action' in msg and msg['action'] == 'presence' \
                and 'time' in msg \
                and 'user' in msg:
            self.autorize_user(msg, client)

        elif 'action' in msg and msg['action'] == 'message' \
                and 'time' in msg \
                and 'sender' in msg and 'destination' in msg \
                and 'message_text' in msg \
                and self.names[msg['sender']] == client:
            if msg['destination'] in self.names:
                self.message_to_client(msg)
                try:
                    send_message(client, {'response': 200})
                except OSError:
                    self.remove_client(client)
            else:
                response = {
                    'response': 400,
                    'error': 'Пользователь не зарегистрирован на сервере.'
                }
                try:
                    send_message(client, response)
                except OSError:
                    pass
            return

        elif 'action' in msg and msg['action'] == 'exit' \
                and 'user' in msg \
                and self.names[msg['user']] == client:
            self.remove_client(client)

        elif 'action' in msg and msg['action'] == 'get_contacts' \
                and 'user' in msg \
                and self.names[msg['user']] == client:
            response = {
                'response': 202,
                'alert': self.database.get_contacts(msg['user'])
            }
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif 'action' in msg and msg['action'] == 'add_contact' \
                and 'contact' in msg \
                and 'user' in msg \
                and self.names[msg['user']] == client:
            self.database.add_contact_to_client(msg['user'], msg['contact'])
            try:
                send_message(client, {'response': 200})
            except OSError:
                self.remove_client(client)

        elif 'action' in msg and msg['action'] == 'delete_contact' \
                and 'contact' in msg \
                and 'user' in msg \
                and self.names[msg['user']] == client:
            self.database.delete_contact_from_client(
                msg['user'], msg['contact'])
            try:
                send_message(client, {'response': 200})
            except OSError:
                self.remove_client(client)

        elif 'action' in msg and msg['action'] == 'clients_request' \
                and 'user' in msg \
                and self.names[msg['user']] == client:
            response = {
                'response': 202,
                'alert': [user[0] for user in self.database.get_clients_list()]
            }
            try:
                send_message(client, response)
            except OSError:
                self.remove_client(client)

        elif 'action' in msg and msg['action'] == 'public_key_request' \
                and 'account_name' in msg:
            response = {
                'response': 511,
                'data': self.database.get_pubkey(msg['account_name'])
            }
            if response['data']:
                send_message(client, response)
            else:
                response = {
                    'response': 400,
                    'error': 'Нет публичного ключа для данного пользователя'
                }
                try:
                    send_message(client, response)
                except OSError:
                    self.remove_client(client)

        else:
            send_message(client, {'response': 400, 'error': 'Bad Request'})
            return

    def message_to_client(self, msg):
        """Метод отправки сообщения клиенту."""
        if msg['destination'] in self.names \
                and self.names[msg['destination']] in self.listen_sockets:
            try:
                send_message(self.names[msg['destination']], msg)
                server_logger.info(
                    f'Отправлено сообщение пользователю {msg["destination"]} '
                    f'от пользователя {msg["sender"]}.')
            except OSError:
                self.remove_client(msg["destination"])
        elif msg["destination"] in self.names \
                and self.names[msg["destination"]] not in self.listen_sockets:
            server_logger.error(
                f'Связь с клиентом {msg["destination"]} была потеряна. '
                f'Соединение закрыто, доставка невозможна.')
            self.remove_client(self.names[msg["destination"]])
        else:
            server_logger.error(
                f'Пользователь {msg["destination"]} не зарегистрирован '
                f'на сервере, отправка сообщения невозможна.')

    def autorize_user(self, message, sock):
        """Метод реализующий авторизацию пользователей."""
        server_logger.debug(f'Start auth process for {message["user"]}')
        if message['user']['account_name'] in self.names.keys():
            response = {
                'response': 400,
                'error': 'Имя пользователя уже занято.'
            }
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients_list.remove(sock)
            sock.close()

        elif not self.database.check_user(message['user']['account_name']):
            response = {
                'response': 400,
                'error': 'Пользователь не зарегистрирован.'
            }
            try:
                send_message(sock, response)
            except OSError:
                pass
            self.clients_list.remove(sock)
            sock.close()

        else:
            server_logger.debug('Correct username, starting passwd check.')
            message_auth = {'response': 511, 'data': None}
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            message_auth['data'] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой,
            # сохраняем серверную версию ключа
            hash = hmac.new(self.database.get_hash(
                message['user']['account_name']), random_str, 'MD5')
            digest = hash.digest()
            server_logger.debug(f'Auth message = {message_auth}')
            try:
                send_message(sock, message_auth)
                ans = get_message(sock)
            except OSError as err:
                server_logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans['data'])
            if 'response' in ans and ans['response'] == 511 \
                    and hmac.compare_digest(digest, client_digest):
                self.names[message['user']['account_name']] = sock
                client_ip, client_port = sock.getpeername()
                send_message(sock, {'response': 200})
                self.database.client_login(
                    message['user']['account_name'],
                    client_ip,
                    message['user']['public_key'])
            else:
                response = {'response': 400, 'error': 'Неверный пароль.'}
                try:
                    send_message(sock, response)
                except OSError:
                    pass
                self.clients_list.remove(sock)
                sock.close()

    def service_update_lists(self):
        """Метод реализующий отправку сервисного сообщения 205 клиентам."""
        for client in self.names:
            send_message(self.names[client], {'response': 205})


def main():
    """Основная функция сервера"""
    config = configparser.ConfigParser()

    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")

    listen_address, listen_port = arg_parser(
        config['SETTINGS']['Default_port'],
        config['SETTINGS']['Listen_Address'])

    database = ServerDatabase(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))

    server = Server(listen_address, listen_port, database)
    server.daemon = True
    server.start()

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    def show_all_clients():
        """Метод создающий окно со списком клиентов."""
        global all_clients
        all_clients = AllClientsWindow()
        all_clients.all_clients_table.setModel(
            create_all_users_model(database))
        all_clients.all_clients_table.resizeColumnsToContents()
        all_clients.all_clients_table.resizeRowsToContents()
        all_clients.show()

    def list_update():
        """Метод обновляющий список клиентов."""
        main_window.active_clients_table.setModel(gui_create_model(database))
        main_window.active_clients_table.resizeColumnsToContents()
        main_window.active_clients_table.resizeRowsToContents()

    def show_statistics():
        """Метод создающий окно со статистикой клиентов."""
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    def server_config():
        """Метод создающий окно с настройками сервера."""
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    def reg_user():
        """Метод создающий окно регистрации пользователя."""
        global reg_window
        reg_window = RegisterUser(database, server)
        reg_window.show()

    def rem_user():
        """Метод создающий окно удаления пользователя."""
        global rem_window
        rem_window = DelUserDialog(database, server)
        rem_window.show()

    def save_server_config():
        """
        Метод сохранения настроек.
        Проверяет правильность введённых данных и сохраняет ini файл.
        """
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.all_clients_button.triggered.connect(show_all_clients)
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)
    main_window.register_btn.triggered.connect(reg_user)
    main_window.remove_btn.triggered.connect(rem_user)

    server_app.exec_()


if __name__ == '__main__':
    main()
