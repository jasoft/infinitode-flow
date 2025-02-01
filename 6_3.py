import pydirectinput as di
import pyautogui
from merge_platforms import activate_window, logging
import asyncio

cellsize = 90
boardcenter = (1920, 1010)


async def process_command(command_line: str):
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

    command_map = {
        "sleep": handle_sleep,
        "leftclick": handle_leftclick,
        "cellsize": handle_cellsize,
        "boardcenter": handle_boardcenter,
        "move": handle_move,
    }

    if command in command_map:
        await command_map[command](parts)
    else:
        await handle_keypress(parts)


async def handle_sleep(parts):
    try:
        sleep_time = float(parts[1])
        logging.info(f"🕒 暂停 {sleep_time} 秒...")
        for i in range(int(sleep_time), 0, -1):
            logging.info(f"倒计时: {i} 秒")
            await asyncio.sleep(1)
    except ValueError:
        logging.error("⚠️ 错误: sleep 后必须跟一个有效的数字！")


async def handle_leftclick(parts):
    di.leftClick(int(parts[1]), int(parts[2]))


async def handle_cellsize(parts):
    global cellsize
    cellsize = int(parts[1])


async def handle_boardcenter(parts):
    global boardcenter
    boardcenter = (int(parts[1]), int(parts[2]))


async def handle_move(parts):
    x = int(parts[1])
    y = int(parts[2])
    di.click(boardcenter[0] + x * cellsize, boardcenter[1] + y * cellsize)


async def handle_keypress(parts):
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
            await asyncio.sleep(0.05)
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
        element = pyautogui.locateOnScreen(
            f"elements/{image_file}.png", minSearchTime=3, confidence=0.9
        )
        if element:
            element_center = pyautogui.center(element)
            di.click(element_center.x, element_center.y)
            logging.info(f"点击 {image_file}")
            return True
    except Exception:
        logging.info(f"没有找到 {image_file}")
        return False


async def run(filename):
    with open(filename, "r") as file:
        for line in file:
            # while not pyautogui.getActiveWindow().title == "Infinitode 2":
            #     await asyncio.sleep(1)
            #     logging.info(
            #         f"等待 Infinitode 2 窗口激活... 当前窗口:{pyautogui.getActiveWindow().title}"
            #     )
            if line.startswith("#") or line.strip() == "":  # 忽略注释行和空行
                continue
            command = line.strip()
            await process_command(command)
            await asyncio.sleep(0)  # ���出控制权以便其他任务运行


async def main(script_file):
    run_task = None

    activate_window("infinitode 2")

    while True:
        # activate_window("infinitode 2")
        # 检查屏幕上是否存在指定的图像
        if click_element("restart"):
            if run_task:
                run_task.cancel()  # 取消之前的任务
                try:
                    await run_task
                except asyncio.CancelledError:
                    logging.info("任务已取消")

            # 购买技能
            di.leftClick(1104, 732, 1)
            di.leftClick(3142, 1537, 1)
            di.leftClick(3567, 1510, 2)

            # 开始游戏
            click_element("startgame")
            run_task = asyncio.create_task(run(script_file))

        if element_exists("musicplayer"):
            if run_task:
                run_task.cancel()  # 取消之前的任务
                try:
                    await run_task
                except asyncio.CancelledError:
                    logging.info("任务已取消")

            run_task = asyncio.create_task(run(script_file))
            logging.info("游戏已开始")

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main("level/6.3quickmove.txt"))
