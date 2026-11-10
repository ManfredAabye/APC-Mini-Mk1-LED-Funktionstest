import sys
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import mido


class APCMiniTester:

    def __init__(self, root):

        self.root = root

        self.root.title("APC Mini Mk1 LED Tester")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        self.colors = {
            "GRUEN": 1,
            "ROT": 3,
            "GELB": 5,
            "BLINKEN_GRUEN": 2,
        }

        self.matrix_pads = list(range(64))
        self.right_buttons = list(range(64, 72))
        self.bottom_buttons = list(range(82, 90))

        self.all_led_notes = (
            self.matrix_pads +
            self.right_buttons +
            self.bottom_buttons
        )

        self.create_ui()

        self.log("=" * 60)
        self.log("APC Mini Mk1 LED Funktionstest")
        self.log("=" * 60)
        self.log(f"Python: {sys.version.split()[0]}")
        self.log(f"Mido: {getattr(mido, '__version__', 'Unbekannt')}")

        self.scan_devices()

    def xy_to_note(self, x, y):
        return y * 8 + x

    def create_ui(self):

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except Exception:
            pass

        header = ttk.Label(
            self.root,
            text="APC Mini Mk1 LED Funktionstest",
            font=("Segoe UI", 18, "bold")
        )

        header.pack(pady=10)

        port_frame = ttk.Frame(self.root)
        port_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(
            port_frame,
            text="MIDI-Ausgang:"
        ).pack(side="left", padx=5)

        self.port_var = tk.StringVar()

        self.port_combo = ttk.Combobox(
            port_frame,
            textvariable=self.port_var,
            state="readonly"
        )

        self.port_combo.pack(
            side="left",
            fill="x",
            expand=True,
            padx=5
        )

        ttk.Button(
            port_frame,
            text="Neu scannen",
            command=self.scan_devices
        ).pack(side="left", padx=5)

        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.start_button = ttk.Button(
            control_frame,
            text="LED-Test + Lightshow starten",
            command=self.start_test
        )

        self.start_button.pack(side="left", padx=5)

        self.progress = ttk.Progressbar(
            control_frame,
            mode="determinate"
        )

        self.progress.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10
        )

        self.log_text = tk.Text(
            self.root,
            wrap="word",
            bg="#1E1E1E",
            fg="#DCDCDC",
            insertbackground="white",
            font=("Consolas", 10)
        )

        self.log_text.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )

    def log(self, text):

        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def clear_matrix(self, outport):

        for note in range(64):

            outport.send(
                mido.Message(
                    "note_on",
                    note=note,
                    velocity=0
                )
            )

    def all_off(self, outport):

        for note in self.all_led_notes:

            outport.send(
                mido.Message(
                    "note_on",
                    note=note,
                    velocity=0
                )
            )

    def horizontal_scan(self, outport):

        for color in [1, 3, 5]:

            for x in range(8):

                self.clear_matrix(outport)

                for y in range(8):

                    outport.send(
                        mido.Message(
                            "note_on",
                            note=self.xy_to_note(x, y),
                            velocity=color
                        )
                    )

                time.sleep(0.12)

    def vertical_scan(self, outport):

        for color in [1, 3, 5]:

            for y in range(8):

                self.clear_matrix(outport)

                for x in range(8):

                    outport.send(
                        mido.Message(
                            "note_on",
                            note=self.xy_to_note(x, y),
                            velocity=color
                        )
                    )

                time.sleep(0.12)

    def checkerboard(self, outport):

        for color in [1, 3, 5]:

            for y in range(8):

                for x in range(8):

                    velocity = color if (x + y) % 2 == 0 else 0

                    outport.send(
                        mido.Message(
                            "note_on",
                            note=self.xy_to_note(x, y),
                            velocity=velocity
                        )
                    )

            time.sleep(1)

    def starfield(self, outport):

        self.clear_matrix(outport)

        for _ in range(300):

            note = random.randint(0, 63)

            color = random.choice([1, 3, 5])

            outport.send(
                mido.Message(
                    "note_on",
                    note=note,
                    velocity=color
                )
            )

            time.sleep(0.03)

            outport.send(
                mido.Message(
                    "note_on",
                    note=note,
                    velocity=0
                )
            )

    def rainbow_wave(self, outport):

        colors = [1, 3, 5]

        for _ in range(10):

            for shift in range(8):

                for y in range(8):

                    for x in range(8):

                        outport.send(
                            mido.Message(
                                "note_on",
                                note=self.xy_to_note(x, y),
                                velocity=colors[(x + shift) % 3]
                            )
                        )

                time.sleep(0.10)

    def scan_devices(self):

        try:

            outputs = mido.get_output_names() # type: ignore

            self.port_combo["values"] = outputs

            for port in outputs:

                if "apc" in port.lower() and "mini" in port.lower():

                    self.port_var.set(port)
                    break

            self.log("")
            self.log("MIDI-Ausgänge gefunden:")

            for port in outputs:
                self.log(f"  {port}")

            if not outputs:
                self.log("Keine MIDI-Ausgänge gefunden.")

        except Exception as e:

            self.log(f"MIDI-Fehler: {e}")

    def start_test(self):

        if not self.port_var.get():

            messagebox.showerror(
                "Fehler",
                "Kein MIDI-Port ausgewählt."
            )

            return

        self.start_button.config(state="disabled")

        threading.Thread(
            target=self.run_test,
            daemon=True
        ).start()

    def run_test(self):

        try:

            output_name = self.port_var.get()

            self.log("")
            self.log(f"Verbinde mit: {output_name}")

            with mido.open_output(output_name) as outport: # type: ignore

                self.log("Phase 1: Einzel-LED-Test")

                for color in [1, 3, 5]:

                    for note in self.all_led_notes:

                        outport.send(
                            mido.Message(
                                "note_on",
                                note=note,
                                velocity=color
                            )
                        )

                        time.sleep(0.012)

                        outport.send(
                            mido.Message(
                                "note_on",
                                note=note,
                                velocity=0
                            )
                        )

                self.log("Phase 2: Vollbildtest")

                for color in [1, 3, 5]:

                    for note in self.all_led_notes:

                        outport.send(
                            mido.Message(
                                "note_on",
                                note=note,
                                velocity=color
                            )
                        )

                    time.sleep(1)

                self.log("Phase 3: Blinktest")

                for note in self.all_led_notes:

                    outport.send(
                        mido.Message(
                            "note_on",
                            note=note,
                            velocity=2
                        )
                    )

                time.sleep(2)

                self.log("Animation: Horizontales Lauflicht")
                self.horizontal_scan(outport)

                self.log("Animation: Vertikales Lauflicht")
                self.vertical_scan(outport)

                self.log("Animation: Schachbrett")
                self.checkerboard(outport)

                self.log("Animation: Sternenhimmel")
                self.starfield(outport)

                self.log("Animation: Regenbogen-Welle")
                self.rainbow_wave(outport)

                self.log("LEDs ausschalten")

                self.all_off(outport)

            self.progress["value"] = 100

            self.log("")
            self.log("✅ Test erfolgreich abgeschlossen")

            messagebox.showinfo(
                "Fertig",
                "LED-Test erfolgreich beendet."
            )

        except Exception as e:

            self.log("")
            self.log(f"FEHLER: {e}")

            messagebox.showerror(
                "Fehler",
                str(e)
            )

        finally:

            self.start_button.config(state="normal")


def main():

    root = tk.Tk()

    APCMiniTester(root)

    root.mainloop()


if __name__ == "__main__":
    main()