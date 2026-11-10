# APC-Mini-Mk1-LED-Funktionstest

Der APC Mini Mk1 LED-Funktionstest überprüft die Funktionsfähigkeit sämtlicher LEDs des AKAI APC Mini Controllers über die MIDI-Schnittstelle. Nach dem Start wird das Gerät automatisch erkannt und eine Testsequenz ausgeführt.

Folgende Prüfungen werden durchgeführt:
```text
Einzeltest aller LEDs in den Farben Grün, Rot und Gelb
Vollflächiger Farbtest zur Kontrolle der Stromversorgung und Helligkeit
Blinktest aller LEDs
Horizontales und vertikales Lauflicht
Schachbrettmuster zur Erkennung fehlerhafter LEDs
Sternenhimmel-Effekt mit zufälligen Farbanimationen
Regenbogen-Wellenanimation
Automatisches Ausschalten aller LEDs nach Testende
```
Der Test eignet sich besonders für:
```text
Gebrauchtgeräteprüfung
Reparatur und Wartung
Qualitätskontrolle nach LED- oder Tastenreparaturen
Funktionsnachweis vor dem Verkauf
Hardware-Diagnose bei MIDI-Problemen
```
Die Software kommuniziert direkt über MIDI mit dem APC Mini Mk1 und benötigt eine installierte Python-Laufzeitumgebung oder die erstellte EXE-Version. Für den Betrieb werden die Python-Pakete mido und python-rtmidi verwendet.

Hinweis: Während des Tests sollten Ableton Live, FL Studio, Reaper oder andere MIDI-Anwendungen geschlossen sein, damit der APC Mini exklusiv verwendet werden kann.
