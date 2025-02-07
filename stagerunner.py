import pydirectinput as di
from common import (
    logging,
    GameBot,
)
import asyncio
from console_monitor import ConsoleMonitor
from transitions.extensions.asyncio import AsyncMachine as Machine
import time

BUY_SKILL = (454, 349)
BUY_SKILL_YES = (1474, 724)
ALL_SKILL_PURCHASED_OK = (1738, 701)
# 棋盘参数
cellsize = 0
boardcenter = (0, 0)


game = GameBot("Infinitode 2", elements_path="elements/1080")
machine = None

status_monitor = ConsoleMonitor(max_status=20)
status_monitor.start(refresh_interval=0.1)


class GameStateMachine:
    states = [
        "MAIN_MENU",
        "RESTART_SCREEN",
        "START_GAME_SCREEN",
        "PREPARE_TOWERS_SCREEN",
        "GAME_RUNNING_SCREEN",
    ]
    run_task = None

    def __init__(self, script_file):
        # 初始化状态机
        self.machine = Machine(
            model=self,
            states=self.states,
            initial="START_GAME_SCREEN",  # 初始状态
            auto_transitions=False,  # 关闭自动状态转换
        )

        # 定义状态转换规则（从 A 状态可跳转到 B 状态）
        self.machine.add_transition(
            "restart", "*", "RESTART_SCREEN", after="on_enter_restart"
        )
        self.machine.add_transition(
            "startgame", "*", "START_GAME_SCREEN", after="on_enter_startgame"
        )
        self.machine.add_transition(
            "prepare_towers",
            "*",
            "PREPARE_TOWERS_SCREEN",
            conditions=["is_not_preparing_towers"],
            after="on_enter_prepare_towers",
        )
        self.machine.add_transition(
            "quitbot", "*", "MAIN_MENU", after="on_enter_quitbot"
        )
        self.machine.add_transition(
            "run_script_finished",
            "*",
            "GAME_RUNNING_SCREEN",
            after="on_enter_run_script_finished",
        )

        self.script_file = script_file
        self._is_game_running = False

    def is_not_preparing_towers(self):
        return not self._is_game_running

    def on_enter_run_script_finished(self):
        self._is_game_running = False

    async def on_enter_restart(self):
        logging.info("游戏结束，准备重新开始")
        status_monitor.update_status("游戏结束，准备重新开始", color="yellow")
        self.cancel_botting_task()
        await game.click_element("restart")

    async def on_enter_startgame(self):
        self.cancel_botting_task()
        await asyncio.sleep(2)
        await game.click(*BUY_SKILL)
        await game.click(*BUY_SKILL_YES)
        # 如果所有技能都买了, 会弹出一个对话框，点击确定
        if await game.element_exists("all_abi_purchased"):
            await game.click(*ALL_SKILL_PURCHASED_OK)
        await game.click_element("startgame")

    async def on_enter_prepare_towers(self):
        self.cancel_botting_task()
        logging.info("准备防御塔")
        status_monitor.update_status("准备防御塔", color="yellow")
        # 开始游戏
        self._is_game_running = True

        self.run_task = asyncio.create_task(run(self.script_file))
        logging.info("游戏已开始")

    async def on_enter_quitbot(self):
        self.cancel_botting_task()
        logging.info("退出bot")
        status_monitor.update_status("退出bot", color="yellow")

    def cancel_botting_task(self):
        if self.run_task:
            self.run_task.cancel()
            self._is_game_running = False
            try:
                self.run_task.result()
            except (asyncio.CancelledError, asyncio.InvalidStateError) as e:
                logging.info(f"任务取消或无效状态错误: {e}")
                status_monitor.update_status("当前任务已取消", color="yellow")


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
        status_monitor.update_status(f"{command_line[1:].lstrip()}", color="green")
        return
    status_monitor.update_status(f"执行命令: {command_line}", color="white")
    logging.info(f'执行命令: "{command_line}"')

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
        status_monitor.set_countdown_time(sleep_time)
        for i in range(int(sleep_time), 0, -1):
            await asyncio.sleep(1)

    except ValueError:
        logging.error("⚠️ 错误: sleep 后必须跟一个有效的数字！")


async def handle_leftclick(parts):
    await game.click(int(parts[1]), int(parts[2]))


async def handle_cellsize(parts):
    global cellsize
    cellsize = int(parts[1])


async def handle_boardcenter(parts):
    global boardcenter
    boardcenter = (int(parts[1]), int(parts[2]))


async def handle_move(parts):
    x = int(parts[1])
    y = int(parts[2])
    await game.click(boardcenter[0] + x * cellsize, boardcenter[1] + y * cellsize)


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
    logging.info(f"运行脚本: {filename}")
    # start_time = time.time()

    # async def update_runtime():
    #     while True:
    #         elapsed_time = int(time.time() - start_time)
    #         status_monitor.update_info("脚本运行时间", f"{elapsed_time} 秒")
    #         await asyncio.sleep(1)

    # task = asyncio.create_task(update_runtime())

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip() == "":  # 忽略注释行和空行
                continue
            command = line.strip()

            await process_command(command)
            await asyncio.sleep(0)  # 出控制权以便其他任务运行
    await machine.run_script_finished()
    # task.cancel()


async def find_elements(elements):
    """
    并发查找多个元素是否存在, 返回一个字典
    """
    start_time = time.time()
    elements_found = await asyncio.gather(
        *[game.element_exists(element) for element in elements]
    )
    result = dict(zip(elements, elements_found))
    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.debug(f"查找游戏元素耗时: {elapsed_time:.2f} 秒")

    return result


async def main(script_file):
    game_elements = ["restart", "startgame", "prepare_towers"]
    global machine
    machine = GameStateMachine(script_file)

    try:
        while True:
            game.resize(1920, 1080)
            game.activate()

            elements_found = await find_elements(game_elements)

            for method_name, exists in elements_found.items():
                if exists:
                    logging.info(f"执行 machine.{method_name} 方法...")
                    await machine.trigger(method_name)

            await asyncio.sleep(5)
    except KeyboardInterrupt:
        await machine.quitbot()
        status_monitor.update_status("ConsoleMonitor 已停止")
        status_monitor.stop()


if __name__ == "__main__":
    asyncio.run(main("level/6.3.it2"))
