import os
from subprocess import Popen

clients_list = []
server = ''
path = os.path.dirname(__file__)
path_to_server = os.path.join(path, "server.py")
path_to_client = os.path.join(path, "client.py")

while True:
    action = input('открыть сервер (o), запустить 4 клиента (s), выйти (q)')
    if action == 'q':
        break
    elif action == 'o':
        print("Запустили сервер")
        server = Popen(
            f'osascript -e \'tell application "Terminal" to do'
            f' script "python3 {path_to_server}"\'', shell=True)
    elif action == 's':
        print("Запустили 4 клиента")
        for i in range(4):
            clients_list.append(
                Popen(
                    f'osascript -e \'tell application "Terminal" to do'
                    f' script "python3 {path_to_client} -n client{i + 1}"\'',
                    shell=True))
