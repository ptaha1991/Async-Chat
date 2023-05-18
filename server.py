import logging
import sys
from argparse import ArgumentParser
from select import select
from socket import socket, AF_INET, SOCK_STREAM

from decorator import logs
from descriptor import WrongPort
from metaclasses import ServerVerifier
from utils import get_message, send_message
import log.server_log_config

server_logger = logging.getLogger('server')


@logs
def arg_parser():
    default_port = 7777
    parser = ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    listen_address = namespace.a
    listen_port = namespace.p

    return listen_address, listen_port


class Server(metaclass=ServerVerifier):
    port = WrongPort()

    def __init__(self, listen_address, listen_port):
        self.address = listen_address
        self.port = listen_port
        self.clients_list = []
        self.messages_list = []
        self.names = dict()

    def init_socket(self):
        server_logger.info(
            f'Запущен сервер, порт для подключений: {self.port}, '
            f'адрес с которого принимаются подключения: {self.address}. '
            f'Если адрес не указан, принимаются соединения с любых адресов.')
        s = socket(AF_INET, SOCK_STREAM)
        s.bind((self.address, self.port))
        s.settimeout(0.5)
        self.s = s
        s.listen(5)

    def main_loop(self):
        self.init_socket()

        while True:
            try:
                client, client_address = self.s.accept()
            except OSError as e:
                pass
            else:
                server_logger.info(f'Установлено соедение с ПК {client_address}')
                self.clients_list.append(client)

            r = []
            w = []
            try:
                if self.clients_list:
                    r, w, e = select(self.clients_list, self.clients_list, [], 1)
            except OSError:
                pass

            if r:
                for client_with_message in r:
                    try:
                        self.process_client_message(get_message(client_with_message), client_with_message)
                    except:
                        server_logger.info(f'Клиент {client_with_message.getpeername()} отключился от сервера.')
                        self.clients_list.remove(client_with_message)

            for i in self.messages_list:
                try:
                    self.message_to_client(i, w)
                except:
                    server_logger.info(f'Связь с клиентом с именем {i["destination"]} была потеряна')
                    self.clients_list.remove(self.names[i["destination"]])
                    del self.names[i["destination"]]
            self.messages_list.clear()

    def process_client_message(self, msg, client):
        server_logger.debug(f'Разбор сообщения от клиента : {msg}')
        if 'action' in msg and msg['action'] == 'presence' and 'time' in msg and \
                'user' in msg:
            if msg['user']['account_name'] not in self.names.keys():
                self.names[msg['user']['account_name']] = client
                send_message(client, {'response': 200})
            else:
                send_message(client, {'response': 400, 'error': 'Имя пользователя уже занято.'})
                self.clients_list.remove(client)
                client.close()
            return

        elif 'action' in msg and msg['action'] == 'message' and 'time' in msg and 'sender' in msg and \
                'destination' in msg and 'message_text' in msg:
            self.messages_list.append(msg)
            return
        elif 'action' in msg and msg['action'] == 'exit' and 'user' in msg:
            self.clients_list.remove(self.names[msg['user']])
            self.names[msg['user']].close()
            del self.names[msg['user']]
            return
        else:
            send_message(client, {
                'response': 400,
                'error': 'Bad Request'
            })
            return

    def message_to_client(self, msg, listen_socks):
        if msg['destination'] in self.names and self.names[msg['destination']] in listen_socks:
            send_message(self.names[msg['destination']], msg)
            server_logger.info(
                f'Отправлено сообщение пользователю {msg["destination"]} от пользователя {msg["sender"]}.')
        else:
            server_logger.error(f'Отправка сообщения невозможна.')


def main():
    listen_address, listen_port = arg_parser()
    server = Server(listen_address, listen_port)
    server.main_loop()


if __name__ == '__main__':
    main()
