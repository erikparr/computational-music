import tkinter as tk
from pythonosc import dispatcher, osc_server
from circle_fifths import CircleOfFifths
from music_theory import MusicTheory
from key_color import KeyColorManager
import threading


class PianoApp:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=1400, height=400)
        self.canvas.pack()

        # Assuming CircleOfFifths needs a canvas, you might need to create another canvas for it
        self.circle_canvas = tk.Canvas(root, width=1400, height=100)
        self.circle_canvas.pack()

        # Initialize the CircleOfFifths
        self.circle_of_fifths = CircleOfFifths(
            self.circle_canvas, self.on_key_selected)
        self.currently_KeyColorManager_notes = []

        self.scale_selection_setup()

        # Initialize key lists as empty lists
        self.white_keys = []
        self.black_keys = []

        # Initialize keyboard size and related attributes before drawing the piano
        # Default to 88 keys, you can adjust this as needed
        self.set_keyboard_size(61)
        self.key_color_manager = KeyColorManager(
            self.canvas, self.white_keys, self.black_keys, self.starting_midi_note)

        self.setup_osc()

    def draw_piano(self):
        self.canvas.delete("all")  # Clear existing keys before redrawing

        # Constants for key dimensions remain the same
        self.white_key_width = 30
        self.white_key_height = 180
        self.black_key_width = 22
        self.black_key_height = 100

        # Draw white keys based on the updated count
        self.white_keys = []
        for i in range(self.white_keys_count):
            x0 = i * self.white_key_width
            key = self.canvas.create_rectangle(
                x0, 0, x0 + self.white_key_width, self.white_key_height, fill="white", outline="black")
            self.white_keys.append(key)

        # Draw black keys considering the updated count and pattern
        self.black_keys = []
        # Correct offsets for black keys within an octave
        black_keys_offsets = [0, 1, 3, 4, 5]

        for i in range(self.white_keys_count):
            if i % 7 in black_keys_offsets:  # Adjust this line to match the correct offsets
                # Correcting position for first two black keys in a set
                if (i % 7 == 0 or i % 7 == 1) and i + 1 < self.white_keys_count:
                    x0 = (i * self.white_key_width) + \
                        self.white_key_width - (self.black_key_width / 2)
                elif i + 2 < self.white_keys_count:  # Correcting position for the next three black keys in a set
                    x0 = (i * self.white_key_width) + \
                        self.white_key_width - (self.black_key_width / 2)
                else:
                    continue  # Skip if the current position would place a black key beyond the keyboard's range
                key = self.canvas.create_rectangle(
                    x0, 0, x0 + self.black_key_width, self.black_key_height, fill="black", outline="black")
                self.black_keys.append(key)

    def scale_selection_setup(self):
        # Define the list of scales to be included in the dropdown, excluding abstract classes
        self.scale_list = ["MinorScale",
             "DorianScale", "HarmonicMinorScale",
            "LydianScale", "OctatonicScale", "SieveScale", "RagMarwa", "MelodicMinorScale", "ChromaticScale",
            "MixolydianScale", "PhrygianScale", "WholeToneScale"
        ]
        self.current_scale = tk.StringVar(value="MajorScale")  # Default scale
        self.scale_dropdown = tk.OptionMenu(
            self.root, self.current_scale, "MajorScale", *self.scale_list, command=self.on_scale_selected)
        self.scale_dropdown.pack()

    def on_scale_selected(self, selection):
        old_scale = self.current_scale.get()
        self.current_scale.set(selection)
        print(f"Scale changed from {old_scale} to {selection}")
        self.visualize_scale_on_keyboard()

    def set_keyboard_size(self, size):
        if size not in (61, 76, 88):
            raise ValueError(
                "Invalid keyboard size. Only 61, 76, and 88 keys are supported.")
        self.keyboard_size = size
        self.adjust_keyboard_parameters()

    def adjust_keyboard_parameters(self):
        if self.keyboard_size == 61:
            self.starting_midi_note = 36  # C2 for 61-key
        elif self.keyboard_size == 76:
            self.starting_midi_note = 28  # E1 for 76-key
        elif self.keyboard_size == 88:
            self.starting_midi_note = 21  # A0 for 88-key

        self.white_keys_count = {61: 36, 76: 45, 88: 52}[self.keyboard_size]
        self.black_keys_count = {61: 25, 76: 33, 88: 36}[self.keyboard_size]
        self.draw_piano()  # Redraw piano with new settings
        if hasattr(self, 'key_color_manager'):
            self.key_color_manager.update_keys(
                self.white_keys, self.black_keys)

    def on_key_selected(self, selected_key):
        # Default to 'None' if not previously set
        old_key = getattr(self, 'current_key', 'None')
        self.current_key = selected_key
        print(f"Key changed from {old_key} to {selected_key}")
        self.reset_keyboard_colors()

        # Calculate the MIDI notes for the current scale and key
        scale_notes = MusicTheory.get_scale_notes(selected_key, self.current_scale.get())
        midi_notes = self.convert_scale_notes_to_midi(scale_notes, selected_key)

        # Update the KeyColorManager with the current scale's MIDI notes
        self.key_color_manager.highlighted_keys = set(midi_notes)

        # Visualize the selected scale on the keyboard
        self.visualize_scale_on_keyboard()

    def KeyColorManager_keys_for_notes(self, midi_notes):
        # Ensure previous highlights are cleared
        self.key_color_manager.reset_highlighted_keys()

        # Debugging output
        print(
            f"Debug: Highlighting MIDI notes across the keyboard: {midi_notes}")

        # Highlight keys for all MIDI notes
        for midi_note in midi_notes:
            self.key_color_manager.highlight_key(midi_note)

    def reset_keyboard_colors(self):
        for key in self.white_keys:
            self.canvas.itemconfig(key, fill='white')
        for key in self.black_keys:
            self.canvas.itemconfig(key, fill='black')

    def setup_osc(self):
        # Setup the dispatcher
        disp = dispatcher.Dispatcher()
        disp.map("/keyOn", self.key_on_handler)
        disp.map("/keyOff", self.key_off_handler)

        # Setup the OSC server
        server = osc_server.ThreadingOSCUDPServer(('127.0.0.1', 57121), disp)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.start()

    def key_on_handler(self, unused_addr, *args):
        print(f"Key On Message Received: {args}")
        midi_number = args[1] if args else None
        if midi_number is not None:
            print(f"Processing Key On for MIDI: {midi_number}")
            self.root.after(0, self.activate_key, midi_number)

    def key_off_handler(self, unused_addr, *args):
        print(f"Key Off Message Received: {args}")
        midi_number = args[1] if args else None
        if midi_number is not None:
            print(f"Processing Key Off for MIDI: {midi_number}")
            self.root.after(0, self.deactivate_key, midi_number)

    def update_keys(self, white_keys, black_keys):
        self.white_keys = white_keys
        self.black_keys = black_keys

    def activate_key(self, midi_number):
        self.key_color_manager.activate_key(midi_number)

    def deactivate_key(self, midi_number):
        self.key_color_manager.deactivate_key(midi_number)

    def find_key_index(self, midi_number):
        if midi_number in self.get_midi_numbers_for_black_keys():
            index = self.get_midi_numbers_for_black_keys().index(midi_number)
            # Debugging statement
            print(
                f"Debug: MIDI {midi_number} is a black key at index {index}.")
            return index, True
        elif midi_number in self.get_midi_numbers_for_white_keys():
            index = self.get_midi_numbers_for_white_keys().index(midi_number)
            # Debugging statement
            print(
                f"Debug: MIDI {midi_number} is a white key at index {index}.")
            return index, False
        # This could indicate a range issue or logic error
        print(f"Debug: MIDI {midi_number} not found.")
        return None, None

    def get_midi_numbers_for_white_keys(self):
        return [i for i in range(self.starting_midi_note, self.starting_midi_note + 88) if i % 12 in [0, 2, 4, 5, 7, 9, 11]]

    def get_midi_numbers_for_black_keys(self):
        return [i for i in range(self.starting_midi_note, self.starting_midi_note + 88) if i % 12 in [1, 3, 6, 8, 10]]

    def visualize_scale_on_keyboard(self):
        if not hasattr(self, 'current_key') or not self.current_key:
            self.current_key = 'C'

        scale_type = self.current_scale.get()
        scale_notes = MusicTheory.get_scale_notes(self.current_key, scale_type)
        midi_notes = self.convert_scale_notes_to_midi(scale_notes, self.current_key)

        # This line might be redundant if the highlighted keys are already updated in on_key_selected
        # self.key_color_manager.highlighted_keys = set(midi_notes)

        self.KeyColorManager_keys_for_notes(midi_notes)


    def convert_scale_notes_to_midi(self, scale_notes, key):
        all_midi_numbers = []
        # Calculate the start MIDI for the key
        start_midi = self.calculate_start_midi_for_key(key, self.starting_midi_note)
        end_midi = self.starting_midi_note + self.keyboard_size - 1

        for midi_num in range(start_midi, end_midi + 1):
            if midi_num % 12 in scale_notes:
                all_midi_numbers.append(midi_num)

        print(f"Debug: Correctly generated MIDI numbers for {key} scale: {all_midi_numbers}")
        return all_midi_numbers

    def calculate_start_midi_for_key(self, key, starting_midi_note):
        # Find the first note of the scale that matches or exceeds the starting MIDI note
        key_offset = MusicTheory.key_signature_map.get(key, 0)
        # Calculate the lowest possible MIDI number for this key that is within the keyboard's range
        lowest_possible_note = (starting_midi_note - key_offset) % 12 + key_offset
        start_midi = starting_midi_note if starting_midi_note >= lowest_possible_note else lowest_possible_note + 12
        return start_midi

# Create the main window
root = tk.Tk()
root.title("88-Key Piano with OSC")

# Create the piano app
app = PianoApp(root)

# Run the application
root.mainloop()
