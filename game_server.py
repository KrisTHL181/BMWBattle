import random
import select
import socket
import json
import time
from game_logger import info, log


class GameServer:
    with open("actions.json", "r", encoding="utf-8") as actions:
        ACTION_MAP = json.load(actions)

    def __init__(
        self,
        gamestart_players: int = 1,  # 当玩家数量大于此值后游戏开始
        iu_money: int = 3000,  # 初始IU金钱
        user_traffic: int = 500,  # 初始用户流量
        user_to_money_percent: float = 0.01,  # 用户流量转成金钱的系数
        reduce_utility: float = 0.03,  # DDoS和误杀的效用系数
        reduce_bias: float = 0.01,  # 降低用户流量的随机加减范围
        ddos_reduce_money: int = 20,  # IU被DDoS攻击减少的金钱
        fix_utility: float = 0.01,  # 修复主防所带来的用户系数
        fix_bias: float = 0.05,  # 修复主防所带来的用户流量随机加减范围
        fix_used_money: int = 50,  # 修复主防消耗的金钱
        fix_add_traffic: int = 150,  # 修复主防增加的用户流量
        buy_traffic_money: int = 150,  # 购买用户流量需要的金额
        buy_traffic_add: int = 500,  # 购买的用户流量数额
        overspeech_attack_reduce: int = 200,  # 舆论攻击降低的流量
        overspeech_attack_bias: float = 0.05,  # 舆论攻击流量降低随机偏差
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
        self.buy_traffic_money = buy_traffic_money
        self.buy_traffic_add = buy_traffic_add
        self.overspeech_attack_reduce = overspeech_attack_reduce
        self.overspeech_attack_bias = overspeech_attack_bias
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
                break
            else:
                info(f"当前玩家数量：{len(self.sockets)}，等待其他玩家加入...")

        while True:
            self.update()

    def test_game_loop(self):
        self.send = lambda *args, **kwargs: None
        globals()["random"].__getattribute__ = (
            __import__("secrets").SystemRandom().__getattribute__
        )
        self.get_action = lambda: random.choice(list(self.ACTION_MAP))
        while True:
            self.update()

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
            utility = round(
                random.uniform(self.reduce_bias, self.reduce_bias * 1.5) / 3, 3
            )
            self.reduce_utility -= utility
            info(f"IU使用神拳，跳过一回合误杀，降低DDoS效用{utility}")
            self.skip_false_alarm = True
        elif action == "写端增强":
            utility = round(
                random.uniform(self.reduce_bias, self.reduce_bias * 1.5) / 2, 3
            )
            self.reduce_utility += utility
            info(f"使用写端增强，DDoS效用增加{utility}")
        elif action == "购买流量":
            self.iu_money -= self.buy_traffic_money
            self.user_traffic += self.buy_traffic_add
            info(f"IU利用{self.buy_traffic_money}元购买了{self.buy_traffic_add}流量")
        elif action == "舆论攻击":
            bias = random.uniform(
                -self.overspeech_attack_bias, self.overspeech_attack_bias
            )
            traffic = round((1 + bias) * self.overspeech_attack_reduce)
            self.user_traffic -= traffic
            info(f"使用舆论攻击让IU用户流量降低{traffic}")
        else:
            info(f"未知操作: {action}")
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
                try:
                    data = sock.recv(1024)
                except ConnectionResetError:
                    __import__("os")._exit(-1)
                if data:
                    return json.loads(data.decode("utf-8"))
            except socket.error:
                return self.receive_data()

    def get_action(self) -> str:
        data = self.receive_data()
        return data["action"]

    def send(self, message: str) -> None:
        for sock in self.sockets:
            sock.send(message.encode("utf-8"))

    def close(self) -> None:
        for sock in self.sockets:
            sock.close()

    def wait_close(self) -> None:
        for sock in self.sockets:
            if sock._closed:
                self.sockets.remove(sock)
                sock.close()
        __import__("os")._exit(0)

    def check_game_end(self) -> None:
        info(f"当前IU金钱: {self.iu_money}，当前用户流量: {self.user_traffic}")
        if (
            self.user_traffic < self.iu_game_stop_traffic
            or self.iu_money < self.iu_game_stop_money
        ):
            log("Kdp夺得宝马!!!")
            status = {
                "status": "game_over",
                "winner": "Kdp",
                "iu_money": self.iu_money,
                "user_traffic": self.user_traffic,
            }
            self.send(json.dumps(status))
            self.save_history()
            time.sleep(8)
            for sock in self.sockets:
                sock.shutdown(socket.SHUT_WR)
            self.wait_close()
        elif (
            self.user_traffic > self.kdp_game_stop_traffic
            or self.iu_money > self.kdp_game_stop_money
        ):
            log("IU夺得宝马!!!")
            status = {
                "status": "game_over",
                "winner": "IU",
                "iu_money": self.iu_money,
                "user_traffic": self.user_traffic,
            }
            self.send(json.dumps(status))
            self.save_history()
            time.sleep(8)
            for sock in self.sockets:
                sock.shutdown(socket.SHUT_WR)
            self.wait_close()

    def save_history(self, filename: str = "GameHistory.txt"):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(self.history, file, ensure_ascii=False, indent=2)
        info(f"历史记录已保存到 {filename}")


if __name__ == "__main__":
    game_server = GameServer()
    game_server.game_loop()
