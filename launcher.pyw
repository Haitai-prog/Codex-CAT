import sys, os, time, threading, webbrowser, subprocess, socket
from pathlib import Path
import tkinter as tk
from tkinter import ttk

BASE_DIR = Path(__file__).parent
BACKEND_DIR = BASE_DIR / "backend"
HOST = "127.0.0.1"
PORT = 8080


def is_port_in_use(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Codex CAT")
        self.root.geometry("320x210")
        self.root.resizable(False, False)

        main_frame = ttk.Frame(root, padding=20)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Codex CAT",
                  font=("Segoe UI", 16, "bold")).pack(pady=(0, 4))
        ttk.Label(main_frame, text="AI-Powered Translation Tool",
                  font=("Segoe UI", 9)).pack()

        self.status_var = tk.StringVar(value="Starting...")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                                     font=("Segoe UI", 10), foreground="gray")
        self.status_bar.pack(pady=(12, 8))

        self.progress = ttk.Progressbar(main_frame, mode="indeterminate", length=200)
        self.progress.pack(pady=(0, 12))
        self.progress.start()

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack()

        self.open_btn = ttk.Button(btn_frame, text="Open Browser",
                                    command=self.open_browser, state="disabled")
        self.open_btn.pack(side="left", padx=4)

        self.quit_btn = ttk.Button(btn_frame, text="Quit",
                                    command=self.quit_app)
        self.quit_btn.pack(side="left", padx=4)

        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)

        threading.Thread(target=self._startup, daemon=True).start()

    def _startup(self):
        if is_port_in_use(HOST, PORT):
            self.root.after(0, self._on_ready)
            return
        start_server()
        for _ in range(30):
            time.sleep(0.3)
            if is_port_in_use(HOST, PORT):
                self.root.after(0, self._on_ready)
                return
        self.root.after(0, self._on_failed)

    def _on_ready(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("Running - http://localhost:8080")
        self.status_bar.configure(foreground="green")
        self.open_btn.configure(state="normal")
        webbrowser.open("http://localhost:8080")

    def _on_failed(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("Failed to start server")
        self.status_bar.configure(foreground="red")
        self.open_btn.configure(state="normal")

    def open_browser(self):
        webbrowser.open("http://localhost:8080")

    def quit_app(self):
        kill_existing()
        self.root.destroy()


server_process = None


def kill_existing():
    global server_process
    if server_process:
        try:
            server_process.terminate()
            server_process.wait(timeout=3)
        except Exception:
            try:
                server_process.kill()
            except Exception:
                pass


def start_server():
    global server_process
    env = os.environ.copy()
    env["DEEPSEEK_API_KEY"] = "YOUR_DEEPSEEK_API_KEY"
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app",
         "--host", HOST, "--port", str(PORT),
         "--app-dir", str(BACKEND_DIR)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


if __name__ == "__main__":
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()
