# 💎 Pixel Blade Chest Opener 💎

A sophisticated automation tool with a polished GUI for opening chests in the Roblox game Pixel Blade.

## 📖 Overview

This script automates the repetitive task of opening chests in Pixel Blade. It's designed to be robust and user-friendly, utilizing low-level hardware inputs to ensure reliability, even in applications with advanced input detection. The interface is fully configurable, allowing you to set coordinates with a single click and fine-tune timings to match your system's performance.

The application is written with an object-oriented approach, making the code clean, optimized, and easier to maintain.

## ✨ Key Features

• **Polished User Interface**: A modern, dark-themed UI with an animated rainbow gradient for a premium feel.

• **Reliable Automation**: Employs the SendInput API for hardware-level mouse clicks that are less likely to be blocked by game clients.

• **"Human-like" Clicks**: Incorporates randomized delays and coordinate "jitter" to better mimic human behavior.

• **One-Click Configuration**: Interactively set all required screen coordinates with a simple point-and-click process.

• **Live Console**: Get real-time feedback with a built-in console that displays mouse/pixel info and a detailed log of the bot's actions.

• **Customizable Timings**: Use intuitive custom-themed sliders to adjust the duration and interval of chest-opening clicks.

• **Persistent Settings**: Your configuration is automatically saved to a config.json file and loaded on startup.

• **Global Hotkey**: Conveniently start and stop the automation at any time with the F6 key.

• **Portable Launcher**: Includes a run.bat file that automatically handles administrator permissions and dependency checks.

## 🚀 Installation & Usage

### Step 1: Download & Install Requirements

1. **Download the Project**: Place the `openchest.py` and `run.bat` files together in a new folder on your computer.

2. **Install Python**: Ensure you have Python 3.7+ installed.

3. **Install Libraries**: The included `run.bat` file handles this automatically. The first time you run it, it will check for and install any missing libraries.

### Step 2: Run the Launcher

1. Navigate to the folder where you saved the files.

2. Double-click the `run.bat` file.

3. A Windows User Account Control (UAC) prompt will appear. You must click "Yes" to grant administrator privileges. This is the most critical step for ensuring the clicks register in-game.

### Step 3: Configure Positions

1. The script's UI will launch.

2. In the Configuration panel, click the "Set" button for an action.

3. Move your mouse over the correct location in the game window and left-click.

4. The UI will reappear with the captured coordinates saved.

5. Repeat for all three required positions:
   • **Chest Slot**: The top-most chest available in the list.
   • **Open Button**: The button to open the selected chest.
   • **Opening Click Pos**: The central area where the chest appears while opening.

### Step 4: Adjust Timings & Save

1. Use the sliders to control the speed of the chest opening sequence.

2. Click "Save Config". A "✓ Saved!" message will appear on the button.

### Step 5: Run the Bot

1. Click the green "START (F6)" button or press the F6 key to begin.

2. Press F6 again to stop at any time.

## 🤝 Credits & Acknowledgements

This project was a collaborative effort:

• **Neohacks**: Project idea, testing, feedback, and final code optimizations.

• **Google's Gemini**: Primary coding, UI design, debugging, and documentation.

This tool was built using several key Python libraries:

• **Tkinter** for the GUI framework.

• **pyautogui**, **keyboard**, **pygetwindow**, and **pywin32** for system automation and control.

## ⚠️ Disclaimer

This script is provided for educational purposes only. Using automation tools may be against the terms of service for Roblox or specific games. The developer assumes no liability for the use or misuse of this software. Any action you take is strictly at your own risk.