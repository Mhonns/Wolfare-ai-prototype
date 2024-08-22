import subprocess
import os
import sys
import signal
from pynput.keyboard import Key, Listener

class ScriptController:
    def __init__(self, script_name):
        self.script_name = script_name
        self.process = None

    def start_script(self):
        if self.process is None:
            print(f"Starting {self.script_name}..")
            self.process = subprocess.Popen(['python3', self.script_name], preexec_fn=os.setsid)
        else:
            print(f"{self.script_name} is already running.")

    def terminate_script(self):
        try:
            if self.process:
                print(f"Terminating {self.script_name}...")
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process = None
            else:
                print(f"{self.script_name} is not running.")
        except:
            print("The main ui has already closed")

if __name__ == "__main__":
    controller = ScriptController('wolfare_ui.py')
    ui_opened = False
    press_state = 0

    def on_press(key):
        global press_state
        global ui_opened
        try:
            if key == Key.ctrl_l:
                press_state = 1
            if key.char == 'h' and press_state == 1:
                if ui_opened == False:
                    controller.start_script()
                    ui_opened = True
                else:
                    controller.terminate_script()
                    print("The main ui was closed")
                    ui_opened = False
            if key.char == '|' and press_state == 1:
                try:
                    raise SystemExit
                except SystemExit:
                    sys.exit()
        except AttributeError:
            pass
    
    def on_release(key):
        global press_state, should_show
        try:
            if key == Key.ctrl_l:
                press_state = 0
                should_show = False  # Indicate that the form should be hidden
        except AttributeError:
            pass

    with Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


