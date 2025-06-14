import tkinter as tk
from tkinter import ttk, messagebox
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
from tkinter.font import Font as tkFont

try:
    import pygetwindow as gw
except ImportError:
    messagebox.showerror("Missing Library", "The 'pygetwindow' library is required.\nPlease install it by running: pip install pygetwindow")
    exit()
try:
    import win32api, win32con
except ImportError:
    messagebox.showerror("Missing Library", "The 'pywin32' library is required.\nPlease install it by running: pip install pywin32")
    exit()

# --- CTYPES Structure Definitions for SendInput ---
PUL = ctypes.POINTER(ctypes.c_ulong)
class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class HardwareInput(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_ulong), ("wParamL", ctypes.c_short), ("wParamH", ctypes.c_ushort)]
class MouseInput(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long), ("mouseData", ctypes.c_ulong), ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]
class Input_I(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("mi", MouseInput), ("hi", HardwareInput)]
class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("ii", Input_I)]

# --- Default Configuration (Simplified) ---
CONFIG = {
    "chest_slot": {"x": 1388, "y": 287},
    "open_button": {"x": 2400, "y": 826},
    "opening_click_pos": {"x": 2005, "y": 497},
    "opening_duration": 4.0,
    "opening_click_interval": 0.05,
}

# --- Application State ---
is_running = False
is_animating = True
script_thread = None
capture_target = None

# --- UI and Thread Management ---
def log_debug(message):
    """Adds a message to the debug window in a thread-safe way."""
    def append_message():
        if 'debug_output' in globals() and debug_output.winfo_exists():
            debug_output.config(state=tk.NORMAL)
            timestamp = time.strftime("%H:%M:%S")
            debug_output.insert(tk.END, f"[{timestamp}] {message}\n")
            debug_output.config(state=tk.DISABLED)
            debug_output.see(tk.END) # Autoscroll
    if 'root' in globals() and root.winfo_exists():
        root.after(0, append_message)

# --- Core Helper Functions ---
def move_and_click(x, y, is_spam=False):
    """
    Performs a robust single click using the SendInput method.
    Includes an option for faster movement and logging for spam clicks.
    """
    rand_x = x + random.randint(-3, 3)
    rand_y = y + random.randint(-3, 3)
    
    if not is_spam:
        log_debug(f"Clicking at ({rand_x}, {rand_y})")
    
    move_duration = 0.05 if is_spam else random.uniform(0.1, 0.2)
    pyautogui.moveTo(rand_x, rand_y, duration=move_duration)
    
    F_ABSOLUTE = 0x8000
    F_MOVE = 0x0001
    F_LEFTDOWN = 0x0002
    F_LEFTUP = 0x0004
    
    screen_width, screen_height = win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1)
    nx = int(rand_x * (65535 / screen_width))
    ny = int(rand_y * (65535 / screen_height))

    inp_down = Input_I()
    inp_down.mi = MouseInput(nx, ny, 0, (F_ABSOLUTE | F_MOVE | F_LEFTDOWN), 0, None)
    command_down = Input(ctypes.c_ulong(0), inp_down)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command_down), ctypes.sizeof(command_down))
    time.sleep(random.uniform(0.02, 0.04)) 
    inp_up = Input_I()
    inp_up.mi = MouseInput(nx, ny, 0, (F_ABSOLUTE | F_MOVE | F_LEFTUP), 0, None)
    command_up = Input(ctypes.c_ulong(0), inp_up)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(command_up), ctypes.sizeof(command_up))
    
    if not is_spam:
        time.sleep(random.uniform(0.1, 0.15))

