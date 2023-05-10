import os
from subprocess import Popen

clients_list = []
server = ''
path = os.path.dirname(__file__)
path_to_server = os.path.join(path, "server.py")
path_to_client = os.path.join(path, "client.py")

while True:
    action = input('Открыть сервер (o), запустить 4 клиента (s) / delete(x) / quit (q)')
    if action == 'q':
        break
    elif action == 'o':
        print("Запустили сервер")
        # server = Popen(f"open -n -a Terminal.app '{path_to_server}'", shell=True)
        server = Popen(
            f'osascript -e \'tell application "Terminal" to do'
            f' script "python3 {path_to_server}"\'', shell=True)
    elif action == 's':
        print("Запустили 4 клиента, 2 слушают, 2 пишут")
        for i in range(2):
            #     clients_list.append(Popen(f"open -n -a Terminal.app '{path_to_client}{i}' -m send", shell=True))
            #     clients_list.append(Popen(f"open -n -a Terminal.app '{path_to_client}{i}' -m listen", shell=True))
            clients_list.append(
                Popen(
                    f'osascript -e \'tell application "Terminal" to do'
                    f' script "python3 {path_to_client} -m listen"\'',
                    shell=True))
            clients_list.append(
                Popen(
                    f'osascript -e \'tell application "Terminal" to do'
                    f' script "python3 {path_to_client} -m send"\'',
                    shell=True))
