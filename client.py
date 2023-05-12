import logging
import sys
import threading
import time
from argparse import ArgumentParser
from socket import AF_INET, SOCK_STREAM, socket

from utils import create_presence, send_message, process_ans, get_message, message_from_server, client_commands
import log.client_log_config

client_logger = logging.getLogger('client')


def args_parser():
    default_address = '127.0.0.1'
    default_port = 7776
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
    if not client_name:
        client_name = input('Введите свое имя: ')

    try:
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((server_address, server_port))
        msg = create_presence(client_name)
        send_message(s, msg)
        answer = process_ans(get_message(s))
        client_logger.info(f'Принят ответ от сервера {answer}')
    except ConnectionRefusedError:
        client_logger.error('Неудачная попытка подключения к серверу!')
        sys.exit(1)

    # 2 потока на прием и отправку сообщений
    read_thread = threading.Thread(target=message_from_server, args=(s, client_name))
    read_thread.daemon = True
    read_thread.start()

    send_thread = threading.Thread(target=client_commands, args=(s, client_name))
    send_thread.daemon = True
    send_thread.start()

    while True:
        time.sleep(1)
        if read_thread.is_alive() and send_thread.is_alive():
            continue
        break


if __name__ == '__main__':
    main()
