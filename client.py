import logging
import sys
import threading
from argparse import ArgumentParser

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
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.address
    server_port = namespace.port
    client_name = namespace.name

    if not 1023 < namespace.port < 65536:
        client_logger.critical(f'Порт "{server_port}" введен некорректно. '
                               f'Необходимо ввести значение от 1024 до 65535.')
        sys.exit(1)

    return server_address, server_port, client_name


def main():
    server_address, server_port, client_name = args_parser()

    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    database = ClientDatabase(client_name)

    # Создаём объект - транспорт и запускаем транспортный поток
    try:
        transport = ClientTransport(server_address, server_port, database, client_name)
    except Exception as e:
        print(e)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат Программа - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()


if __name__ == '__main__':
    main()
