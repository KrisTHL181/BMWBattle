import random
import socket
import json
from colorama import Fore, Style, Cursor, just_fix_windows_console
import threading
import time

just_fix_windows_console()


class _lock_like:
    status = False

    def toggle(self):
        self.status = False if self.status else True


print_lock = _lock_like()

with open("actions.json", "r", encoding="utf-8") as actions:
    data = json.load(actions)
    result = []
    for key, value in data.items():
        result.append(f"{key}: {value}")
    result = ", ".join(result)


class GameClient:
    game_started: bool = False

    def __init__(self, server_ip, server_port, job: str):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_ip, self.server_port))
        self.client_socket.send(json.dumps({"job": job}).encode("utf-8"))

    def send_action(self, action):
        message = json.dumps({"action": action[0]})
        for i in range(steps := 100):
            # 计算当前进度百分比
            progress = i / steps * 100

            # 打印进度条
            bar = "[" + "=" * i + "-" * (steps - i) + "]"
            print(f"\r{bar} {progress+random.uniform(0,1):.2f}%", end="")

            time.sleep(random.uniform(0, 0.1))
        try:
            self.client_socket.send(message.encode("utf-8"))
        except ConnectionResetError:
            return

    def receive_data(self):
        try:
            data = self.client_socket.recv(1024)
            if data:
                try:
                    data = json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    json_str = data.decode("utf-8")
                    json_objects = json_str.split("}{")
                    json_objects = ["{" + obj + "}" for obj in json_objects]
                    last_json = json_objects[1].rsplit("}", 1)[0]
                    data = json.loads(last_json)
                    # TCP/IP协议会粘包，于是只能采取此办法提取最后一个JSON :(

                if data.get("status") == "game_over":
                    print(
                        f"{Fore.MAGENTA}游戏结束，恭喜{data.get('winner', '未知用户 :(')}夺得宝马!!!{Style.RESET_ALL}"
                    )
                    self.close()
                    __import__("os")._exit(0)
                if data.get("status") == "game_start":
                    self.game_started = True
                    print(f"游戏开始! {'职业人数不平衡 :(' if data.get('job_unbalanced') else ''}")
                return data
        except OSError:
            return {"status": "socket_failed"}
        except json.JSONDecodeError:
            return {"status": "json_decode_failed"}

    def render_status(self):
        while True:
            if not self.game_started:
                print(f"游戏尚未开始, 请等待{round(time.time()%4)*'.'}    ", end="\r")
                continue
            if not print_lock.status and (data := self.receive_data()):
                print(Cursor.POS(0, 0))
                print(
                    f"{Fore.LIGHTGREEN_EX}状态：{data.get('status')}{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.LIGHTRED_EX}IU金钱：{data.get('iu_money')}{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.LIGHTBLUE_EX}用户流量：{data.get('user_traffic')}{Style.RESET_ALL}"
                )
                print(
                    f"{Fore.LIGHTYELLOW_EX}最后操作：{data.get('action')}{Style.RESET_ALL}"
                )
                print_lock.toggle()
            time.sleep(0.2)

    def interact_with_server(self):
        while True:
            print_lock.toggle()
            if not print_lock.status:
                print(f"{Cursor.POS(0, 7)}{result}\n请输入你的操作")
                print_lock.toggle()
                action = input()
                if not action or action not in result:
                    continue
                self.send_action(action)
                print("\033c")

    def close(self):
        return self.client_socket.close()


if __name__ == "__main__":
    client = GameClient(input("IP: "), int(input("端口: ")), input("职业(kdp/iu): "))
    render_thread = threading.Thread(target=client.render_status)
    interact_thread = threading.Thread(target=client.interact_with_server)
    threading.excepthook = lambda *args, **kwargs: __import__("os")._exit(
        int(0 * (str(__import__("traceback").print_exc()) + str(client.close())) + "-1")
    )
    print("\033c")
    render_thread.start()
    interact_thread.start()
    render_thread.join()
    interact_thread.join()
