import pydirectinput as di
from common import (
    logging,
    WindowController,
)
import asyncio
from tqdm.asyncio import tqdm

BUY_SKILL = (454, 349)
BUY_SKILL_YES = (1474, 724)
ALL_SKILL_PURCHASED_OK = (1738, 701)
# 棋盘参数
cellsize = 0
boardcenter = (0, 0)


game = WindowController("Infinitode 2")


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
        for i in tqdm(range(int(sleep_time), 0, -1)):
            await asyncio.sleep(1)
    except ValueError:
        logging.error("⚠️ 错误: sleep 后必须跟一个有效的数字！")


async def handle_leftclick(parts):
    game.click(int(parts[1]), int(parts[2]))


async def handle_cellsize(parts):
    global cellsize
    cellsize = int(parts[1])


async def handle_boardcenter(parts):
    global boardcenter
    boardcenter = (int(parts[1]), int(parts[2]))


async def handle_move(parts):
    x = int(parts[1])
    y = int(parts[2])
    game.click(boardcenter[0] + x * cellsize, boardcenter[1] + y * cellsize)


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


async def run(filename):
    with open(filename, "r", encoding="utf-8") as file:
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
            await asyncio.sleep(0)  # 出控制权以便其他任务运行


async def main(script_file):
    run_task = None

    def cancel_task():
        if run_task:
            run_task.cancel()
            try:
                run_task.result()
            except asyncio.CancelledError:
                logging.info("任务已取消")

    game.activate()

    while True:
        # activate_window("infinitode 2")
        # 检查屏幕上是否存在指定的图像
        if await game.click_element("restart", waitUntilSuccess=False):
            logging.info("游戏结束，准备重新开始")
            cancel_task()

            # 购买技能
            game.click(*BUY_SKILL)
            game.click(*BUY_SKILL_YES)
            # 如果所有技能都买了, 会弹出一个对话框，点击确定
            if await game.element_exists("all_abi_purchased"):
                game.click(*ALL_SKILL_PURCHASED_OK)

            # 开始游戏
            await game.click_element("startgame")
            await asyncio.sleep(2)
            run_task = asyncio.create_task(run(script_file))

        if await game.click_element("startgame", waitUntilSuccess=False):
            cancel_task()
            await asyncio.sleep(2)
            run_task = asyncio.create_task(run(script_file))
            logging.info("游戏已开始")

        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main("level/6.3.it2"))
