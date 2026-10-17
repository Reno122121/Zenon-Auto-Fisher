"""Screen-region fishing helper for a custom Roblox mini-game."""
import threading
import time
import tkinter as tk
from tkinter import messagebox
import ctypes
from ctypes import wintypes

import cv2
import mss
import numpy as np
from PIL import Image, ImageTk
from pynput import keyboard


ULONG_PTR = wintypes.WPARAM


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]


class INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUTUNION)]


def send_left_button(pressed):
    flags = 0x0002 if pressed else 0x0004  # LEFTDOWN / LEFTUP
    event = INPUT(type=0, union=INPUTUNION(mi=MOUSEINPUT(0, 0, 0, flags, 0, 0)))
    sent = ctypes.windll.user32.SendInput(1, ctypes.byref(event), ctypes.sizeof(INPUT))
    if sent != 1:
        raise ctypes.WinError()


def focus_roblox_window():
    """Focus the Roblox window and move the pointer into its client area."""
    user32 = ctypes.windll.user32
    candidates = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def collect(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            length = user32.GetWindowTextLengthW(hwnd)
            if length:
                title = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, title, length + 1)
                if "roblox" in title.value.lower() and "auto fish" not in title.value.lower():
                    candidates.append(hwnd)
        return True

    user32.EnumWindows(collect, 0)
    if not candidates:
        return False
    hwnd = candidates[0]
    user32.ShowWindow(hwnd, 9)
    focused = bool(user32.SetForegroundWindow(hwnd))

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    class RECT(ctypes.Structure):
        _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                    ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

    client, pointer = RECT(), POINT()
    if user32.GetClientRect(hwnd, ctypes.byref(client)) and user32.GetCursorPos(ctypes.byref(pointer)):
        user32.ScreenToClient(hwnd, ctypes.byref(pointer))
        if not (0 <= pointer.x < client.right and 0 <= pointer.y < client.bottom):
            destination = POINT(client.right // 2, client.bottom // 2)
            user32.ClientToScreen(hwnd, ctypes.byref(destination))
            user32.SetCursorPos(destination.x, destination.y)
    return focused


class RegionPicker:
    def __init__(self, root):
        self.root = root
        self.box = None
        self.image = None
        with mss.mss() as sct:
            shot = np.array(sct.grab(sct.monitors[1]))[:, :, :3]
        shot = cv2.cvtColor(shot, cv2.COLOR_BGR2RGB)
        self.image = ImageTk.PhotoImage(Image.fromarray(shot))
        self.win = tk.Toplevel(root)
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-topmost", True)
        self.canvas = tk.Canvas(self.win, cursor="crosshair", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_image(0, 0, image=self.image, anchor="nw")
        self.canvas.create_text(20, 20, anchor="nw", text="Drag around both bars and the cast oval's movement area; Escape cancels",
                                fill="yellow", font=("Segoe UI", 18, "bold"))
        self.start = None
        self.rect = None
        self.canvas.bind("<ButtonPress-1>", self.down)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.up)
        self.win.bind("<Escape>", lambda _e: self.win.destroy())

    def down(self, e):
        self.start = (e.x, e.y)
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#00ff00", width=3)

    def drag(self, e):
        if self.start:
            self.canvas.coords(self.rect, *self.start, e.x, e.y)

    def up(self, e):
        if not self.start:
            return
        x1, y1 = self.start
        left, top = min(x1, e.x), min(y1, e.y)
        width, height = abs(e.x - x1), abs(e.y - y1)
        if width < 80 or height < 120:
            messagebox.showinfo("Select a larger area", "Include both fishing bars and the full area where the cast oval moves.", parent=self.win)
            return
        self.box = {"left": left, "top": top, "width": width, "height": height}
        self.win.destroy()


class FishingHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("Zenon")
        self.root.geometry("480x520")
        self.root.resizable(False, False)
        self.bg = "#0b1220"
        self.card = "#111e30"
        self.card_alt = "#1a2b40"
        self.text = "#f1f7fb"
        self.muted = "#9db0c2"
        self.accent = "#35d6c0"
        self.root.configure(bg=self.bg)
        self.region = None
        self.active = False
        self.thread = None
        self.held = False
        self.movement_speed_value = 1.0
        self.deadband_percent_value = 8
        self.detection_sensitivity_value = 5
        self.status = tk.StringVar(value="Choose your fishing area to begin.")
        header = tk.Frame(root, bg=self.bg)
        header.pack(fill="x", padx=20, pady=(18, 8))
        badge = tk.Label(header, text="Z", width=3, height=2, bg=self.accent,
                         fg="#08221f", font=("Bahnschrift SemiBold", 18))
        badge.pack(side="left", padx=(0, 12))
        brand = tk.Frame(header, bg=self.bg)
        brand.pack(side="left", anchor="center")
        tk.Label(brand, text="ZENON", fg=self.text, bg=self.bg,
                 font=("Bahnschrift SemiBold", 21)).pack(anchor="w")
        tk.Label(brand, text="FISHING ASSISTANT", fg=self.muted, bg=self.bg,
                 font=("Bahnschrift SemiBold", 9)).pack(anchor="w", pady=(1, 0))
        tk.Label(header, text="AUTO", fg=self.accent, bg=self.card,
                 font=("Bahnschrift SemiBold", 9), padx=10, pady=5).pack(side="right")

        intro = tk.Label(root, text="Keep the bobber in the orange range. The green bar shows catch progress.",
                         fg=self.muted, bg=self.bg, wraplength=430, justify="left",
                         font=("Segoe UI", 9))
        intro.pack(fill="x", padx=22, pady=(0, 8))

        area_card = tk.Frame(root, bg=self.card, padx=16, pady=14)
        area_card.pack(fill="x", padx=18, pady=7)
        tk.Label(area_card, text="FISHING AREA", font=("Bahnschrift SemiBold", 9),
                 fg=self.accent, bg=self.card).pack(anchor="w")
        self.region_label = tk.StringVar(value="No screen area selected")
        tk.Label(area_card, textvariable=self.region_label, fg=self.text, bg=self.card,
                 font=("Segoe UI", 10)).pack(anchor="w", pady=(6, 10))
        area_buttons = tk.Frame(area_card, bg=self.card)
        area_buttons.pack(fill="x")
        tk.Button(area_buttons, text="Choose area", width=16, command=self.pick,
                  bg=self.card_alt, fg=self.text, activebackground="#27405a",
                  activeforeground=self.text, relief="flat",
                  font=("Bahnschrift SemiBold", 10), pady=8).pack(side="left", padx=(0, 9))
        self.toggle = tk.Button(area_buttons, text="Start fishing", width=19,
                                command=self.toggle_run, state="disabled",
                                bg=self.accent, fg="#08221f", activebackground="#57e5d2",
                                activeforeground="#08221f", disabledforeground="#617b7a",
                                relief="flat", font=("Bahnschrift SemiBold", 10), pady=8)
        self.toggle.pack(side="left")

        key_card = tk.Frame(root, bg=self.card, padx=16, pady=13)
        key_card.pack(fill="x", padx=18, pady=7)
        tk.Label(key_card, text="KEYBINDS", font=("Bahnschrift SemiBold", 9),
                 fg=self.accent, bg=self.card).pack(anchor="w", pady=(0, 8))
        key_row = tk.Frame(key_card, bg=self.card)
        key_row.pack(fill="x")
        self.start_key = keyboard.Key.f8
        self.stop_key = keyboard.Key.esc
        self.capture_binding = None
        self.start_key_label = tk.StringVar(value="Start key: F8")
        self.stop_key_label = tk.StringVar(value="Stop key: ESC")
        self.start_key_button = tk.Button(key_row, textvariable=self.start_key_label,
                                          width=18, command=lambda: self.begin_key_capture("start"),
                                          bg=self.card_alt, fg=self.text, activebackground="#27405a",
                                          activeforeground=self.text, relief="flat",
                                          font=("Bahnschrift SemiBold", 9), pady=8)
        self.start_key_button.pack(side="left", padx=4)
        self.stop_key_button = tk.Button(key_row, textvariable=self.stop_key_label,
                                         width=18, command=lambda: self.begin_key_capture("stop"),
                                         bg=self.card_alt, fg=self.text, activebackground="#27405a",
                                         activeforeground=self.text, relief="flat",
                                         font=("Bahnschrift SemiBold", 9), pady=8)
        self.stop_key_button.pack(side="left", padx=4)
        status_card = tk.Frame(root, bg=self.card, padx=14, pady=12)
        status_card.pack(fill="x", padx=18, pady=(7, 3))
        tk.Label(status_card, text="STATUS", font=("Bahnschrift SemiBold", 9),
                 fg=self.accent, bg=self.card).pack(anchor="w", pady=(0, 5))
        tk.Label(status_card, textvariable=self.status, wraplength=400, fg=self.text,
                 bg=self.card, font=("Segoe UI", 9), justify="left").pack(anchor="w")
        tk.Label(root, text="Click a key to change it   •   Keep Roblox focused while fishing",
                 font=("Segoe UI", 8), fg=self.muted, bg=self.bg).pack(side="bottom", pady=10)
        self.active_overlay = tk.Toplevel(root)
        self.active_overlay.overrideredirect(True)
        self.active_overlay.configure(bg="#0b1220")
        self.active_overlay.attributes("-topmost", True)
        tk.Label(self.active_overlay, text="●  ZENON ACTIVE", bg="#0b1220", fg="#35d6c0",
                 font=("Bahnschrift SemiBold", 11), padx=14, pady=8).pack()
        overlay_x = max(0, self.root.winfo_screenwidth() - 180)
        self.active_overlay.geometry(f"150x40+{overlay_x}+36")
        self.active_overlay.withdraw()
        self.active_overlay.update_idletasks()
        self.make_overlay_clickthrough()
        self.key_listener = keyboard.Listener(on_press=self.key_pressed)
        self.key_listener.start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def make_overlay_clickthrough(self):
        """Let Roblox receive mouse input through the small active badge."""
        user32 = ctypes.windll.user32
        hwnd = self.active_overlay.winfo_id()
        user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
        user32.GetWindowLongW.restype = wintypes.LONG
        user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
        user32.SetWindowLongW.restype = wintypes.LONG
        style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
        flags = 0x00080000 | 0x00000020 | 0x00000080 | 0x08000000
        user32.SetWindowLongW(hwnd, -20, style | flags)

    def show_active_overlay(self, visible):
        if visible:
            self.active_overlay.deiconify()
            self.active_overlay.attributes("-topmost", True)
            self.active_overlay.lift()
        else:
            self.active_overlay.withdraw()

    def key_pressed(self, key):
        if self.capture_binding:
            binding = self.capture_binding
            self.capture_binding = None
            self.root.after(0, self.assign_key, binding, key)
        elif key == self.start_key:
            self.root.after(0, self.toggle_run)
        elif key == self.stop_key:
            self.root.after(0, self.stop)

    @staticmethod
    def key_name(key):
        if isinstance(key, keyboard.Key):
            return key.name.upper()
        return (key.char or "?").upper()

    def begin_key_capture(self, binding):
        self.capture_binding = binding
        self.status.set(f"Press the key you want to use for {binding}.")

    def assign_key(self, binding, key):
        other = self.stop_key if binding == "start" else self.start_key
        if key == other:
            self.status.set("Start and stop keys must be different. Choose another key.")
            return
        if binding == "start":
            self.start_key = key
            self.start_key_label.set(f"Start key: {self.key_name(key)}")
        else:
            self.stop_key = key
            self.stop_key_label.set(f"Stop key: {self.key_name(key)}")
        self.status.set("Keybind updated.")

    def pick(self):
        self.stop()
        picker = RegionPicker(self.root)
        self.root.wait_window(picker.win)
        if picker.box:
            self.region = picker.box
            self.region_label.set(f"Selected: {picker.box['width']} × {picker.box['height']} pixels")
            self.toggle.configure(state="normal")
            self.status.set("Ready. Include both bars and the cast oval's movement area.")

    def detect(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        sensitivity = self.detection_sensitivity_value
        orange = cv2.inRange(
            hsv,
            np.array([max(0, int(5 - (sensitivity - 5) * 0.5)),
                      max(45, int(90 - (sensitivity - 5) * 6)),
                      max(45, int(80 - (sensitivity - 5) * 6))]),
            np.array([min(35, int(30 + (sensitivity - 5) * 0.6)), 255, 255]))
        contours, _ = cv2.findContours(orange, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        _, w = frame.shape[:2]
        zones = []
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            if cv2.contourArea(c) > 250 and ch > 1.5 * cw and x < w * 0.6:
                zones.append((x, y, cw, ch))
        zone = max(zones, key=lambda item: item[3]) if zones else None

        # The white circular fish marker sits inside the dark bar on the left.
        white = cv2.inRange(
            hsv, np.array([0, 0, max(145, int(185 - (sensitivity - 5) * 7))]),
            np.array([179, min(130, int(100 + (sensitivity - 5) * 5)), 255]))
        white[:, int(w * 0.58):] = 0
        white = cv2.morphologyEx(white, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        contours, _ = cv2.findContours(white, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        fish = []
        for c in contours:
            area = cv2.contourArea(c)
            x, y, cw, ch = cv2.boundingRect(c)
            if 120 < area < 10000 and 0.4 < cw / max(ch, 1) < 2.2 and x < w * 0.58:
                moments = cv2.moments(c)
                if moments["m00"] and zone:
                    center_x = moments["m10"] / moments["m00"]
                    if abs(center_x - (zone[0] + zone[2] / 2)) < max(35, zone[2]):
                        fish.append(int(moments["m01"] / moments["m00"]))
        marker = int(np.median(fish)) if fish else None
        target = (zone[1], zone[1] + zone[3]) if zone else None
        return marker, target

    def detect_cast_ready(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        sensitivity = self.detection_sensitivity_value
        mask = cv2.inRange(
            hsv,
            np.array([max(55, int(68 - (sensitivity - 5) * 1.5)),
                      max(35, int(85 - (sensitivity - 5) * 7)),
                      max(100, int(145 - (sensitivity - 5) * 8))]),
            np.array([min(110, int(100 + (sensitivity - 5) * 1.5)), 255, 255]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE,
                                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 250 or area > 30000:
                continue
            x, y, width, height = cv2.boundingRect(contour)
            ratio = width / max(height, 1)
            perimeter = cv2.arcLength(contour, True)
            circularity = 4 * np.pi * area / (perimeter * perimeter) if perimeter else 0
            if 1.15 <= ratio <= 3.5 and circularity >= 0.20:
                return True
        return False

    def toggle_run(self):
        if self.active:
            self.stop()
        elif self.region:
            focused = focus_roblox_window()
            self.active = True
            self.toggle.configure(text="Stop fishing")
            self.status.set("Fishing active." if focused else "Fishing active; Roblox window not found.")
            self.show_active_overlay(True)
            self.thread = threading.Thread(target=self.loop, daemon=True)
            self.thread.start()

    def loop(self):
        last_status = 0
        pulse_until = 0.0
        control_cooldown_until = 0.0
        cast_click_cooldown_until = 0.0
        cast_cue_latched = False
        cast_cue_missing_since = None
        previous_marker = None
        previous_time = None
        velocity = 0.0
        input_pulses = 0
        try:
            with mss.mss() as sct:
                while self.active:
                    frame = np.array(sct.grab(self.region))[:, :, :3]
                    marker, target = self.detect(frame)
                    now = time.monotonic()

                    if self.detect_cast_ready(frame):
                        cast_cue_missing_since = None
                        if not cast_cue_latched and now >= cast_click_cooldown_until:
                            try:
                                if self.held:
                                    send_left_button(False)
                                    self.held = False
                                send_left_button(True)
                                time.sleep(0.060)
                                send_left_button(False)
                                input_pulses += 1
                                cast_cue_latched = True
                                cast_click_cooldown_until = time.monotonic() + 4.0
                                self.root.after(0, self.status.set,
                                                "Cast cue detected • click sent")
                            except OSError as exc:
                                self.root.after(0, self.status.set, f"Cast click failed: {exc}")
                                self.active = False
                                continue
                    elif cast_cue_latched:
                        if cast_cue_missing_since is None:
                            cast_cue_missing_since = now
                        elif now - cast_cue_missing_since >= 0.70:
                            cast_cue_latched = False
                            cast_cue_missing_since = None

                    if self.held and now >= pulse_until:
                        send_left_button(False)
                        self.held = False
                        control_cooldown_until = now + 0.010

                    if marker is not None and target is not None:
                        top, bottom = target
                        orange_midpoint = (top + bottom) / 2
                        band_height = max(1, bottom - top)
                        deadband = max(2, int(band_height * self.deadband_percent_value / 100))
                        if previous_marker is not None and previous_time is not None:
                            elapsed = max(0.001, now - previous_time)
                            velocity = max(-1200.0, min(1200.0,
                                                       (marker - previous_marker) / elapsed))
                        predicted_y = marker + velocity * 0.10
                        error = predicted_y - orange_midpoint
                        previous_marker, previous_time = marker, now
                        wants_hold = error < 0  # holding lowers; releasing raises
                        outside = abs(error) > deadband
                        if outside and wants_hold and not self.held and now >= control_cooldown_until:
                            distance = abs(error) - deadband
                            duration = max(0.035, min(0.650,
                                                      (0.040 + distance * 0.00120)
                                                      * self.movement_speed_value))
                            try:
                                send_left_button(True)
                                input_pulses += 1
                                self.held = True
                                pulse_until = now + duration
                            except OSError as exc:
                                self.root.after(0, self.status.set, f"Mouse input failed: {exc}")
                                self.active = False
                        elif (not outside or not wants_hold) and self.held:
                            send_left_button(False)
                            self.held = False
                            control_cooldown_until = now + 0.002

                        if time.time() - last_status > 0.5:
                            state = "DOWN" if self.held else "UP"
                            self.root.after(0, self.status.set,
                                            f"Fishing active • LMB {state} • {input_pulses} inputs")
                            last_status = time.time()
                    else:
                        previous_marker, previous_time, velocity = None, None, 0.0
                        if self.held:
                            send_left_button(False)
                            self.held = False
                        if time.time() - last_status > 0.5:
                            self.root.after(0, self.status.set,
                                            "Watching for bobber, orange range, or cast cue…")
                            last_status = time.time()
                    time.sleep(0.010)
        except OSError as exc:
            self.root.after(0, self.status.set, f"Mouse input failed: {exc}")
            self.active = False
        except Exception as exc:
            self.root.after(0, self.status.set, f"Fishing stopped: {exc}")
            self.active = False
        finally:
            if self.held:
                try:
                    send_left_button(False)
                finally:
                    self.held = False
            self.root.after(0, self.finish_run)

    def finish_run(self):
        if not self.active:
            self.show_active_overlay(False)
            self.toggle.configure(text="Start fishing")

    def stop(self):
        self.active = False
        self.show_active_overlay(False)
        if self.held:
            send_left_button(False)
            self.held = False
        self.toggle.configure(text="Start fishing")
        if self.region:
            self.status.set("Stopped.")

    def close(self):
        self.stop()
        self.key_listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    app_root = tk.Tk()
    FishingHelper(app_root)
    app_root.mainloop()
