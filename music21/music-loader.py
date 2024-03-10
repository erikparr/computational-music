# music21_module.py
from music21 import *
from keyboard_listener import KeyboardListener
from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import BlockingOSCUDPServer
import tkinter as tk
from tkinter import filedialog, Tk, Button
import time
import threading

env = environment.Environment()
env['musescoreDirectPNGPath'] = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'
env['musicxmlPath'] = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'

# All the existing function definitions remain the same...


class Music21Module:
    def __init__(self, master):
        self.master = master
        self.client = self.initialize_osc_client()
        self.score = None
        self.playing = False
        self.stop_playback_flag = False
        self.current_chord_index = 0
        self.scrub_mode_var = tk.BooleanVar(self.master)  # Use self.master
        self.prev_chord = None  # Initialize previous chord variable
        self.instrument_stave_map = {}  # Step 2: Initialize the mapping
        self.selected_instrument = None  # Initialize selected_instrument
        self.keyboard_listener = KeyboardListener()
        # Add this to the create_widgets method
        self.chord_listener_var = tk.BooleanVar()
        self.chord_listener_toggle = tk.Checkbutton(
        self.master, text="Chord Listener", variable=self.chord_listener_var, command=self.toggle_chord_listener)
        self.chord_listener_toggle.pack()

        self.create_widgets()

    def create_widgets(self):
        self.load_button = Button(
            self.master, text="Load Score", command=self.load_score)
        self.load_button.pack()

        self.play_button = Button(
            self.master, text="Play Score", command=self.toggle_play_score)
        self.play_button.pack()

        self.chords_button = Button(
            self.master, text="Play Chords", command=self.toggle_play_chords)
        self.chords_button.pack()
        chords_button = Button(
            self.master, text="Get All Chords", command=self.get_chords)
        chords_button.pack()
        save_button = Button(
            self.master, text="Save Chords to MusicXML", command=self.save_chords)
        save_button.pack()
        self.scrub_mode_var = tk.BooleanVar()
        self.scrub_mode_toggle = tk.Checkbutton(
            self.master, text="Scrub Mode", variable=self.scrub_mode_var, command=self.toggle_scrub_mode)
        self.scrub_mode_toggle.pack()
        # Toggle for sending OSC messages for chords
        self.send_osc_var = tk.BooleanVar()
        self.send_osc_toggle = tk.Checkbutton(
            self.master, text="Send Chord", variable=self.send_osc_var)
        self.send_osc_toggle.pack()
        # Inside the create_widgets method of Music21Module class
        self.morph_chords_var = tk.BooleanVar()
        self.morph_chords_toggle = tk.Checkbutton(
            self.master, text="Morph Chords", variable=self.morph_chords_var)
        self.morph_chords_toggle.pack()
        # Toggle for filtering duplicate chords
        self.filter_duplicates_var = tk.BooleanVar()
        self.filter_duplicates_toggle = tk.Checkbutton(
            self.master, text="Filter Duplicate Chords", variable=self.filter_duplicates_var)
        self.filter_duplicates_toggle.pack()

        self.combine_staves_button = Button(
            self.master, text="Combine Staves", command=self.process_combined_staves)
        self.combine_staves_button.pack()

    def process_combined_staves(self):
        """Process the combination of staves, extract chords, and filter duplicates if specified."""
        combined_stream = self.combine_staves_for_instrument(
            self.selected_instrument)
        if combined_stream:
            # Pass filter_duplicates_var directly to extract_chords_from_stream
            chords = self.extract_chords_from_stream(
                combined_stream, self.filter_duplicates_var.get())
            self.chords = chords  # Prepare for scrubbing
            self.current_chord_index = 0  # Reset index for scrubbing
            for chord in chords:
                print(chord)
        else:
            print("No applicable combined process.")

    def toggle_scrub_mode(self):
        if self.scrub_mode_var.get():
            self.master.bind("<Right>", self.scrub_forward)
            self.master.bind("<Left>", self.scrub_backward)
        else:
            self.master.unbind("<Right>")
            self.master.unbind("<Left>")

    def toggle_chord_listener(self):
        if self.chord_listener_var.get():
            self.keyboard_listener.start_listening()
            print("Chord Listener enabled.")
        else:
            self.keyboard_listener.stop_listening()
            print("Chord Listener disabled.")

    def send_chord_on(self, chord):
        midi_numbers = [note.pitch.midi for note in chord]
        if self.send_osc_var.get():
            self.client.send_message("/chordOn", midi_numbers)

    def send_key_on(self, channel, midi_number):
        self.client.send_message("/keyOnPlay", [channel, midi_number])

    def send_key_off(self, channel, midi_number):
        self.client.send_message("/keyOffPlay", [channel, midi_number])

    def initialize_osc_client(self, ip='127.0.0.1', port=57120):
        return udp_client.SimpleUDPClient(ip, port)

    def scrub_forward(self, event=None):
        if self.scrub_mode_var.get() and hasattr(self, 'chords') and self.chords:
            self.current_chord_index = min(
                self.current_chord_index + 1, len(self.chords) - 1)
            self.play_current_chord()

    def scrub_backward(self, event=None):
        if self.scrub_mode_var.get() and hasattr(self, 'chords') and self.chords:
            self.current_chord_index = max(self.current_chord_index - 1, 0)
            self.play_current_chord()

    def play_current_chord(self):
        if 0 <= self.current_chord_index < len(self.chords):
            chord = self.chords[self.current_chord_index]

            # Check if Morph Chords is enabled and scrub mode is active
            if not (self.morph_chords_var.get() or self.send_osc_var.get()):
                # Send key on messages only if Morph Chords is not enabled or not in scrub mode
                for note in chord:
                    midi_number = note.pitch.midi
                    self.send_key_on(0, midi_number)

            # send just the chord on message
            if self.send_osc_var.get():
                if not self.morph_chords_var.get():
                    self.send_chord_on(chord)
                    print(f"send_chord_on with {chord} is executed.")

            # Morphing logic
            if self.morph_chords_var.get() and self.prev_chord:
                morph_values = self.calculate_morph_values(
                    self.prev_chord, chord)
                self.send_chord_on(chord)  # send chord on message
                self.send_morph_values(morph_values)  # send morph values

            # Update previous chord and manage key off with a delay
            self.prev_chord = chord
            # threading.Timer(1, self.stop_current_chord, args=[chord]).start()

    def stop_current_chord(self, chord):
        for note in chord:
            midi_number = note.pitch.midi
            self.send_key_off(0, midi_number)

        # New method in Music21Module class
    def calculate_morph_values(self, prev_chord, current_chord):
        morph_values = []

        # Ensuring both chords have the same number of notes
        while len(prev_chord) < len(current_chord):
            # Duplicate the last note if necessary
            prev_chord.append(prev_chord[-1])
        while len(current_chord) < len(prev_chord):
            # Duplicate the last note if necessary
            current_chord.append(current_chord[-1])

        for prev_note, curr_note in zip(prev_chord, current_chord):
            difference = curr_note.pitch.midi - prev_note.pitch.midi

            # If the difference is more than an octave, abort the operation
            if abs(difference) > 12:
                return []

            # Map the difference to MIDI bend values
            # Mapping -12 to +12 steps to 0-16384
            bend_value = int(8192 + (difference * 682.6666666666666))
            morph_values.append(bend_value)

        return morph_values

    def send_morph_values(self, morph_values):
        if morph_values:
            self.client.send_message("/morphNotes", morph_values)

    def load_and_display_score(self, work_name):
        try:
            score = converter.parse(work_name).makeNotation()
            score.show()
            return score
        except musicxml.m21ToXml.MusicXMLExportException as e:
            print(f"Error loading file: {e}")
            return None

    def get_all_chords(self, score):
        chords = []
        for part in score.parts:
            for measure in part.getElementsByClass('Measure'):
                for element in measure.notesAndRests:
                    if element.isChord:
                        chords.append(element)
        return chords

    def save_chords_to_musicxml(self, chords, file_path):
        score = stream.Score()
        part = stream.Part()
        for ch in chords:
            new_chord = chord.Chord(ch.pitches)
            part.append(new_chord)
        score.append(part)
        score.write('musicxml', file_path)

    def toggle_play_score(self):
        if self.playing:
            self.stop_playback()
        else:
            if self.score:
                self.playing = True
                self.stop_playback_flag = False
                self.update_button_text()
                threading.Thread(target=self.play_score).start()

    def toggle_play_chords(self):
        if self.playing:
            self.stop_playback()
        else:
            if hasattr(self, 'chords'):
                self.playing = True
                self.update_button_text()
                # Start the play_chords method in a separate thread
                threading.Thread(target=self.play_chords_thread).start()

    def stop_playback(self):
        self.stop_playback_flag = True  # Set the flag to signal the playback thread to stop
        self.playing = False
        self.master.after(0, self.update_button_text)

    def update_button_text(self):
        if self.playing:
            self.play_button.config(text="Stop")
            self.chords_button.config(text="Stop")
        else:
            self.play_button.config(text="Play Score")
            self.chords_button.config(text="Play Chords")

    def clear(self):
        self.canvas.delete("all")

    def load_score(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("MusicXML files", "*.mxl"), ("MIDI files", "*.mid")])
        if file_path:
            self.score = self.load_and_display_score(file_path)
            self.analyze_score(self.score)

    def extract_metadata(self, score):
        # Initialize default metadata values
        metadata_info = {
            'title': "Unknown Title",
            'composer': "Unknown Composer"
        }

        # Check if metadata is available
        if score.metadata:
            # Attempt to access standard metadata fields
            metadata_info['title'] = score.metadata.title or metadata_info['title']
            metadata_info['composer'] = score.metadata.composer or metadata_info['composer']

            # Attempt to access alternative fields or custom metadata
            if not metadata_info['title'] or not metadata_info['composer']:
                for field in ['alternativeTitle', 'movementName']:
                    if getattr(score.metadata, field, None):
                        metadata_info['title'] = getattr(score.metadata, field)
                        break

                # Accessing custom or less common composer fields
                composers = score.metadata.getContributorsByRole('composer')
                if composers:
                    metadata_info['composer'] = ', '.join(
                        [str(c) for c in composers])

        return metadata_info

    def analyze_score(self, score):
        if not score:
            print("No score loaded to analyze.")
            return

        # Extract and print basic score information
        metadata = self.extract_metadata(score)
        print(f"Title: {metadata['title']}")
        print(f"Composer: {metadata['composer']}")

        # Key Signature Analysis
        key = score.analyze('key')
        print(f"Estimated key: {key}")

        # Time Signatures
        time_signatures = set()
        for elem in score.recurse().getElementsByClass('TimeSignature'):
            time_signatures.add(str(elem))
        print(f"Time signatures used: {', '.join(time_signatures)}")

        # Tempos
        tempos = set()
        for elem in score.recurse().getElementsByClass('MetronomeMark'):
            tempos.add(f"{elem.number} BPM")
        print(f"Tempos found: {', '.join(tempos)}")

        # Parts and Instruments Analysis
        print("Parts and Instruments:")
        for part in score.parts:
            instr = part.getInstrument()
            instrument_name = instr.instrumentName or "Unknown Instrument"
            print(f"- {part.partName or 'Part'}: {instrument_name}")

            # Initialize pitch range variables
            lowest_pitch = None
            highest_pitch = None

            # Iterate over all notes and chords to calculate pitch range
            for element in part.recurse().notesAndRests:
                pitches = []
                if element.isNote:
                    pitches = [element.pitch]
                elif element.isChord:
                    pitches = element.pitches

                for pitch in pitches:
                    if not lowest_pitch or pitch < lowest_pitch:
                        lowest_pitch = pitch
                    if not highest_pitch or pitch > highest_pitch:
                        highest_pitch = pitch

            if lowest_pitch and highest_pitch:
                print(f"  Pitch range: {lowest_pitch} to {highest_pitch}")
            else:
                print("  Pitch range: N/A")

            # Assuming each Part as one staff unless explicitly divided
            print("  Number of staves: 1")  # Simplified assumption

        # Additional analyses...
        # Total Measures
        total_measures = max([len(p.getElementsByClass('Measure'))
                             for p in score.parts])
        print(f"Total measures: {total_measures}")

        # Duration
        total_duration = score.duration
        print(f"Total duration: {total_duration.quarterLength} quarter notes")

        # Dynamics
        dynamics = set()
        for elem in score.recurse().getElementsByClass('Dynamic'):
            dynamics.add(str(elem.value))
        print(f"Dynamics used: {', '.join(dynamics)}")

        self.instrument_stave_map = self.catalog_instruments(score)

    def catalog_instruments(self, score):
        instrument_stave_map = {}
        first_instrument_set = False  # Flag to check if the first instrument is already set

        for part in score.parts:
            instrument_name = str(part.getInstrument())
            if instrument_name not in instrument_stave_map:
                instrument_stave_map[instrument_name] = [part]
                if not first_instrument_set:
                    self.selected_instrument = instrument_name
                    first_instrument_set = True
                    print(
                        f"Default selected instrument set to: {self.selected_instrument}")
            else:
                instrument_stave_map[instrument_name].append(part)

        return instrument_stave_map

    def play_score(self):
        if self.score:
            channel = 0  # Default MIDI channel
            for part in self.score.parts:
                for measure in part.getElementsByClass('Measure'):
                    if self.stop_playback_flag:
                        return  # Exit early if stop flag is set
                    for element in measure.notesAndRests:
                        duration = element.duration.quarterLength
                        if element.isNote:
                            midi_number = element.pitch.midi
                            self.send_key_on(channel, midi_number)
                            time.sleep(duration)
                            self.send_key_off(channel, midi_number)
                        elif element.isChord:
                            for note in element:
                                midi_number = note.pitch.midi
                                self.send_key_on(channel, midi_number)
                            time.sleep(duration)
                            for note in element:
                                midi_number = note.pitch.midi
                                self.send_key_off(channel, midi_number)
                        elif element.isRest:
                            time.sleep(duration)

    def extract_chords_from_stream(self, stream, filter_duplicates=False):
        """Extract chords from a given music21 stream and optionally filter duplicates.
        Only include chords that consist of 2 or more notes."""
        chords = []
        seen_chords = set()  # For filtering duplicates

        for element in stream.recurse():
            if isinstance(element, chord.Chord) and len(element) >= 2:  # Check for 2 or more notes
                # Construct a chord signature for duplicate checking
                chord_signature = tuple(n.pitch.midi for n in element)
                if filter_duplicates:
                    if chord_signature not in seen_chords:
                        chords.append(element)
                        seen_chords.add(chord_signature)
                else:
                    chords.append(element)

        return chords

    def combine_staves_for_instrument(self, instrument_name):
        """Combine staves for the specified instrument into a single stream."""
        if instrument_name in self.instrument_stave_map and len(self.instrument_stave_map[instrument_name]) > 1:
            combined_score = stream.Score()
            for part in self.instrument_stave_map[instrument_name]:
                combined_score.insert(0, part)
            return combined_score.chordify()
        else:
            print(f"No multiple streams to combine for {instrument_name}")
            return None

    def get_chords_from_stream(self, combined_stream):
        # Use the chordify() method to convert the combined stream into a series of chords
        chordified_stream = combined_stream.chordify()

        # Initialize a list to hold the extracted chords
        chords = []

        # Iterate through the elements in the chordified stream, including measures and their contents
        for element in chordified_stream.recurse():
            # Check if the element is a chord
            if isinstance(element, chord.Chord):
                chords.append(element)
                # Debug: Confirm when chords are found
                print(f"Chord extracted: {element}")

        # Debug: Summary of chords found
        print(f"Total chords extracted: {len(chords)}")
        return chords

    def get_chords(self):
        if self.score:
            chords = self.get_all_chords(self.score)

            if self.filter_duplicates_var.get():
                chords = self.filter_duplicate_chords(chords)
            self.chords = chords
            self.current_chord_index = 0  # Reset the index whenever a new score is loaded

    def filter_duplicate_chords(self, chords):
        unique_chords = []
        seen_chords = set()

        for chord in chords:
            chord_signature = self.get_chord_signature(chord)
            if chord_signature not in seen_chords:
                unique_chords.append(chord)
                seen_chords.add(chord_signature)

        return unique_chords

    def get_chord_signature(self, chord):
        return tuple(n.pitch.midi for n in chord)

    def play_chords_thread(self):
        # This method will be used to handle the chord playing in a separate thread
        if hasattr(self, 'chords'):
            self.play_chords()

    # Modification in the play_chords method
    def play_chords(self):
        prev_chord = None
        for chord in self.chords:
            # [Existing code to play the chord...]

            if self.morph_chords_var.get() and prev_chord:
                morph_values = self.calculate_morph_values(prev_chord, chord)
                self.send_morph_values(morph_values)

            prev_chord = chord  # Update the previous chord for the next iteration
            if self.stop_playback_flag:
                break

    def save_chords(self):
        if hasattr(self, 'chords'):
            file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[
                                                    ("MusicXML files", "*.xml")])
            if file_path:
                self.save_chords_to_musicxml(self.chords, file_path)

# Additional functions


# Running the module standalone
if __name__ == "__main__":
    root = Tk()
    app = Music21Module(root)
    root.mainloop()
