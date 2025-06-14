import tkinter as tk
from tkinter import ttk, font as tkFont
import threading
import time
import pyautogui
import keyboard
import json
import os
import re
import random
import ctypes
from collections import deque

try:
    import pygetwindow as gw
except ImportError:
    root = tk.Tk(); root.withdraw()
    tk.messagebox.showerror("Missing Library", "pygetwindow is required. Please run: pip install pygetwindow")
    exit()
try:
    import win32api, win32con
except ImportError:
    root = tk.Tk(); root.withdraw()
    tk.messagebox.showerror("Missing Library", "pywin32 is required. Please run: pip install pywin32")
    exit()

# CTYPES definitions for low-level input
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure): _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class HardwareInput(ctypes.Structure): _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]
class MouseInput(ctypes.Structure): _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class Input_I(ctypes.Union): _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]
class Input(ctypes.Structure): _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

class PixelBladeApp:
    def __init__(self):
        self.root = tk.Tk()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file_path = os.path.join(self.script_dir, "config.json")
        self.is_running = False
        self.script_thread = None
        self.capture_target = None
        self.ui_update_job = None
        self.config = {
            "chest_slot": {"x": 1388, "y": 287},
            "open_button": {"x": 2400, "y": 826},
            "opening_click_pos": {"x": 2005, "y": 497},
            "opening_duration": 4.0,
            "opening_click_interval": 0.05,
        }
        self.BG_COLOR = "#2B2B2B"
        self.font_family = "Segoe UI"
        self.STATUS_COLORS = {"idle": "#A9B7C6", "running": "#6A8759", "paused": "#FFC66D", "error": "#CC7832"}
        self.DULL_RAINBOW = ["#8C5353", "#8C6F53", "#8C8C53", "#6F8C53", "#538C8C", "#6F538C", "#8C5379"]
        self.load_config()
        self._setup_ui()

    def _setup_ui(self):
        self.root.title("Pixel Blade Chest Opener")
        self.root.geometry("620x720")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG_COLOR)
        self._configure_styles()
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(expand=True, fill="both")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        self._create_header(main_frame)
        self._create_controls(main_frame)
        self._create_content_panels(main_frame)
        keyboard.add_hotkey('f6', self.toggle_automation)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.after(100, self.start_ui_updates)

    def _configure_styles(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        FRAME_COLOR, TEXT_COLOR, HEADER_COLOR = "#3C3F41", "#A9B7C6", "#CCCCCC"
        style.configure('.', background=self.BG_COLOR, foreground=TEXT_COLOR, font=(self.font_family, 10))
        style.configure('TFrame', background=self.BG_COLOR)
        style.configure('TLabel', background=self.BG_COLOR, foreground=TEXT_COLOR, font=(self.font_family, 10))
        style.configure('Status.TLabel', font=(self.font_family, 10, 'bold'))
        style.configure('Header.TLabel', foreground=HEADER_COLOR, font=(self.font_family, 18, 'bold'))
        style.configure('TLabelframe', background=self.BG_COLOR, bordercolor=FRAME_COLOR, relief='solid')
        style.configure('TLabelframe.Label', background=self.BG_COLOR, foreground=TEXT_COLOR, font=(self.font_family, 11, 'bold'))
        style.configure('TButton', font=(self.font_family, 10, 'bold'), borderwidth=0, padding=(10, 8), relief='flat')
        style.map('TButton', background=[('active', '#55555C')])
        style.configure('Highlight.TButton', background="#E8E8E8", foreground=self.BG_COLOR)
        for i, color in enumerate(self.DULL_RAINBOW):
            style.configure(f'Accent{i}.TButton', background=color, foreground=HEADER_COLOR)
            style.map(f'Accent{i}.TButton', background=[('active', TEXT_COLOR)])
        style.configure('Saved.TButton', background="#6F8C53", foreground=HEADER_COLOR)

    def _create_header(self, parent):
        self.header_font = tkFont.Font(family=self.font_family, size=18, weight='bold')
        self.header_text = "Pixel Blade Chest Opener"
        self.header_canvas = tk.Canvas(parent, height=self.header_font.metrics('linespace'), bg=self.BG_COLOR, highlightthickness=0)
        self.header_canvas.grid(row=0, column=0, pady=(0, 5), sticky='ew')
        self.rainbow_canvas = tk.Canvas(parent, height=4, bg=self.BG_COLOR, highlightthickness=0)
        self.rainbow_canvas.grid(row=1, column=0, sticky="ew", pady=(0, 20))

    def _create_controls(self, parent):
        controls_frame = ttk.LabelFrame(parent, text="Controls", padding=15)
        controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        controls_frame.columnconfigure((0, 1), weight=1)
        self.start_button = ttk.Button(controls_frame, text="START (F6)", command=self.start_automation, style='Accent3.TButton')
        self.start_button.grid(row=0, column=0, sticky="ew", padx=5)
        self.stop_button = ttk.Button(controls_frame, text="STOP (F6)", command=self.stop_automation, state=tk.DISABLED, style='Accent0.TButton')
        self.stop_button.grid(row=0, column=1, sticky="ew", padx=5)
        status_frame = ttk.Frame(controls_frame)
        status_frame.grid(row=1, column=0, columnspan=2, pady=(15, 5), sticky='ew')
        status_frame.columnconfigure(1, weight=1)
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky='w')
        self.status_label = ttk.Label(status_frame, text="Idle", style='Status.TLabel', foreground=self.STATUS_COLORS['idle'])
        self.status_label.grid(row=0, column=1, sticky='w', padx=5)

    def _create_content_panels(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.grid(row=3, column=0, sticky="nsew")
        content_frame.columnconfigure(1, weight=3); content_frame.columnconfigure(0, weight=2)
        content_frame.rowconfigure(0, weight=1)
        self._create_config_panel(content_frame)
        self._create_console_panel(content_frame)
    
    def _create_config_panel(self, parent):
        config_frame = ttk.LabelFrame(parent, text="Configuration", padding=(15, 10))
        config_frame.grid(row=0, column=0, sticky="ns", padx=(0, 15))
        config_frame.columnconfigure(0, weight=3)
        config_frame.columnconfigure(1, weight=1)

        self.all_set_buttons = []
        self.config_entries = {}

        def create_coord_entry(p, label_text, key, accent_index):
            btn_style = f'Accent{accent_index}.TButton'
            row = len(self.config_entries) * 2
            ttk.Label(p, text=label_text, font=(self.font_family, 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 2))
            entry = tk.Entry(p, bg="#313335", fg="#A9B7C6", relief='flat', font=(self.font_family, 10), width=15, insertbackground="#A9B7C6")
            entry.grid(row=row+1, column=0, sticky="ew", pady=(0, 5))
            entry.insert(0, f"({self.config[key]['x']}, {self.config[key]['y']})")
            
            # FIX: Create button first, then configure its command to avoid UnboundLocalError
            button = ttk.Button(p, text="Set", style=btn_style, width=5)
            button.config(command=lambda e=entry, b=button, s=btn_style, k=key: self.set_capture_target(e, b, s, k))
            
            button.grid(row=row+1, column=1, padx=(10,0), pady=(0, 5))
            self.all_set_buttons.append(button)
            return entry

        self.config_entries['chest_slot'] = create_coord_entry(config_frame, "Chest Slot", "chest_slot", 0)
        self.config_entries['open_button'] = create_coord_entry(config_frame, "Open Button", "open_button", 1)
        self.config_entries['opening_click_pos'] = create_coord_entry(config_frame, "Opening Click Pos", "opening_click_pos", 2)

        current_row = len(self.config_entries) * 2
        duration_label_val = tk.StringVar(value=f'{self.config["opening_duration"]:.1f}s')
        ttk.Label(config_frame, text="Opening Duration", font=(self.font_family, 10, 'bold')).grid(row=current_row, column=0, sticky="w", pady=(10,2))
        ttk.Label(config_frame, textvariable=duration_label_val, font=(self.font_family, 9, 'italic')).grid(row=current_row, column=1, sticky="e", pady=(10,2))
        self.duration_slider = CustomSlider(config_frame, from_=1, to=15, initial_value=self.config["opening_duration"], command=lambda v: duration_label_val.set(f'{float(v):.1f}s'), bg=self.BG_COLOR)
        self.duration_slider.grid(row=current_row+1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        current_row += 2
        interval_label_val = tk.StringVar(value=f'{self.config["opening_click_interval"]:.2f}s')
        ttk.Label(config_frame, text="Opening Click Interval", font=(self.font_family, 10, 'bold')).grid(row=current_row, column=0, sticky="w", pady=(10,2))
        ttk.Label(config_frame, textvariable=interval_label_val, font=(self.font_family, 9, 'italic')).grid(row=current_row, column=1, sticky="e", pady=(10,2))
        self.interval_slider = CustomSlider(config_frame, from_=0.01, to=1.0, initial_value=self.config["opening_click_interval"], command=lambda v: interval_label_val.set(f'{float(v):.2f}s'), bg=self.BG_COLOR)
        self.interval_slider.grid(row=current_row+1, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        current_row += 2
        self.save_button = ttk.Button(config_frame, text="Save Config", command=self.save_config, style='Accent5.TButton')
        self.save_button.grid(row=current_row, column=0, columnspan=2, pady=(20, 0), sticky="ew")

    def _create_console_panel(self, parent):
        debug_frame = ttk.LabelFrame(parent, text="Live Console", padding=(10, 5))
        debug_frame.grid(row=0, column=1, sticky="nsew")
        debug_frame.columnconfigure(0, weight=1); debug_frame.rowconfigure(1, weight=1)
        self.info_label = ttk.Label(debug_frame, text="X: ... , Y: ...  |  RGB: (...) ", font=("Consolas", 10), anchor='center')
        self.info_label.grid(row=0, column=0, sticky='ew', pady=(0,5))
        self.debug_output = tk.Text(debug_frame, state=tk.DISABLED, background="#313335", fg="#A9B7C6", relief=tk.FLAT, font=("Consolas", 9), wrap=tk.WORD, borderwidth=0)
        self.debug_output.grid(row=1, column=0, sticky="nsew")
    
    def log_debug(self, message):
        def append_message():
            if not self.debug_output.winfo_exists(): return
            self.debug_output.config(state=tk.NORMAL)
            self.debug_output.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.debug_output.config(state=tk.DISABLED); self.debug_output.see(tk.END)
        if self.root.winfo_exists(): self.root.after(0, append_message)

    def start_automation(self):
        if self.is_running: return
        if any(self.config[key]['x'] == 0 for key in ["chest_slot", "open_button", "opening_click_pos"]):
            CustomMessagebox(self.root, "Config Incomplete", "Please set all required positions.", "warning"); return
        self.is_running = True
        self.script_thread = threading.Thread(target=self.automation_loop, daemon=True)
        self.script_thread.start()
        self.update_ui_state()

    def stop_automation(self):
        if self.is_running:
            self.is_running = False
            self.update_ui_state()

    def toggle_automation(self):
        if self.is_running: self.stop_automation()
        else: self.start_automation()

    def update_ui_state(self):
        is_on = self.is_running
        self.start_button.config(state=tk.DISABLED if is_on else tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL if is_on else tk.DISABLED)
        self.update_status("Running" if is_on else "Idle", "running" if is_on else "idle")
    
    def update_status(self, message, status_type="idle"):
        color = self.STATUS_COLORS.get(status_type, self.STATUS_COLORS["idle"])
        def _update():
            if self.status_label.winfo_exists(): self.status_label.config(text=message, foreground=color)
        if self.root.winfo_exists(): self.root.after(0, _update)
        if status_type in ["error", "paused"]: self.log_debug(f"STATUS: {message}")

    def save_config(self):
        try:
            for key, entry in self.config_entries.items():
                coords = [int(v.strip()) for v in re.findall(r'-?\d+', entry.get())]
                if len(coords) == 2: self.config[key] = {"x": coords[0], "y": coords[1]}
            self.config["opening_duration"] = self.duration_slider.get()
            self.config["opening_click_interval"] = self.interval_slider.get()
            with open(self.config_file_path, "w") as f: json.dump(self.config, f, indent=4)
            self.save_button.config(text="✓ Saved!", style="Saved.TButton", state=tk.DISABLED)
            self.root.after(1500, lambda: self.save_button.config(text="Save Config", style="Accent5.TButton", state=tk.NORMAL))
        except Exception as e: CustomMessagebox(self.root, "Error", f"Failed to save config: {e}", "error")

    def load_config(self):
        if os.path.exists(self.config_file_path):
            try:
                with open(self.config_file_path, "r") as f: self.config.update(json.load(f))
            except json.JSONDecodeError: CustomMessagebox(self.root, "Config Error", "config.json is corrupted.", "error")

    def set_capture_target(self, target_widget, button, original_style, key):
        for btn in self.all_set_buttons: btn.config(state=tk.DISABLED)
        button.config(state=tk.NORMAL, style="Highlight.TButton")
        self.capture_target = {"widget": target_widget, "button": button, "original_style": original_style, "key": key}
        self.root.withdraw()
        capture_window = tk.Toplevel(self.root)
        capture_window.attributes('-fullscreen', True, '-alpha', 0.1, '-topmost', True)
        capture_window.config(cursor="crosshair")
        capture_window.bind("<Button-1>", self.on_capture_click)
        capture_window.bind("<Escape>", self.on_capture_cancel)

    def on_capture_click(self, event):
        x, y = event.x_root, event.y_root
        if self.capture_target:
            self.config[self.capture_target["key"]] = {"x": x, "y": y}
            self.capture_target["widget"].delete(0, tk.END); self.capture_target["widget"].insert(0, f"({x}, {y})")
        self.on_capture_cancel(event)

    def on_capture_cancel(self, event):
        event.widget.destroy()
        if self.capture_target: self.capture_target["button"].config(style=self.capture_target["original_style"])
        for btn in self.all_set_buttons: btn.config(state=tk.NORMAL)
        self.capture_target = None
        self.root.deiconify()
    
    def start_ui_updates(self):
        self.root.update_idletasks()
        header_width = self.header_canvas.winfo_width()
        text_width = self.header_font.measure(self.header_text)
        x_start = (header_width - text_width) / 2
        y_center = self.header_font.metrics('linespace') / 2
        self.header_char_ids = [
            self.header_canvas.create_text(x_start + self.header_font.measure(self.header_text[:i]), y_center, text=char, fill="white", font=self.header_font, anchor='w')
            for i, char in enumerate(self.header_text)
        ]
        self.color_deque = deque(self._create_smooth_gradient(self.DULL_RAINBOW, 30))
        self.unified_ui_loop()

    def unified_ui_loop(self):
        if not self.root.winfo_exists(): return
        self.update_animations(list(self.color_deque))
        self.color_deque.rotate(-1)
        try:
            x, y = pyautogui.position()
            r, g, b = pyautogui.pixel(x, y)
            self.info_label.config(text=f"X: {x:>4}, Y: {y:>4}  |  RGB: ({r:>3},{g:>3},{b:>3})")
        except Exception: pass
        self.ui_update_job = self.root.after(50, self.unified_ui_loop)

    def _create_smooth_gradient(self, colors, steps):
        gradient = []
        extended_colors = colors + [colors[0]]
        for i in range(len(extended_colors) - 1):
            r1,g1,b1 = self.root.winfo_rgb(extended_colors[i]); r2,g2,b2 = self.root.winfo_rgb(extended_colors[i+1])
            for j in range(steps):
                p = j / steps
                r, g, b = int(r1 * (1 - p) + r2 * p) >> 8, int(g1 * (1 - p) + g2 * p) >> 8, int(b1 * (1 - p) + b2 * p) >> 8
                gradient.append(f'#{r:02x}{g:02x}{b:02x}')
        return gradient

    def update_animations(self, colors):
        width, height = self.rainbow_canvas.winfo_width(), self.rainbow_canvas.winfo_height()
        self.rainbow_canvas.delete("all")
        if width > 1:
            for i, color in enumerate(colors):
                self.rainbow_canvas.create_rectangle(i * (width / len(colors)), 0, (i + 1) * (width / len(colors)), height, fill=color, outline="")
        char_colors = deque(colors)
        for item_id in self.header_char_ids:
            self.header_canvas.itemconfig(item_id, fill=char_colors[0]); char_colors.rotate(-4)
    
    def move_and_click(self, x, y, is_spam=False):
        rand_x, rand_y = x + random.randint(-3, 3), y + random.randint(-3, 3)
        if not is_spam: self.log_debug(f"Clicking at ({rand_x}, {rand_y})")
        pyautogui.moveTo(rand_x, rand_y, duration=0.05 if is_spam else random.uniform(0.1, 0.2))
        screen_width, screen_height = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
        nx, ny = int(rand_x * 65535 / screen_width), int(rand_y * 65535 / screen_height)
        
        flags = 0x8001; down_flags, up_flags = flags | 0x0002, flags | 0x0004
        
        inp_down = Input_I(); inp_down.mi = MouseInput(nx, ny, 0, down_flags, 0, None)
        inp_up = Input_I(); inp_up.mi = MouseInput(nx, ny, 0, up_flags, 0, None)
        command_down = Input(ctypes.c_ulong(0), inp_down); command_up = Input(ctypes.c_ulong(0), inp_up)
        
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command_down), ctypes.sizeof(command_down))
        time.sleep(random.uniform(0.02, 0.04))
        ctypes.windll.user32.SendInput(1, ctypes.pointer(command_up), ctypes.sizeof(command_up))
        if not is_spam: time.sleep(random.uniform(0.1, 0.15))

    def automation_loop(self):
        self.log_debug("Automation thread started."); time.sleep(1)
        while self.is_running:
            try:
                roblox_windows = gw.getWindowsWithTitle('Roblox')
                if not roblox_windows:
                    self.update_status("Paused: Roblox not found", "paused"); time.sleep(3); continue
                roblox_win, active_win = roblox_windows[0], gw.getActiveWindow()
                if not active_win or active_win.title != roblox_win.title:
                    self.update_status("Focusing Roblox...", "paused"); roblox_win.activate(); time.sleep(0.5)
                    if not gw.getActiveWindow() or gw.getActiveWindow().title != roblox_win.title:
                        self.log_debug("Failed to focus Roblox, retrying..."); time.sleep(2); continue
                self.update_status("Running: Opening chest...", "running")
                self.move_and_click(self.config["chest_slot"]['x'], self.config["chest_slot"]['y']); time.sleep(random.uniform(0.4, 0.6))
                self.move_and_click(self.config["open_button"]['x'], self.config["open_button"]['y']); time.sleep(random.uniform(0.8, 1.0))
                self.log_debug("Spam-clicking...")
                start_time, open_pos = time.time(), self.config["opening_click_pos"]
                while time.time() - start_time < self.config["opening_duration"]:
                    if not self.is_running: break
                    self.move_and_click(open_pos['x'], open_pos['y'], is_spam=True); time.sleep(self.config["opening_click_interval"])
                if self.is_running: self.log_debug("Cycle complete."); time.sleep(random.uniform(1.2, 1.5))
            except Exception as e:
                self.update_status(f"Error: {e}", "error"); self.stop_automation()
                CustomMessagebox(self.root, "Error", f"Script stopped: {e}", "error"); break
        if not self.is_running: self.log_debug("Automation stopped by user.")

    def on_closing(self):
        if self.ui_update_job: self.root.after_cancel(self.ui_update_job)
        self.stop_automation(); self.root.destroy()

    def run(self):
        self.root.mainloop()

class CustomSlider(tk.Canvas):
    def __init__(self, parent, from_, to, initial_value, command, **kwargs):
        kwargs.setdefault('height', 20); kwargs.setdefault('highlightthickness', 0)
        super().__init__(parent, **kwargs)
        self.from_, self.to_, self.command = from_, to, command
        self.set(initial_value)
        self.bind("<Configure>", self._draw); self.bind("<B1-Motion>", self._on_drag); self.bind("<Button-1>", self._on_drag)

    def _draw(self, e=None):
        self.delete("all"); width, height = self.winfo_width(), self.winfo_height()
        self.create_rectangle(5, height/2 - 3, width - 5, height/2 + 3, fill="#313335", outline="")
        pos = 5 + ((self.value - self.from_) / (self.to_ - self.from_)) * (width - 10)
        self.create_oval(pos-6, height/2-6, pos+6, height/2+6, fill="#A9B7C6", outline="#E8E8E8", width=1)

    def _on_drag(self, e):
        pos = max(5, min(e.x, self.winfo_width() - 5))
        self.value = self.from_ + ((pos - 5) / (self.winfo_width() - 10)) * (self.to_ - self.from_)
        self._draw()
        if self.command: self.command(self.value)

    def get(self): return self.value
    def set(self, value): self.value = value

class CustomMessagebox(tk.Toplevel):
    def __init__(self, parent, title, message, alert_type="info"):
        super().__init__(parent)
        self.title(title); self.overrideredirect(True)
        self.config(bg="#2B2B2B", highlightbackground="#3C3F41", highlightthickness=1)
        px, py, pw, ph = parent.winfo_x(), parent.winfo_y(), parent.winfo_width(), parent.winfo_height()
        self.geometry(f"350x150+{px + (pw // 2) - 175}+{py + (ph // 2) - 75}")
        self.transient(parent); self.grab_set()
        main_frame = ttk.Frame(self, padding=20); main_frame.pack(expand=True, fill="both")
        main_frame.bind('<ButtonPress-1>', lambda e: setattr(self, '_off', (e.x, e.y)))
        main_frame.bind('<B1-Motion>', lambda e: self.geometry(f'+{self.winfo_x() + e.x - self._off[0]}+{self.winfo_y() + e.y - self._off[1]}'))
        msg_frame = ttk.Frame(main_frame); msg_frame.pack(expand=True, fill="both")
        icon_color = {"info": "#3399FF", "warning": "#FFCC00", "error": "#FF3333"}.get(alert_type)
        icon_text = "i" if alert_type == "info" else "!"
        ttk.Label(msg_frame, text=icon_text, font=("Segoe UI", 24, 'bold'), foreground=icon_color).pack(side="left", padx=(0, 15))
        ttk.Label(msg_frame, text=message, wraplength=250, justify="left").pack(side="left", expand=True, fill="both")
        btn_frame = ttk.Frame(main_frame, padding=(0, 10, 0, 0)); btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="OK", command=self.destroy, style="Accent4.TButton").pack()

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    app = PixelBladeApp()
    app.run()