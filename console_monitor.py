# language: python
import time
import threading
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

console = Console()


class ConsoleMonitor:
    def __init__(self, max_status=5, max_progress=600):
        self.max_status = max_status
        self.status_history = []
        self.max_progress = max_progress
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.percentage:>3.0f}%"),
            console=console,
            transient=True,
        )
        # 添加一个进度条任务，总值为 max_progress
        self.task = self.progress.add_task(
            "等待中", total=self.max_progress, completed=0
        )
        self._lock = threading.Lock()
        self._running = False

    def update_status(self, status_text, color="white"):
        with self._lock:
            self.status_history.append((status_text, color))
            if len(self.status_history) > self.max_status:
                self.status_history.pop(0)

    def set_progress(self, total, completed):
        with self._lock:
            if completed < 0:
                completed = 0
            elif completed > self.max_progress:
                completed = self.max_progress
            self.progress.update(self.task, total=total, completed=completed)

    def render(self):
        with self._lock:
            # 拼�� status_history 为多行文本
            status_lines = "\n".join(
                f"[{color}]{text}[/{color}]" for text, color in self.status_history
            )
        status_panel = Panel(
            status_lines if status_lines else "无状态信息",
            title="Bot 当前状态",
            border_style="blue",
        )
        return Group(status_panel, self.progress)

    def start(self, refresh_interval=0.1):
        self._running = True
        # Live 运行在当前线程，会阻塞，因此使用后台线程启动
        thread = threading.Thread(
            target=self._live_loop, args=(refresh_interval,), daemon=True
        )
        thread.start()

    def _live_loop(self, refresh_interval):
        with Live(self.render(), console=console, auto_refresh=False) as live:
            while self._running:
                live.update(self.render())
                live.refresh()
                time.sleep(refresh_interval)

    def stop(self):
        self._running = False


if __name__ == "__main__":
    monitor = ConsoleMonitor(max_status=5, max_progress=200)
    monitor.start(refresh_interval=0.1)

    # 模拟状态和进度更新
    import random

    colors = ["cyan", "yellow", "green", "red", "magenta"]
    progress_value = 0

    try:
        while True:
            # 每隔 0.5 秒更新状态
            monitor.update_status(
                f"当前状态更新：{random.randint(0, 100)}", color=random.choice(colors)
            )
            progress_value += random.randint(1, 5)
            if progress_value > 200:
                progress_value = 0
            monitor.set_progress(progress_value)
            time.sleep(0.5)
    except KeyboardInterrupt:
        monitor.stop()
        console.print("ConsoleMonitor 已停止")
