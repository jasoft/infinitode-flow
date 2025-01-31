import pydirectinput as di
import pyautogui
from merge_platforms import activate_window, logging
import time
import tkinter as tk


cellsize = 90
boardcenter = (1920, 1010)


def create_log_window():
    window = tk.Tk()
    window.title("Bot Log")
    window.geometry("300x200")
    window.attributes("-topmost", True)  # 将窗口置顶

    log_text = tk.Text(window, state="disabled", wrap="word")
    log_text.pack(expand=True, fill="both")

    return window, log_text


def update_log(log_text, message):
    try:
        log_text.config(state="normal")
        log_text.insert(tk.END, message + "\n")
        log_text.config(state="disabled")
        log_text.see(tk.END)

    except Exception as e:
        logging.error(f"⚠️ 错误: {e}")


def process_command(command_line: str):
    """
    解析按键字符串并执行按键输入：
    - "ctrl-r"、"alt-f4" 形式的组合键
    - "a"、"enter" 形式的单键ee
    - "sleep 3" 让程序暂停 3 秒
    - repeat 参数指定按键的重复次数
    - "cellsize 90" 设置单元格大小
    - "boardcenter 1920 1010" 设置棋盘中心
    - "move 1 2" 移动到指定单元格

    :param command: 按键字符串，例如 "ctrl-r", "alt-f4", "a", "enter", "sleep 3"
    :param repeat: 按键重复次数（仅对按键有效），默认为 1
    """
    parts = command_line.split()
    command = parts[0]

    if command.startswith("#"):  # 忽略注释行
        return
    logging.info(f'执行按键: "{command_line}"')
    update_log(log_text, f'执行按键: "{command_line}"')  # 更新日志窗口

    command_map = {
        "sleep": handle_sleep,
        "leftclick": handle_leftclick,
        "cellsize": handle_cellsize,
        "boardcenter": handle_boardcenter,
        "move": handle_move,
    }

    if command in command_map:
        command_map[command](parts)
    else:
        handle_keypress(parts)


def handle_sleep(parts):
    try:
        sleep_time = float(parts[1])
        logging.info(f"🕒 暂停 {sleep_time} 秒...")
        update_log(log_text, f"🕒 暂停 {sleep_time} 秒...")  # 更新日志窗口
        for i in range(int(sleep_time), 0, -1):
            update_log(log_text, f"倒计时: {i} 秒")
            time.sleep(1)
    except ValueError:
        logging.error("⚠️ 错误: sleep 后必须跟一个有效的数字！")


def handle_leftclick(parts):
    di.leftClick(int(parts[1]), int(parts[2]))


def handle_cellsize(parts):
    global cellsize
    cellsize = int(parts[1])


def handle_boardcenter(parts):
    global boardcenter
    boardcenter = (int(parts[1]), int(parts[2]))


def handle_move(parts):
    x = int(parts[1])
    y = int(parts[2])
    di.click(boardcenter[0] + x * cellsize, boardcenter[1] + y * cellsize)


def handle_keypress(parts):
    command = parts[0]
    repeat = int(parts[1]) if len(parts) > 1 else 1
    if "-" in command:  # 处理组合键
        keys = command.split("-")
        modifier_keys = [key for key in keys if key in ["ctrl", "alt", "shift"]]
        main_key = next((key for key in keys if key not in modifier_keys), None)

        if not main_key:
            logging.info("⚠️ 错误: 组合键中必须包含一个主键！")
            return

        for _ in range(repeat):
            for mod in modifier_keys:
                di.keyDown(mod)  # 按住修饰键

            di.press(main_key)  # 按下主键

            for mod in modifier_keys:
                di.keyUp(mod)  # 释放修饰键
    else:
        for _ in range(repeat):  # 处理单个按键
            di.keyDown(command)
            time.sleep(0.05)
            di.keyUp(command)


def element_exists(element):
    try:
        pyautogui.locateOnScreen(f"elements/{element}.png")
        return True
    except Exception:
        return False


def click_element(image_file):
    try:
        logging.info(f"查找 {image_file}")
        element = pyautogui.locateOnScreen(f"elements/{image_file}.png")
        if element:
            element_center = pyautogui.center(element)
            di.click(element_center.x, element_center.y)
            logging.info(f"点击 {image_file}")
            update_log(log_text, f"点击 {image_file}")  # 更新日志窗口
            return True
    except Exception:
        logging.info(f"没有找到 {image_file}")
        update_log(log_text, f"没有找到 {image_file}")  # 更新日志窗口
        return False


def run(filename):
    with open(filename, "r") as file:
        for line in file:
            if line.startswith("#") or line.strip() == "":  # 忽略注释行和空行
                continue
            command = line.strip()

            process_command(command)

    # 等待一段时间以确保按键操作完成


def update_log_window(window):
    window.update_idletasks()
    window.after(100, update_log_window, window)


def main(script_file):
    global log_text
    window, log_text = create_log_window()
    window.after(100, update_log_window, window)
    while True:
        activate_window("infinitode 2")
        # 检查屏幕上是否存在指定的图像
        if click_element("restart"):
            # 购买技能
            di.leftClick(1104, 732, duration=0.5)
            time.sleep(1)
            di.leftClick(3142, 1537, duration=0.5)
            time.sleep(1)
            di.leftClick(3567, 1510, duration=0.5)
            time.sleep(2)

            click_element("startgame")
            run(script_file)

        if element_exists("musicplayer"):
            run(script_file)
        time.sleep(5)


if __name__ == "__main__":
    main("level/6.3quickmove.txt")