# --- Automation Logic ---
def automation_loop():
    """Main logic for the chest-opening bot, using SendInput."""
    global is_running
    log_debug("Automation thread started. Press 'F6' to toggle.")
    time.sleep(2)

    while is_running:
        try:
            roblox_win = gw.getWindowsWithTitle('Roblox')
            if not roblox_win:
                log_debug("Roblox window not found. Pausing...")
                time.sleep(3)
                continue
            
            roblox_win = roblox_win[0]
            
            slot = CONFIG["chest_slot"]
            if slot['x'] == 0 and slot['y'] == 0:
                log_debug("Chest Slot is not configured. Pausing...")
                time.sleep(5)
                continue

            log_debug(f"Attempting to open chest at ({slot['x']}, {slot['y']}).")
            move_and_click(slot['x'], slot['y'])
            time.sleep(random.uniform(0.4, 0.6)) 
            
            log_debug(f"Clicking 'Open' button at ({CONFIG['open_button']['x']}, {CONFIG['open_button']['y']}).")
            move_and_click(CONFIG["open_button"]['x'], CONFIG["open_button"]['y'])
            time.sleep(random.uniform(0.8, 1.0)) 

            log_debug("Spam-clicking chest to open...")
            open_pos = CONFIG["opening_click_pos"]
            start_time = time.time()
            while time.time() - start_time < CONFIG["opening_duration"]:
                if not is_running: break
                move_and_click(open_pos['x'], open_pos['y'], is_spam=True) 
                time.sleep(CONFIG["opening_click_interval"]) 
            
            log_debug("Chest sequence complete. Waiting before next cycle.")
            time.sleep(random.uniform(1.2, 1.5)) 

        except Exception as e:
            log_debug(f"ERROR: {e}")
            stop_automation()
            messagebox.showerror("An Error Occurred", f"Script stopped: {e}")
            break
            
    if not is_running:
         log_debug("Automation stopped by user.")

# --- UI LOGIC AND MANAGEMENT ---
def start_automation():
    global is_running, script_thread
    if CONFIG["chest_slot"]['x'] == 0 or CONFIG["open_button"]['x'] == 0 or CONFIG["opening_click_pos"]['x'] == 0:
        messagebox.showwarning("Configuration Incomplete", "Please set the Chest Slot, Open Button, and Opening Click Position.")
        return
    if not is_running:
        is_running = True
        script_thread = threading.Thread(target=automation_loop, daemon=True)
        script_thread.start()
        update_ui_state()

def stop_automation():
    global is_running
    if is_running:
        is_running = False
        update_ui_state()

def toggle_automation():
    if is_running: stop_automation()
    else: start_automation()

def update_ui_state():
    is_on = is_running
    start_button.config(state=tk.DISABLED if is_on else tk.NORMAL)
    stop_button.config(state=tk.NORMAL if is_on else tk.DISABLED)

def save_config():
    """Saves the current UI settings to config.json."""
    try:
        def parse_entry(entry_text):
            return [int(v.strip()) for v in re.findall(r'-?\d+', entry_text)]
        
        coords = parse_entry(chest_slot_entry.get())
        if len(coords) == 2: CONFIG["chest_slot"] = {"x": coords[0], "y": coords[1]}

        for key, entry in config_entries.items():
            coords = parse_entry(entry.get())
            if len(coords) == 2: CONFIG[key] = {"x": coords[0], "y": coords[1]}

        CONFIG["opening_duration"] = duration_slider.get()
        CONFIG["opening_click_interval"] = interval_slider.get()

        with open("config.json", "w") as f:
            json.dump(CONFIG, f, indent=4)
        messagebox.showinfo("Success", "Configuration saved to config.json")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save config. Ensure formats are correct.\n\nError: {e}")

def load_config():
    """Loads settings from config.json if it exists."""
    global CONFIG
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                loaded_config = json.load(f)
                for key, value in CONFIG.items():
                    CONFIG[key] = loaded_config.get(key, value)
        except json.JSONDecodeError:
            messagebox.showerror("Config Error", "Could not read config.json. It might be corrupted. Using defaults.")

def on_capture_click(event):
    """Handles the mouse click event on the transparent capture window."""
    global capture_target, all_set_buttons
    event.widget.destroy() 

    if capture_target:
        x, y = event.x_root, event.y_root
        text_val = f"({x}, {y})"
        
        CONFIG[capture_target["key"]] = {"x": x, "y": y}

        capture_target["widget"].delete(0, tk.END)
        capture_target["widget"].insert(0, text_val)
        
        capture_target["button"].config(style=capture_target["original_style"])
        for btn in all_set_buttons:
            btn.config(state=tk.NORMAL)
        
        capture_target = None
    root.deiconify() 

