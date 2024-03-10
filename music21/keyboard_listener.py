import threading
from collections import deque
import time
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer

class KeyboardListener:
    def __init__(self, port=50000, chord_duration=1):
        self.port = port
        self.chord_duration = chord_duration
        self.liveChords = deque()
        self.currentChordNotes = []
        self.dispatcher = Dispatcher()
        self.dispatcher.map("/keyOn", self.key_on_handler)
        self.server = BlockingOSCUDPServer(('127.0.0.1', self.port), self.dispatcher)
        self.listening = False
        self.chordTimer = None

    def key_on_handler(self, address, *args):
        note = args[0]  # Assuming the first arg is the MIDI note number
        print(f"Note received: {note}")
        if not self.currentChordNotes:
            # Start timer on receiving the first note of a chord
            self.start_chord_timer()
        self.currentChordNotes.append(note)

    def start_chord_timer(self):
        if self.chordTimer:
            self.chordTimer.cancel()
        self.chordTimer = threading.Timer(self.chord_duration, self.finalize_chord)
        self.chordTimer.start()

    def finalize_chord(self):
        chord = list(self.currentChordNotes)  # Copy current notes to form a chord
        self.liveChords.append(chord)
        print(f"New chord: {chord}, Live Chords Size: {len(self.liveChords)}")
        self.currentChordNotes.clear()

    def start_listening(self):
        if not self.listening:
            self.listening = True
            threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
        self.server.serve_forever()

    def stop_listening(self):
        if self.listening:
            self.server.shutdown()
            self.listening = False
