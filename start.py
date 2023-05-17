import os
from subprocess import Popen

clients_list = []
server = ''
path = os.path.dirname(__file__)
path_to_server = os.path.join(path, "server.py")
path_to_client = os.path.join(path, "client.py")

while True:
    action = input('открыть сервер (o), запустить клиентcкие приложения (s), выйти (q)')
    if action == 'q':
        break
    elif action == 'o':
        print("Запустили сервер")
        server = Popen(
            f'osascript -e \'tell application "Terminal" to do'
            f' script "python3 {path_to_server}"\'', shell=True)
    elif action == 's':
        x = int(input("Какое количество клиентских приложений вы хотите запустить?"))
        for i in range(x):
            clients_list.append(
                Popen(
                    f'osascript -e \'tell application "Terminal" to do'
                    f' script "python3 {path_to_client} -n client{i + 1}"\'',
                    shell=True))
        print(f"Запустили {x} клиентских приложений")
