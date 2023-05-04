# 2. В каждом модуле выполнить настройку соответствующего логгера по следующему алгоритму:
# Создание именованного логгера;
# Сообщения лога должны иметь следующий формат: "<дата-время> <уровеньважности> <имямодуля> <сообщение>";
# Журналирование должно производиться в лог-файл;
# На стороне сервера необходимо настроить ежедневную ротацию лог-файлов.
#
# 3. Реализовать применение созданных логгеров для решения двух задач:
# Журналирование обработки исключений try/except.
# Вместо функции print() использовать журналирование и обеспечить вывод служебных сообщений в лог-файл;


import logging.handlers
import os
import sys
sys.path.append('../')


formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'server.log')

error_hand = logging.StreamHandler(sys.stderr)
error_hand.setLevel(logging.ERROR)
error_hand.setFormatter(formatter)

# настроить ежедневную ротацию лог-файлов
log_file = logging.handlers.TimedRotatingFileHandler(PATH, encoding='utf8', interval=1, when='D')
log_file.setFormatter(formatter)

logger = logging.getLogger('server')
logger.addHandler(error_hand)
logger.addHandler(log_file)
logger.setLevel(logging.DEBUG)


if __name__ == '__main__':
    logger.critical('Creeping death detected!')
    logger.error('Error')
    logger.info('INFO')
