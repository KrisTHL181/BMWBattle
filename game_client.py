import socket
import json
from colorama import Fore, Style, Cursor, just_fix_windows_console
import threading

just_fix_windows_console()


class GameClient:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))
        self.client_socket.setblocking(False)

    def send_action(self, action):
        message = json.dumps({"action": action})
        self.client_socket.send(message.encode("utf-8"))

    def receive_data(self):
        try:
            data = self.client_socket.recv(1024)
            if data:
                return json.loads(data.decode("utf-8"))
        except socket.error:
            pass

    def close(self):
        self.client_socket.close()

    def render_status(self):
        while True:
            data = self.receive_data()
            if data:
                print(Cursor.POS(0, 0))
                print(f"{Fore.GREEN}状态：{data.get('status')}{Style.RESET_ALL}")
                print(f"{Fore.RED}IU金钱：{data.get('iu_money')}{Style.RESET_ALL}")
                print(
                    f"{Fore.BLUE}用户流量：{data.get('user_traffic')}{Style.RESET_ALL}"
                )
                print(f"{Fore.YELLOW}操作：{data.get('action')}{Style.RESET_ALL}")
                if data.get("status") == "game_over":
                    print(
                        f"{Fore.MAGENTA}游戏结束，宝马哥：{data['winner']}!{Style.RESET_ALL}"
                    )
                    self.close()
                    break

    def interact_with_server(self):
        while True:
            print("0: DDoS, 1: 修复主动防御, 2: 误杀IU, 3: 进行神拳")
            action = input(f"{Cursor.POS(0, 7)}请输入你的操作：")
            self.send_action(action)


if __name__ == "__main__":
    threading.excepthook = lambda: __import__("os")._exit(-1)
    client = GameClient(input("IP: "), int(input("端口: ")))
    render_thread = threading.Thread(target=client.render_status)
    interact_thread = threading.Thread(target=client.interact_with_server)
    render_thread.start()
    interact_thread.start()
    render_thread.join()
    interact_thread.join()
