import logging.handlers
import os
import sys
sys.path.append('../')


formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(message)s')

PATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(PATH, 'client.log')

error_hand = logging.StreamHandler(sys.stderr)
error_hand.setLevel(logging.ERROR)
error_hand.setFormatter(formatter)

log_file = logging.FileHandler(PATH,  encoding='utf8')
log_file.setFormatter(formatter)


logger = logging.getLogger('client')
logger.addHandler(error_hand)
logger.addHandler(log_file)
logger.setLevel(logging.INFO)


if __name__ == '__main__':
    logger.critical('Creeping death detected!')
    logger.error('Error')
    logger.debug('Debug')
    logger.info('INFO')
