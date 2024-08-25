from pynput import keyboard
from pynput.keyboard import Key, Listener
import subprocess

class ScriptController:
    def __init__(self, script_name):
        self.script_name = script_name
        self.process = None

    def start_script(self):
        if self.process is None:
            self.process = subprocess.Popen(['python', self.script_name], creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            print(f"{self.script_name} is already running.")

    def terminate_script(self):
        try:
            if self.process:
                print(f"Terminating {self.script_name}...")
                self.process.terminate()  # Terminate the process
                self.process = None
            else:
                print(f"{self.script_name} is not running.")
        except Exception as e:
            print(f"Error terminating script: {e}")

# Configure logging to save keypresses to a file
press_state = 0
ui_opened = False

def on_press(key):
    global press_state
    global ui_opened
    try:
        if key == Key.ctrl_l:
            press_state = 1
        if f'{key.char}' == "\x08" and press_state == 1:
            if ui_opened:
                ui_opened = False
                controller.terminate_script()
            else:
                ui_opened = True
                controller.start_script()

    except AttributeError:
        pass

def on_release(key):
    global press_state
    if key == Key.esc:
        # Stop listener
        return False
    if key == Key.ctrl_l:
        press_state = 0


# Set up the listener for keyboard events
with Listener(on_press=on_press, on_release=on_release) as listener:
    controller = ScriptController('wolfare_ui.py')
    listener.join()
