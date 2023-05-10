import logging
import sys
from argparse import ArgumentParser
from socket import AF_INET, SOCK_STREAM, socket

from utils import create_presence, send_message, process_ans, get_message, create_message, message_from_server
import log.client_log_config

client_logger = logging.getLogger('client')


def args_parser():
    default_address = '127.0.0.1'
    default_port = 7776
    parser = ArgumentParser()
    parser.add_argument('address', default=default_address, nargs='?')
    parser.add_argument('port', default=default_port, type=int, nargs='?')
    parser.add_argument('-m', '--mode', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.address
    server_port = namespace.port
    client_mode = namespace.mode

    if not 1023 < namespace.port < 65536:
        client_logger.critical(f'Порт "{server_port}" введен некорректно. '
                               f'Необходимо ввести значение от 1024 до 65535.')
        sys.exit(1)
    if client_mode not in ('listen', 'send'):
        client_logger.critical(f'Указан недопустимый режим работы {client_mode}, '
                               f'допустимые режимы: listen , send')
        sys.exit(1)

    return server_address, server_port, client_mode


def main():
    server_address, server_port, client_mode = args_parser()
    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_address, server_port))
        msg = create_presence()
        send_message(s, msg)
        answer = process_ans(get_message(s))
        client_logger.info(f'Принят ответ от сервера {answer}')
    except ConnectionRefusedError:
        client_logger.error('Неудачная попытка подключения к серверу!')
        sys.exit(1)

    while True:
        if client_mode == 'send':
            print('Режим работы - отправка сообщений.')
            try:
                send_message(s, create_message(s))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                client_logger.error(f'Соединение с сервером {server_address} было потеряно.')
                sys.exit(1)

        elif client_mode == 'listen':
            print('Режим работы - приём сообщений.')
            try:
                message_from_server(get_message(s))
            except (ConnectionResetError, ConnectionError, ConnectionAbortedError):
                client_logger.error(f'Соединение с сервером {server_address} было потеряно.')
                sys.exit(1)


if __name__ == '__main__':
    main()
