import random
import select
import socket
import json
from game_logger import info


class GameServer:
    ACTION_MAP = {"0": "DDoS", "1": "修复主动防御", "2": "误杀", "3": "神拳"}

    def __init__(
        self,
        gamestart_players: int = 4,  # 当玩家数量大于此值后游戏开始
        iu_money: int = 3000,  # 初始IU金钱
        user_traffic: int = 350,  # 初始用户流量
        user_to_money_percent: float = 0.02,  # 用户流量转成金钱的系数
        reduce_utility: float = 0.05,  # DDoS和误杀的效用系数
        reduce_bias: float = 0.01,  # 降低用户流量的随机加减范围
        ddos_reduce_money: int = 20,  # IU被DDoS攻击减少的金钱
        fix_utility: float = 0.005,  # 修复主防所带来的用户系数
        fix_bias: float = 0.05,  # 修复主防所带来的用户流量随机加减范围
        fix_used_money: int = 20,  # 修复主防消耗的金钱
        fix_add_traffic: int = 50,  # 修复主防增加的用户流量
        iu_game_stop_traffic: int = 0,  # 当用户流量小于此值后Kdp胜利
        iu_game_stop_money: int = 0,  # 当IU金钱小于此值后Kdp胜利
        kdp_game_stop_traffic: int = 10000,  # 当用户流量大于此值后IU胜利
        kdp_game_stop_money: int = 15000,  # 当IU金钱大于此值后IU胜利
    ):
        self.gamestart_players = gamestart_players
        self.iu_money = iu_money
        self.user_traffic = user_traffic
        self.user_to_money_percent = user_to_money_percent
        self.reduce_utility = reduce_utility
        self.reduce_bias = reduce_bias
        self.ddos_reduce_money = ddos_reduce_money
        self.fix_utility = fix_utility
        self.fix_bias = fix_bias
        self.fix_used_money = fix_used_money
        self.fix_add_traffic = fix_add_traffic
        self.iu_game_stop_traffic = iu_game_stop_traffic
        self.iu_game_stop_money = iu_game_stop_money
        self.kdp_game_stop_traffic = kdp_game_stop_traffic
        self.kdp_game_stop_money = kdp_game_stop_money
        self.history = {"iu_money": [], "user_traffic": []}
        self.skip_false_alarm = False
        self.sockets = []

    def game_loop(self) -> None:
        port = random.randint(5000, 60000)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("0.0.0.0", port))
        server_socket.listen(8)
        info(f"服务器已启动(端口:{port})，等待客户端连接...")

        while True:
            client_socket, addr = server_socket.accept()
            info(f"客户端 {addr} 已连接")
            self.sockets.append(client_socket)
            if len(self.sockets) >= self.gamestart_players:
                info(f"当前玩家数量：{len(self.sockets)}，游戏开始")
                self.send(json.dumps({"status": "game_start"}))
            else:
                info(f"当前玩家数量：{len(self.sockets)}，等待其他玩家加入...")

    def update(self) -> None:
        self.check_game_end()
        money_add = round(self.user_traffic * self.user_to_money_percent)
        self.iu_money += money_add
        info(f"IU金钱增加{money_add}")
        action = self.ACTION_MAP.get(self.get_action(), "未知操作")
        if action == "DDoS":
            bias = random.uniform(-self.reduce_bias, self.reduce_bias)
            traffic = round((1 + bias) * self.reduce_utility * self.user_traffic)
            self.iu_money -= self.ddos_reduce_money
            self.user_traffic -= traffic
            info(
                f"IU被DDoS攻击，金钱减少{self.ddos_reduce_money}，用户流量减少{traffic}"
            )
        elif action == "修复主动防御":
            if self.iu_money >= self.fix_used_money:
                bias = random.uniform(-self.fix_bias, self.fix_bias)
                traffic = round((1 + bias) * self.fix_utility) + self.fix_add_traffic
                self.iu_money -= self.fix_used_money
                self.user_traffic += traffic
                info(
                    f"IU修复主动防御，金钱减少{self.fix_used_money}，用户流量增加{traffic}"
                )
            else:
                info("IU金钱不足，无法修复主动防御")
        elif action == "误杀":
            if self.skip_false_alarm:
                return
            bias = random.uniform(-self.reduce_bias, self.reduce_bias)
            traffic = round((1 + bias) * self.fix_utility * self.user_traffic)
            self.user_traffic -= traffic
            info(f"IU被误杀，用户流量减少{traffic}")
        elif action == "神拳":
            bias = random.uniform(-self.reduce_bias, self.reduce_bias)
            traffic = round((1 + bias) * self.reduce_utility * self.user_traffic)
            self.user_traffic -= traffic
            info(f"IU使用神拳，用户流量降低{traffic}，跳过一回合误杀")
            self.skip_false_alarm = True
        else:
            info("未知操作")
        self.history["iu_money"].append(self.iu_money)
        self.history["user_traffic"].append(self.user_traffic)
        log = {
            "status": "game_running",
            "iu_money": self.iu_money,
            "user_traffic": self.user_traffic,
            "action": action,
        }
        self.send(json.dumps(log))

    def receive_data(self):
        readable, _, _ = select.select(self.sockets, [], [])
        for sock in readable:
            try:
                data = sock.recv(1024)
                if data:
                    return json.loads(data.decode("utf-8"))
            except socket.error:
                pass

    def get_action(self) -> str:
        while True:
            data = self.receive_data()
            try:
                json.loads(data)
                return data
            except ValueError:
                continue

    def send(self, message: str) -> None:
        for sock in self.sockets:
            sock.send(message.encode("utf-8"))

    def close(self) -> None:
        for sock in self.sockets:
            sock.close()

    def check_game_end(self) -> None:
        info(f"当前IU金钱: {self.iu_money}，当前用户流量: {self.user_traffic}")
        if (
            self.user_traffic < self.iu_game_stop_traffic
            or self.iu_money < self.iu_game_stop_money
        ):
            info("Kdp夺得宝马!!!")
            status = {
                "status": "game_over",
                "winner": "Kdp",
                "iu_money": self.iu_money,
                "user_traffic": self.user_traffic,
            }
            self.send(status)
            self.save_history()
            __import__("os")._exit(0)
        elif (
            self.user_traffic > self.kdp_game_stop_traffic
            or self.iu_money > self.kdp_game_stop_money
        ):
            info("IU夺得宝马!!!")
            status = {
                "status": "game_over",
                "winner": "iu",
                "iu_money": self.iu_money,
                "user_traffic": self.user_traffic,
            }
            self.send(status)
            self.save_history()
            __import__("os")._exit(0)

    def save_history(self, filename: str = "GameHistory.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.history, file, ensure_ascii=False, indent=2)
        info(f"历史记录已保存到 {filename}")


if __name__ == "__main__":
    game_server = GameServer()
    game_server.game_loop()
