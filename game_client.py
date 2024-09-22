import socket
import json
from colorama import Fore, Style, Cursor, just_fix_windows_console
import threading

just_fix_windows_console()
lock = threading.Lock()
with open("actions.json", "r", encoding="utf-8") as actions:
    data = json.load(actions)
    result = []
    for key, value in data.items():
        result.append(f"{key}: {value}")
    result = ", ".join(result)

class GameClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))

    def send_action(self, action):
        message = json.dumps({"action": action[0]})
        self.client_socket.send(message.encode("utf-8"))

    def receive_data(self):
        try:
            data = self.client_socket.recv(1024)
            if data:
                data = json.loads(data.decode("utf-8"))
                if data.get("status") == "game_over":
                    print(
                        f"{Fore.MAGENTA}游戏结束，宝马哥：{data['winner']}!{Style.RESET_ALL}"
                    )
                    self.close()
                    __import__("os")._exit(0)
                return data
        except (socket.error, json.decoder.JSONDecodeError):
            return self.receive_data()

    def render_status(self):
        while True:
            data = self.receive_data()
            if data:
                with lock:
                    print(Cursor.POS(0, 0))
                    print(f"{Fore.LIGHTGREEN_EX}状态：{data.get('status')}{Style.RESET_ALL}")
                    print(f"{Fore.LIGHTRED_EX}IU金钱：{data.get('iu_money')}{Style.RESET_ALL}")
                    print(
                        f"{Fore.LIGHTBLUE_EX}用户流量：{data.get('user_traffic')}{Style.RESET_ALL}"
                    )
                    print(f"{Fore.LIGHTYELLOW_EX}操作：{data.get('action')}{Style.RESET_ALL}")
                    if data.get("status") == "game_over":
                        print(
                            f"{Fore.MAGENTA}游戏结束，宝马哥：{data['winner']}!{Style.RESET_ALL}"
                        )
                        self.close()
                        break

    def interact_with_server(self):
        while True:
            with lock:
                print(f"{Cursor.POS(0, 7)}{result}")
                action = input("请输入你的操作：")
                if not action:
                    continue
                self.send_action(action)
                print('\033c')

    def close(self):
        return self.client_socket.close()


if __name__ == "__main__":
    client = GameClient(input("IP: "), int(input("端口: ")))
    render_thread = threading.Thread(target=client.render_status)
    interact_thread = threading.Thread(target=client.interact_with_server)
    threading.excepthook = lambda *args, **kwargs: __import__("os")._exit(int(0*(str(__import__("traceback").print_exc())+str(client.close()))+"-1"))
    print('\033c')
    render_thread.start()
    interact_thread.start()
    render_thread.join()
    interact_thread.join()
