import json
import matplotlib.pyplot as plt


# 读取 GameHistory.txt 文件
def load_history(filename):
    with open(filename, "r", encoding="utf-8") as file:
        history = json.load(file)
    return history


# 绘制图像
def plot_history(history):
    iu_money = history["iu_money"]
    user_traffic = history["user_traffic"]

    plt.figure(figsize=(12, 6))

    plt.plot(iu_money, label="IU Money", color="blue", alpha=0.7)
    plt.plot(user_traffic, label="User Traffic", color="red", alpha=0.7)

    plt.title("IU Money & User Traffic Over Time")
    plt.xlabel("Time Step")
    plt.ylabel("Value")
    plt.legend()

    plt.show()


# 主函数
def main():
    filename = "GameHistory.txt"
    history = load_history(filename)
    plot_history(history)


if __name__ == "__main__":
    main()