def set_capture_target(target_widget, button, original_style, key):
    """Initiates the screen capture process."""
    global capture_target, all_set_buttons
    
    for btn in all_set_buttons:
        btn.config(state=tk.DISABLED)
    button.config(state=tk.NORMAL, style="Highlight.TButton")

    capture_target = {"widget": target_widget, "button": button, "original_style": original_style, "key": key}
    
    root.withdraw() 
    capture_window = tk.Toplevel(root)
    capture_window.attributes('-fullscreen', True)
    capture_window.attributes('-alpha', 0.1)
    capture_window.wait_visibility(capture_window)
    capture_window.attributes('-topmost', True)
    capture_window.config(cursor="crosshair")
    
    capture_window.bind("<Button-1>", on_capture_click)
    capture_window.bind("<Escape>", lambda e: (e.widget.destroy(), root.deiconify(), button.config(style=original_style), [btn.config(state=tk.NORMAL) for btn in all_set_buttons]))

# --- Animated Gradient Logic ---
def create_smooth_gradient(colors, steps_per_transition):
    """Generates a list of hex color strings for a smooth gradient."""
    gradient = []
    extended_colors = colors + [colors[0]] 
    for i in range(len(extended_colors) - 1):
        c1 = extended_colors[i]
        c2 = extended_colors[i+1]
        r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
        r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
        for j in range(steps_per_transition):
            p = j / steps_per_transition
            r = int(r1 * (1 - p) + r2 * p)
            g = int(g1 * (1 - p) + g2 * p)
            b = int(b1 * (1 - p) + b2 * p)
            gradient.append(f'#{r:02x}{g:02x}{b:02x}')
    return gradient

def animate_gradient_thread(bar_canvas, header_canvas, header_font, header_text, colors):
    """Shifts the colors and triggers a redraw in a loop."""
    color_deque = deque(colors)
    while is_animating:
        try:
            color_deque.rotate(-1)
            current_colors = list(color_deque)
            canvas_list = [bar_canvas, header_canvas]
            for canvas in canvas_list:
                if canvas.winfo_exists():
                    canvas.after(0, update_animations, bar_canvas, header_canvas, header_font, header_text, current_colors)
            time.sleep(0.05)
        except Exception:
            break

def update_animations(bar_canvas, header_canvas, header_font, header_text, colors):
    """Draws the gradient on the canvas and updates the header color."""
    bar_canvas.delete("all")
    width = bar_canvas.winfo_width()
    height = bar_canvas.winfo_height()
    if width > 1 and height > 1:
        for i, color in enumerate(colors):
            x0 = i * (width / len(colors))
            x1 = (i + 1) * (width / len(colors))
            bar_canvas.create_rectangle(x0, 0, x1, height, fill=color, outline="")

    header_canvas.delete("all")
    header_width = header_canvas.winfo_width()
    header_height = header_canvas.winfo_height()
    if header_width > 1 and header_height > 1:
        text_width = header_font.measure(header_text)
        x_start = (header_width - text_width) / 2
        y_center = header_height / 2
        
        char_colors = deque(colors)
        for char in header_text:
            char_width = header_font.measure(char)
            header_canvas.create_text(x_start, y_center, text=char, fill=char_colors[0], font=header_font, anchor='w')
            x_start += char_width
            char_colors.rotate(-4) 

def finder_loop(label):
    while is_animating:
        try:
            x, y = pyautogui.position()
            r, g, b = pyautogui.pixel(x, y)
            label.config(text=f"X: {x:>4}, Y: {y:>4}  |  RGB: ({r:>3},{g:>3},{b:>3})")
            time.sleep(0.1)
        except (OSError, tk.TclError, pyautogui.PyAutoGUIException): break

