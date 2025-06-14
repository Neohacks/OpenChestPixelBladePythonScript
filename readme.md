# Pixel Blade Chest Opener

A Python script with a polished GUI to automate opening chests in the Roblox game *Pixel Blade*.

![UI Screenshot](https://i.imgur.com/your-screenshot-url.png) 
*It's recommended to replace this with a real screenshot of the UI.*

---

## Features

-   **Modern Dark-Themed UI** with animated accents.
-   **Reliable Automation** using low-level input simulation.
-   **One-Click Coordinate Setup** for all required actions.
-   **Adjustable Timings** for chest opening using sliders.
-   **Live Console** to monitor bot actions and mouse position.
-   **Global Hotkey (F6)** to start and stop the script at any time.
-   **Saves Your Settings** to a `config.json` file.

---

## Requirements

-   Python 3.7+
-   Windows OS
-   Required libraries:
    ```bash
    pip install pyautogui keyboard pygetwindow pywin32
    ```

---

## How to Use

### 1. **Run as Administrator**
-   **This is the most important step.**
-   Right-click the Python script and select **"Run as administrator"**. If you don't, the clicks will not register in the game.

### 2. **Configure Positions**
-   Launch the script to open the UI.
-   For each item in the **Configuration** panel ("Chest Slot", "Open Button", etc.):
    1.  Click the **"Set"** button.
    2.  Move your mouse to the correct spot in the game.
    3.  **Left-click** to capture the coordinates.

### 3. **Adjust Timings & Save**
-   Use the sliders to control the speed of the chest opening sequence.
-   Click **"Save Config"** to remember your settings for next time.

### 4. **Run the Bot**
-   Press the green **"START (F6)"** button or the `F6` key to begin.
-   Press `F6` again to stop.

---

## Disclaimer

This script is for educational purposes. Using automation tools may be against game terms of service. Use at your own risk.
