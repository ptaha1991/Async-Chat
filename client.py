import logging
import os
import sys
import threading
from argparse import ArgumentParser

from Crypto.PublicKey import RSA
from PyQt5.QtWidgets import QApplication

from client_database import ClientDatabase
from client_gui import UserNameDialog, ClientMainWindow
from transport import ClientTransport

import log.client_log_config

client_logger = logging.getLogger('client')

sock_lock = threading.Lock()
database_lock = threading.Lock()


def args_parser():
    default_address = '127.0.0.1'
    default_port = 7777
    parser = ArgumentParser()
    parser.add_argument('address', default=default_address, nargs='?')
    parser.add_argument('port', default=default_port, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.address
    server_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password

    if not 1023 < namespace.port < 65536:
        client_logger.critical(f'Порт "{server_port}" введен некорректно. '
                               f'Необходимо ввести значение от 1024 до 65535.')
        sys.exit(1)

    return server_address, server_port, client_name, client_passwd


def main():
    server_address, server_port, client_name, client_passwd = args_parser()

    client_app = QApplication(sys.argv)

    if not client_name or not client_passwd:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            client_logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)

    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())

    client_logger.debug("Keys sucsessfully loaded.")

    database = ClientDatabase(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_address, server_port, database, client_name, client_passwd, keys)
    except Exception as e:
        print(e)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    del start_dialog

    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