# --- GUI Creation ---
def create_gui():
    global root, start_button, stop_button, chest_slot_entry, config_entries, duration_slider, debug_output, interval_slider, all_set_buttons
    load_config()

    root = tk.Tk()
    root.title("Pixel Blade Chest Opener")
    root.geometry("680x780") 
    root.resizable(False, False) 
    
    BG_COLOR = "#2B2B2B"
    FRAME_COLOR = "#3C3F41"
    TEXT_COLOR = "#A9B7C6"
    ENTRY_BG = "#313335"
    HEADER_COLOR = "#CCCCCC"
    DULL_RAINBOW = ["#8C5353", "#8C6F53", "#8C8C53", "#6F8C53", "#538C8C", "#6F538C", "#8C5379"]

    root.configure(bg=BG_COLOR)
    style = ttk.Style(root)
    style.theme_use('clam')

    font_family = "Segoe UI"
    style.configure('.', background=BG_COLOR, foreground=TEXT_COLOR, font=(font_family, 10))
    style.configure('TFrame', background=BG_COLOR)
    style.configure('TLabel', background=BG_COLOR, foreground=TEXT_COLOR, font=(font_family, 10))
    style.configure('Header.TLabel', foreground=HEADER_COLOR, font=(font_family, 18, 'bold'))
    style.configure('SubHeader.TLabel', foreground=TEXT_COLOR, font=(font_family, 9, 'italic'))
    style.configure('TLabelframe', background=BG_COLOR, bordercolor=FRAME_COLOR, relief='solid', borderwidth=1)
    style.configure('TLabelframe.Label', background=BG_COLOR, foreground=TEXT_COLOR, font=(font_family, 11, 'bold'))
    style.configure('TButton', font=(font_family, 10, 'bold'), borderwidth=0, padding=(10, 8), relief='flat')
    style.map('TButton', background=[('active', '#55555C')])
    style.configure('Highlight.TButton', background="#E8E8E8", foreground=BG_COLOR)
    for i, color in enumerate(DULL_RAINBOW):
        style.configure(f'Accent{i}.TButton', background=color, foreground=HEADER_COLOR)
        style.map(f'Accent{i}.TButton', background=[('active', TEXT_COLOR)])
    style.configure("Horizontal.TScale", background=BG_COLOR, troughcolor=ENTRY_BG, bordercolor=FRAME_COLOR)
    
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(expand=True, fill="both")
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(3, weight=1)
    
    header_font = tkFont(family=font_family, size=18, weight='bold')
    header_text = "Pixel Blade Chest Opener"
    header_canvas = tk.Canvas(main_frame, height=header_font.metrics('linespace'), bg=BG_COLOR, highlightthickness=0)
    header_canvas.grid(row=0, column=0, pady=(0, 5), sticky='ew')
    
    rainbow_canvas = tk.Canvas(main_frame, height=4, bg=BG_COLOR, highlightthickness=0)
    rainbow_canvas.grid(row=1, column=0, sticky="ew", pady=(0, 20))
    
    controls_frame = ttk.LabelFrame(main_frame, text="Controls", padding=15)
    controls_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
    controls_frame.columnconfigure((0, 1), weight=1)
    start_button = ttk.Button(controls_frame, text="START (F6)", command=start_automation, style='Accent3.TButton')
    start_button.grid(row=0, column=0, sticky="ew", padx=5)
    stop_button = ttk.Button(controls_frame, text="STOP (F6)", command=stop_automation, state=tk.DISABLED, style='Accent0.TButton')
    stop_button.grid(row=0, column=1, sticky="ew", padx=5)
    admin_warning = ttk.Label(controls_frame, text="Tip: If clicks don't register, right-click this script and 'Run as administrator'.", wraplength=500, justify='center', style='SubHeader.TLabel')
    admin_warning.grid(row=1, column=0, columnspan=2, pady=(15, 5))

    content_frame = ttk.Frame(main_frame)
    content_frame.grid(row=3, column=0, sticky="nsew")
    content_frame.columnconfigure(1, weight=1)
    content_frame.rowconfigure(0, weight=1)

    config_frame = ttk.LabelFrame(content_frame, text="Configuration", padding=(15, 10))
    config_frame.grid(row=0, column=0, sticky="ns")
    config_frame.columnconfigure(0, weight=1)
    
    debug_frame = ttk.LabelFrame(content_frame, text="Live Console", padding=(10, 5))
    debug_frame.grid(row=0, column=1, sticky="nsew", padx=15)
    debug_frame.columnconfigure(0, weight=1)
    debug_frame.rowconfigure(1, weight=1)
    
    info_label = ttk.Label(debug_frame, text="X:    0, Y:    0  |  RGB: (  0,  0,  0)", font=("Consolas", 10), justify='center')
    info_label.grid(row=0, column=0, sticky='ew', pady=(0,5))
    debug_output = tk.Text(debug_frame, state=tk.DISABLED, background=ENTRY_BG, foreground=TEXT_COLOR, relief=tk.FLAT, font=("Consolas", 9), wrap=tk.WORD, borderwidth=0, highlightthickness=0)
    debug_output.grid(row=1, column=0, sticky="nsew")
    
    all_set_buttons = []
    config_entries = {}
    
    row=0
    # Single Chest Slot
    btn_style = 'Accent0.TButton'
    ttk.Label(config_frame, text="Chest Slot", font=(font_family, 10, 'bold')).grid(row=row, column=0, sticky="w", pady=(10, 2))
    chest_slot_entry = tk.Entry(config_frame, bg=ENTRY_BG, fg=TEXT_COLOR, relief='flat', font=(font_family, 10), width=15, insertbackground=TEXT_COLOR)
    chest_slot_entry.grid(row=row+1, column=0, sticky="ew", pady=(0, 5))
    chest_slot_entry.insert(0, f"({CONFIG['chest_slot']['x']}, {CONFIG['chest_slot']['y']})")
    button = ttk.Button(config_frame, text="Set", style=btn_style, width=5)
    button.config(command=lambda e=chest_slot_entry, b=button, s=btn_style, k="chest_slot": set_capture_target(e, b, s, k))
    button.grid(row=row+1, column=1, padx=(10,0), pady=(0, 5))
    all_set_buttons.append(button)
    row += 2
        
    # Other settings
    setting_map = {"Open Button": "open_button", "Opening Click Pos": "opening_click_pos"}
    for i, (label_text, key) in enumerate(setting_map.items()):
        btn_style = f'Accent{i+1}.TButton'
        ttk.Label(config_frame, text=label_text, font=(font_family, 10, 'bold')).grid(row=row, column=0, sticky="w", pady=(10,2))
        entry = tk.Entry(config_frame, bg=ENTRY_BG, fg=TEXT_COLOR, relief='flat', font=(font_family, 10), width=15, insertbackground=TEXT_COLOR)
        entry.grid(row=row+1, column=0, sticky="ew", pady=(0, 5))
        entry.insert(0, f"({CONFIG[key]['x']}, {CONFIG[key]['y']})")
        button = ttk.Button(config_frame, text="Set", style=btn_style, width=5)
        button.config(command=lambda e=entry, b=button, s=btn_style, k=key: set_capture_target(e, b, s, k))
        button.grid(row=row+1, column=1, padx=(10,0), pady=(0, 5))
        all_set_buttons.append(button)
        config_entries[key] = entry
        row += 2

    # Sliders
    duration_label_val = tk.StringVar(value=f'{CONFIG["opening_duration"]:.1f}s')
    ttk.Label(config_frame, text="Opening Duration", font=(font_family, 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10,2))
    duration_slider = ttk.Scale(config_frame, from_=1, to=15, orient='horizontal', style="Horizontal.TScale", command=lambda v: duration_label_val.set(f'{float(v):.1f}s'))
    duration_slider.set(CONFIG["opening_duration"])
    duration_slider.grid(row=row+1, column=0, columnspan=2, sticky="ew")
    ttk.Label(config_frame, textvariable=duration_label_val, font=(font_family, 9, 'italic')).grid(row=row, column=1, sticky="e", pady=(10,2))
    row += 2
    
    interval_label_val = tk.StringVar(value=f'{CONFIG["opening_click_interval"]:.2f}s')
    ttk.Label(config_frame, text="Opening Click Interval", font=(font_family, 10, 'bold')).grid(row=row, column=0, columnspan=2, sticky="w", pady=(10,2))
    ttk.Label(config_frame, textvariable=interval_label_val, font=(font_family, 9, 'italic')).grid(row=row, column=1, sticky="e", pady=(10,2))
    interval_slider = ttk.Scale(config_frame, from_=0.01, to=1.0, orient='horizontal', style="Horizontal.TScale", command=lambda v: interval_label_val.set(f'{float(v):.2f}s'))
    interval_slider.set(CONFIG["opening_click_interval"])
    interval_slider.grid(row=row+1, column=0, columnspan=2, sticky="ew")
    row += 2

    save_button = ttk.Button(config_frame, text="Save Config", command=save_config, style='Accent5.TButton')
    save_button.grid(row=row, column=0, columnspan=2, pady=(20, 0), sticky="ew")

    keyboard.add_hotkey('f6', toggle_automation)
    
    smooth_gradient_colors = create_smooth_gradient(DULL_RAINBOW, steps_per_transition=30)
    animation_thread = threading.Thread(target=animate_gradient_thread, args=(rainbow_canvas, header_canvas, header_font, header_text, smooth_gradient_colors), daemon=True)
    animation_thread.start()
    
    finder_thread = threading.Thread(target=finder_loop, args=(info_label,), daemon=True)
    finder_thread.start()
    
    def on_closing():
        global is_animating
        is_animating = False
        stop_automation()
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    pyautogui.FAILSAFE = True
    create_gui()
