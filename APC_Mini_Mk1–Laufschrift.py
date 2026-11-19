import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import mido


# ----------------------------------------------------------------------
# 5x7-Pixel-Schrift (jeder Buchstabe als Liste von 7 Zeilen à 5 Bit)
# Bit gesetzt = Pixel an.  Reihenfolge: A-Z, 0-9, Leerzeichen, Sonderzeichen
# ----------------------------------------------------------------------
FONT = {
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "B": ["11110","10001","10001","11110","10001","10001","11110"],
    "C": ["01110","10001","10000","10000","10000","10001","01110"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "G": ["01110","10001","10000","10111","10001","10001","01111"],
    "H": ["10001","10001","10001","11111","10001","10001","10001"],
    "I": ["01110","00100","00100","00100","00100","00100","01110"],
    "J": ["00111","00010","00010","00010","00010","10010","01100"],
    "K": ["10001","10010","10100","11000","10100","10010","10001"],
    "L": ["10000","10000","10000","10000","10000","10000","11111"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "P": ["11110","10001","10001","11110","10000","10000","10000"],
    "Q": ["01110","10001","10001","10001","10101","10010","01101"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "U": ["10001","10001","10001","10001","10001","10001","01110"],
    "V": ["10001","10001","10001","10001","10001","01010","00100"],
    "W": ["10001","10001","10001","10101","10101","10101","01010"],
    "X": ["10001","10001","01010","00100","01010","10001","10001"],
    "Y": ["10001","10001","01010","00100","00100","00100","00100"],
    "Z": ["11111","00001","00010","00100","01000","10000","11111"],
    "0": ["01110","10001","10011","10101","11001","10001","01110"],
    "1": ["00100","01100","00100","00100","00100","00100","01110"],
    "2": ["01110","10001","00001","00010","00100","01000","11111"],
    "3": ["11111","00010","00100","00010","00001","10001","01110"],
    "4": ["00010","00110","01010","10010","11111","00010","00010"],
    "5": ["11111","10000","11110","00001","00001","10001","01110"],
    "6": ["00110","01000","10000","11110","10001","10001","01110"],
    "7": ["11111","00001","00010","00100","01000","01000","01000"],
    "8": ["01110","10001","10001","01110","10001","10001","01110"],
    "9": ["01110","10001","10001","01111","00001","00010","01100"],
    " ": ["00000","00000","00000","00000","00000","00000","00000"],
    "!": ["00100","00100","00100","00100","00100","00000","00100"],
    "?": ["01110","10001","00001","00010","00100","00000","00100"],
    ".": ["00000","00000","00000","00000","00000","00000","00100"],
    ",": ["00000","00000","00000","00000","00100","00100","01000"],
    "-": ["00000","00000","00000","11111","00000","00000","00000"],
    ":": ["00000","00100","00000","00000","00000","00100","00000"],
}

CHAR_W = 5      # Breite eines Zeichens
CHAR_H = 7      # Höhe eines Zeichens
SPACING = 1     # Abstand zwischen Zeichen


class APCMiniLaufschrift:

    def __init__(self, root):
        self.root = root
        self.root.title("APC Mini Mk1 – Laufschrift")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        self.running = False
        self.stop_flag = False
        self.outport = None

        # Farben (APC Mini Mk1 Velocity-Werte)
        self.color_map = {
            "GRUEN": 1,
            "GRUEN_HELL": 2,
            "ROT": 3,
            "ROT_HELL": 4,
            "GELB": 5,
            "GELB_HELL": 6,
            "ORANGE": 9,
            "BLAU": 45,
            "VIOLETT": 53,
            "WEISS": 3,   # APC Mini hat kein echtes Weiß, hier Rot als Ersatz
        }
        self.color_names = list(self.color_map.keys())

        self.matrix_pads = list(range(64))

        self.create_ui()
        self.scan_devices()

    # ------------------------------------------------------------------
    def create_ui(self):
        try:
            ttk.Style().theme_use("clam")
        except Exception:
            pass

        header = ttk.Label(
            self.root,
            text="APC Mini Mk1 – Laufschrift (8×8)",
            font=("Segoe UI", 18, "bold"),
        )
        header.pack(pady=10)

        # Text-Eingabe
        text_frame = ttk.Frame(self.root)
        text_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(text_frame, text="Text:").pack(side="left", padx=5)
        self.text_var = tk.StringVar(value="HALLO WELT")
        self.text_entry = ttk.Entry(
            text_frame, textvariable=self.text_var, font=("Consolas", 14)
        )
        self.text_entry.pack(side="left", fill="x", expand=True, padx=5)

        # Farbauswahl
        color_frame = ttk.Frame(self.root)
        color_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(color_frame, text="Farbe:").pack(side="left", padx=5)
        self.color_var = tk.StringVar(value="ROT")
        self.color_combo = ttk.Combobox(
            color_frame,
            textvariable=self.color_var,
            values=self.color_names,
            state="readonly",
            width=15,
        )
        self.color_combo.pack(side="left", padx=5)

        # Geschwindigkeit
        ttk.Label(color_frame, text="Geschwindigkeit (ms):").pack(
            side="left", padx=5
        )
        self.speed_var = tk.IntVar(value=100)
        self.speed_spin = ttk.Spinbox(
            color_frame,
            from_=20,
            to=1000,
            increment=10,
            textvariable=self.speed_var,
            width=6,
        )
        self.speed_spin.pack(side="left", padx=5)

        # Loop
        self.loop_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            color_frame, text="Endlosschleife", variable=self.loop_var
        ).pack(side="left", padx=15)

        # Port
        port_frame = ttk.Frame(self.root)
        port_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(port_frame, text="MIDI-Ausgang:").pack(side="left", padx=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(
            port_frame, textvariable=self.port_var, state="readonly"
        )
        self.port_combo.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Button(
            port_frame, text="Neu scannen", command=self.scan_devices
        ).pack(side="left", padx=5)

        # Steuerung
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill="x", padx=10, pady=10)

        self.start_button = ttk.Button(
            ctrl, text="▶ Laufschrift starten", command=self.start_scroll
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            ctrl, text="■ Stoppen", command=self.stop_scroll, state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        ttk.Button(
            ctrl, text="Alle LEDs aus", command=self.all_off
        ).pack(side="left", padx=5)

        # Log
        self.log_text = tk.Text(
            self.root,
            wrap="word",
            bg="#1E1E1E",
            fg="#DCDCDC",
            insertbackground="white",
            font=("Consolas", 10),
            height=10,
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    # ------------------------------------------------------------------
    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    # ------------------------------------------------------------------
    def scan_devices(self):
        try:
            outputs = mido.get_output_names()  # type: ignore
            self.port_combo["values"] = outputs
            for port in outputs:
                if "apc" in port.lower() and "mini" in port.lower():
                    self.port_var.set(port)
                    break
            self.log("=" * 60)
            self.log("MIDI-Ausgänge gefunden:")
            for p in outputs:
                self.log(f"  {p}")
            if not outputs:
                self.log("⚠ Keine MIDI-Ausgänge gefunden.")
        except Exception as e:
            self.log(f"MIDI-Fehler: {e}")

    # ------------------------------------------------------------------
    #  Text -> Bitmap (Liste von Spalten, jede Spalte 8 Bit hoch)
    # ------------------------------------------------------------------
    def text_to_columns(self, text, color_velocity):
        columns = []

        for ch in text.upper():
            pattern = FONT.get(ch, FONT["?"])

            for col in range(CHAR_W):
                column_pixels = []
                for y in range(8):
                    # APC-Y 0 = unten.  FONT-Zeile 0 = oben.
                    # -> FONT-Zeile "row" gehört zu APC-Y "7 - row"
                    font_row = 7 - y          # <-- DREHUNG
                    if 0 <= font_row < CHAR_H:
                        bit = pattern[font_row][col]
                        column_pixels.append(color_velocity if bit == "1" else 0)
                    else:
                        column_pixels.append(0)
                columns.append(column_pixels)

            for _ in range(SPACING):
                columns.append([0] * 8)

        for _ in range(8):
            columns.append([0] * 8)

        return columns

    # ------------------------------------------------------------------
    def render_column(self, outport, col_index, column_data):
        """Setzt eine Spalte auf dem 8x8-Grid.
        col_index: 0..7 (x-Position), column_data: 8 Velocity-Werte (y 0..7)."""
        for y in range(8):
            note = self.xy_to_note(col_index, y)
            velocity = column_data[y]
            outport.send(
                mido.Message("note_on", note=note, velocity=velocity)
            )

    # ------------------------------------------------------------------
    def xy_to_note(self, x, y):
        # APC Mini Mk1: unten-links = Note 0, Reihen von unten nach oben
        return y * 8 + x

    # ------------------------------------------------------------------
    def clear_matrix(self, outport):
        for note in range(64):
            outport.send(mido.Message("note_on", note=note, velocity=0))

    # ------------------------------------------------------------------
    def all_off(self):
        if not self.outport:
            self.log("Kein Ausgang offen – bitte zuerst starten.")
            return
        try:
            self.clear_matrix(self.outport)
            self.log("Alle LEDs aus.")
        except Exception as e:
            self.log(f"Fehler: {e}")

    # ------------------------------------------------------------------
    def start_scroll(self):
        if not self.port_var.get():
            messagebox.showerror("Fehler", "Kein MIDI-Ausgang gewählt.")
            return
        text = self.text_var.get().strip()
        if not text:
            messagebox.showerror("Fehler", "Bitte Text eingeben.")
            return

        try:
            self.outport = mido.open_output(self.port_var.get())  # type: ignore
        except Exception as e:
            messagebox.showerror("Fehler", f"Port konnte nicht geöffnet werden:\n{e}")
            return

        self.running = True
        self.stop_flag = False
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.log("")
        self.log(f"Laufschrift: '{text}'  Farbe: {self.color_var.get()}  "
                 f"Speed: {self.speed_var.get()} ms")

        threading.Thread(target=self._scroll_loop, daemon=True).start()

    # ------------------------------------------------------------------
    def _scroll_loop(self):
        try:
            color_vel = self.color_map[self.color_var.get()]
            columns = self.text_to_columns(self.text_var.get(), color_vel)
            speed = max(20, self.speed_var.get()) / 1000.0
            total = len(columns)

            while not self.stop_flag:
                for start in range(total + 8):
                    if self.stop_flag:
                        break
                    self.clear_matrix(self.outport)
                    # 8 Spalten auf dem Grid anzeigen, beginnend bei 'start'
                    for x in range(8):
                        src = start + x
                        if 0 <= src < total:
                            self.render_column(self.outport, x, columns[src])
                    time.sleep(speed)

                if not self.loop_var.get():
                    break

            self.clear_matrix(self.outport)
        except Exception as e:
            self.log(f"Fehler in Laufschrift: {e}")
        finally:
            self._close_port()
            self.root.after(0, self._scroll_stopped)

    # ------------------------------------------------------------------
    def stop_scroll(self):
        self.stop_flag = True

    # ------------------------------------------------------------------
    def _close_port(self):
        if self.outport:
            try:
                self.outport.close()
            except Exception:
                pass
        self.outport = None

    # ------------------------------------------------------------------
    def _scroll_stopped(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log("Laufschrift gestoppt.")


# ----------------------------------------------------------------------
def main():
    root = tk.Tk()
    APCMiniLaufschrift(root)
    root.mainloop()


if __name__ == "__main__":
    main()