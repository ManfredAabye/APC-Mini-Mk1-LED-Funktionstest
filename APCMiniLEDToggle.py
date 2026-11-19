import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import mido


class APCMiniLEDToggle:

    def __init__(self, root):
        self.root = root
        self.root.title("APC Mini Mk1 – LED Toggle")
        self.root.geometry("900x650")
        self.root.minsize(800, 600)

        # Farb-Zyklus pro Taste: Rot -> Grün -> Gelb -> Aus -> Rot ...
        # Reihenfolge entspricht den Druck-Zuständen 0,1,2,3
        self.cycle = [3, 1, 5, 0]
        self.color_names = {3: "ROT", 1: "GRUEN", 5: "GELB", 0: "AUS"}

        # Pro Note den aktuellen Zustandsindex merken
        self.state_index = {}

        # Alle Tasten, die der APC Mini Mk1 als Eingang sendet
        self.matrix_pads = list(range(64))        # 8x8 Grid
        self.right_buttons = list(range(64, 72))  # rechte Spalte
        self.bottom_buttons = list(range(82, 90)) # untere Reihe
        self.all_buttons = (
            self.matrix_pads + self.right_buttons + self.bottom_buttons
        )

        self.running = False
        self.inport = None
        self.outport = None

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
            text="APC Mini Mk1 – LED Toggle pro Taste",
            font=("Segoe UI", 18, "bold"),
        )
        header.pack(pady=10)

        # --- Port-Auswahl Eingang ---
        in_frame = ttk.Frame(self.root)
        in_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(in_frame, text="MIDI-Eingang:").pack(side="left", padx=5)
        self.in_port_var = tk.StringVar()
        self.in_port_combo = ttk.Combobox(
            in_frame, textvariable=self.in_port_var, state="readonly"
        )
        self.in_port_combo.pack(side="left", fill="x", expand=True, padx=5)

        # --- Port-Auswahl Ausgang ---
        out_frame = ttk.Frame(self.root)
        out_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(out_frame, text="MIDI-Ausgang:").pack(side="left", padx=5)
        self.out_port_var = tk.StringVar()
        self.out_port_combo = ttk.Combobox(
            out_frame, textvariable=self.out_port_var, state="readonly"
        )
        self.out_port_combo.pack(side="left", fill="x", expand=True, padx=5)

        ttk.Button(
            in_frame, text="Neu scannen", command=self.scan_devices
        ).pack(side="left", padx=5)

        # --- Steuerung ---
        ctrl = ttk.Frame(self.root)
        ctrl.pack(fill="x", padx=10, pady=10)

        self.start_button = ttk.Button(
            ctrl, text="Listener starten", command=self.start_listener
        )
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(
            ctrl, text="Stoppen", command=self.stop_listener, state="disabled"
        )
        self.stop_button.pack(side="left", padx=5)

        ttk.Button(
            ctrl, text="Alle LEDs aus", command=self.all_off
        ).pack(side="left", padx=5)

        # --- Log ---
        self.log_text = tk.Text(
            self.root,
            wrap="word",
            bg="#1E1E1E",
            fg="#DCDCDC",
            insertbackground="white",
            font=("Consolas", 10),
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    # ------------------------------------------------------------------
    def log(self, text):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    # ------------------------------------------------------------------
    def scan_devices(self):
        try:
            inputs = mido.get_input_names()   # type: ignore
            outputs = mido.get_output_names() # type: ignore

            self.in_port_combo["values"] = inputs
            self.out_port_combo["values"] = outputs

            for port in inputs:
                if "apc" in port.lower() and "mini" in port.lower():
                    self.in_port_var.set(port)
                    break
            for port in outputs:
                if "apc" in port.lower() and "mini" in port.lower():
                    self.out_port_var.set(port)
                    break

            self.log("=" * 60)
            self.log("MIDI-Geräte")
            self.log("=" * 60)
            self.log("Eingänge:")
            for p in inputs:
                self.log(f"  {p}")
            self.log("Ausgänge:")
            for p in outputs:
                self.log(f"  {p}")
            if not inputs or not outputs:
                self.log("⚠ Keine passenden MIDI-Ports gefunden.")
        except Exception as e:
            self.log(f"MIDI-Fehler: {e}")

    # ------------------------------------------------------------------
    def start_listener(self):
        if not self.in_port_var.get() or not self.out_port_var.get():
            messagebox.showerror(
                "Fehler", "Bitte MIDI-Eingang UND -Ausgang wählen."
            )
            return

        try:
            self.inport = mido.open_input(self.in_port_var.get())   # type: ignore
            self.outport = mido.open_output(self.out_port_var.get())# type: ignore
        except Exception as e:
            messagebox.showerror("Fehler", f"Ports konnten nicht geöffnet werden:\n{e}")
            return

        self.running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.log("")
        self.log(f"Listener läuft auf: {self.in_port_var.get()}")
        self.log("Drücke eine Taste, um ihre LED weiterzuschalten.")

        threading.Thread(target=self._listen_loop, daemon=True).start()

    # ------------------------------------------------------------------
    def _listen_loop(self):
        try:
            for msg in self.inport:  # type: ignore
                if not self.running:
                    break
                self._handle_message(msg)
        except Exception as e:
            self.log(f"Listener-Fehler: {e}")
        finally:
            self._close_ports()
            self.root.after(0, self._listener_stopped)

    # ------------------------------------------------------------------
    def _handle_message(self, msg):
        # APC Mini sendet note_on mit velocity>0 beim Drücken,
        # und note_on mit velocity 0 beim Loslassen (manchmal auch note_off).
        if msg.type not in ("note_on", "note_off"):
            return

        note = msg.note
        is_press = (msg.type == "note_on" and msg.velocity > 0)

        # Wir reagieren nur auf das Drücken, nicht aufs Loslassen
        if not is_press:
            return

        # Nur Tasten, die der APC Mini als Grid/Buttons kennt
        if note not in self.all_buttons:
            return

        # Zustand weiterschalten
        idx = self.state_index.get(note, -1)
        idx = (idx + 1) % len(self.cycle)
        self.state_index[note] = idx
        velocity = self.cycle[idx]

        # LED setzen
        try:
            self.outport.send(  # type: ignore
                mido.Message("note_on", note=note, velocity=velocity)
            )
        except Exception as e:
            self.log(f"Sende-Fehler: {e}")
            return

        color_name = self.color_names[velocity]
        self.log(f"Taste {note:>3}  ->  {color_name}")

    # ------------------------------------------------------------------
    def stop_listener(self):
        self.running = False
        # inport schließen, damit die Iteration beendet wird
        if self.inport:
            try:
                self.inport.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    def _close_ports(self):
        for p in (self.inport, self.outport):
            if p:
                try:
                    p.close()
                except Exception:
                    pass
        self.inport = None
        self.outport = None

    # ------------------------------------------------------------------
    def _listener_stopped(self):
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.log("Listener gestoppt.")

    # ------------------------------------------------------------------
    def all_off(self):
        if not self.outport:
            self.log("Kein Ausgang offen – bitte Listener starten.")
            return
        try:
            for note in self.all_buttons:
                self.outport.send(
                    mido.Message("note_on", note=note, velocity=0)
                )
                self.state_index[note] = 3  # "AUS" ist Index 3
            self.log("Alle LEDs aus.")
        except Exception as e:
            self.log(f"Fehler beim Ausschalten: {e}")


# ----------------------------------------------------------------------
def main():
    root = tk.Tk()
    APCMiniLEDToggle(root)
    root.mainloop()


if __name__ == "__main__":
    main()