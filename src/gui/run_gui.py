"""
SteelBid Pro 桌面与本地 Web 交互式工作台启动器 (GUI Runner)

使用方法:
    uv run python -m src.gui.run_gui
    python -m src.gui.run_gui --port 8765

启动后将自动唤起系统默认浏览器打开算量工作台，支持平铺、WBS层级折叠、三阶段成本穿透、清单量差对照四大灵活视图
"""

import argparse
import http.server
import os
from pathlib import Path
import socketserver
import sys
import threading
import time
import webbrowser


WORKBENCH_DIR = Path(__file__).parent / "workbench"


class QuietHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    """静默 HTTP 静态资源请求处理器"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WORKBENCH_DIR), **kwargs)

    def log_message(self, format, *args):
        # 简化日志输出
        if "404" in format % args:
            sys.stderr.write(f"[GUI HTTP 404] {format % args}\n")


def launch_server(port: int = 8765, open_browser: bool = True):
    """启动本地 GUI 服务并在独立线程中唤起浏览器"""
    if not WORKBENCH_DIR.exists() or not (WORKBENCH_DIR / "app.html").exists():
        raise FileNotFoundError(f"工作台文件不存在: {WORKBENCH_DIR / 'app.html'}")

    handler = QuietHttpRequestHandler
    url = f"http://localhost:{port}/app.html"

    print("=" * 70)
    print("  SteelBid Pro · 钢结构商务估价与全生命周期成本管控系统")
    print(f"  工作台本地服务已就绪: {url}")
    print("  包含全量 81 个湛江北站真实构件、4大灵活视图、7大业务Dialog")
    print("=" * 70)

    if open_browser:
        def _open():
            time.sleep(0.5)
            print(f"正在唤起默认浏览器访问: {url} ...")
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    with socketserver.TCPServer(("", port), handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n正在停止 GUI 服务...")
            httpd.server_close()


def main():
    parser = argparse.ArgumentParser(description="SteelBid Pro 本地 GUI 工作台启动器")
    parser.add_argument("--port", type=int, default=8765, help="本地服务端口 (默认 8765)")
    parser.add_argument("--no-browser", action="store_true", help="不自动拉起浏览器")
    args = parser.parse_args()

    launch_server(port=args.port, open_browser=not args.no_browser)


if __name__ == "__main__":
    main()
