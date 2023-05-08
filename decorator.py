# 1. Продолжая задачу логирования, реализовать декоратор @log, фиксирующий обращение к декорируемой функции.
# Он сохраняет ее имя и аргументы.
# 2. В декораторе @log реализовать фиксацию функции, из которой была вызвана декодированная. Если имеется такой код:
# @log
# def func_z():
# pass
# def main():
# func_z()
# ...в логе должна быть отражена информация:
# "<дата-время> Функция func_z() вызвана из функции main"
import inspect
import logging
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
