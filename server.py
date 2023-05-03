# Реализовать простое клиент-серверное взаимодействие по протоколу JIM (JSON instant messaging):
# a. клиент отправляет запрос серверу;
# b. сервер отвечает соответствующим кодом результата.
# Клиент и сервер должны быть реализованы в виде отдельных скриптов, содержащих соответствующие функции.
#
# Функции клиента:
# ● сформировать presence-сообщение;
# ● отправить сообщение серверу;
# ● получить ответ сервера;
# ● разобрать сообщение сервера;
# ● параметры командной строки скрипта client.py <addr> [<port>]:
# ○ addr — ip-адрес сервера;
# ○ port — tcp-порт на сервере, по умолчанию 7777.
#
# Функции сервера:
# ● принимает сообщение клиента;
# ● формирует ответ клиенту;
# ● отправляет ответ клиенту;
# ● имеет параметры командной строки:
# ○ -p <port> — TCP-порт для работы (по умолчанию использует 7777);
# ○ -a <addr> — IP-адрес для прослушивания (по умолчанию слушает все
# доступные адреса).
import json
import sys
from socket import socket, AF_INET, SOCK_STREAM

from utils import get_message, process_client_message, send_message


def main():
    try:
        if '-p' in sys.argv:
            listen_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            listen_port = 7777
        if listen_port < 1024 or listen_port > 65535:
            raise ValueError
    except IndexError:
        print('После параметра -\'p\' необходимо указать номер порта.')
        sys.exit(1)
    except ValueError:
        print(
            'В качастве порта может быть указано только число в диапазоне от 1024 до 65535.')
        sys.exit(1)


    try:
        if '-a' in sys.argv:
            listen_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            listen_address = ''

    except IndexError:
        print(
            'После параметра \'a\'- необходимо указать адрес, который будет слушать сервер.')
        sys.exit(1)

    s = socket(AF_INET, SOCK_STREAM)
    s.bind((listen_address, listen_port))
    s.listen(5)

    while True:
        client, client_address = s.accept()
        try:
            message_from_client = get_message(client)
            response = process_client_message(message_from_client)
            send_message(client, response)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Принято некорретное сообщение от клиента.')
            client.close()


if __name__ == '__main__':
    main()
