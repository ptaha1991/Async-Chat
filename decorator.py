import inspect
import logging
import socket
from functools import wraps

import log.server_log_config
import log.client_log_config

server_logger = logging.getLogger('server')
client_logger = logging.getLogger('client')


def logs(func):
    @wraps(func)
    def log_saver(*args, **kwargs):
        ret = func(*args, **kwargs)
        out_func = inspect.stack()[1][3]
        server_logger.debug(
            f'Функция  "{func.__name__}" c аргументами {args}, {kwargs} вызвана из функции "{out_func}"')
        client_logger.debug(
            f'Функция  "{func.__name__}" c аргументами {args}, {kwargs} вызвана из функции "{out_func}"')
        return ret

    return log_saver


def login_required(func):
    def checker(*args, **kwargs):
        # проверяем, что первый аргумент - экземпляр Server
        # Импортить необходимо тут, иначе ошибка рекурсивного импорта.
        from server import Server
        if isinstance(args[0], Server):
            found = False
            for arg in args:
                if isinstance(arg, socket.socket):
                    # Проверяем, что данный сокет есть в списке names класса
                    # Server
                    for client in args[0].names:
                        if args[0].names[client] == arg:
                            found = True

            # Теперь надо проверить, что передаваемые аргументы не presence
            # сообщение. Если presense, то разрешаем
            for arg in args:
                if isinstance(arg, dict):
                    if 'action' in arg and arg['action'] == 'presence':
                        found = True
            # Если не не авторизован и не сообщение начала авторизации, то
            # вызываем исключение.
            if not found:
                raise TypeError
        return func(*args, **kwargs)

    return checker
