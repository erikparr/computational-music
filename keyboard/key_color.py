class KeyColorManager:
    def __init__(self, canvas, white_keys, black_keys, starting_midi_note):
        self.canvas = canvas
        self.white_keys = white_keys
        self.black_keys = black_keys
        self.default_white_key_color = 'white'
        self.default_black_key_color = 'black'
        self.highlight_color = 'blue'  # Color for highlighting keys in the current scale
        self.active_color = 'yellow'  # Color for active keys
        self.starting_midi_note = starting_midi_note
        self.highlighted_keys = set()  # Track highlighted keys by their MIDI numbers

    def highlight_key(self, midi_number, color=None):
        """Highlight a key with the given color or the default highlight color."""
        color = color or self.highlight_color  # Use provided color or default to highlight color
        index, is_black = self.find_key_index(midi_number)
        if index is not None:
            key_list = self.black_keys if is_black else self.white_keys
            self.canvas.itemconfig(key_list[index], fill=color)
            self.highlighted_keys.add(midi_number)
            
    def reset_highlighted_keys(self):
        """Reset all highlighted keys to their default color."""
        for midi_number in self.highlighted_keys:
            self.reset_key_color(midi_number)
        self.highlighted_keys.clear()

    def reset_key_color(self, midi_number):
        """Reset a key's color to its default."""
        index, is_black = self.find_key_index(midi_number)
        if index is not None:
            default_color = self.default_black_key_color if is_black else self.default_white_key_color
            key_list = self.black_keys if is_black else self.white_keys
            self.canvas.itemconfig(key_list[index], fill=default_color)

    def deactivate_key(self, midi_number):
        """Deactivate a key, ensuring it returns to its highlighted color if it was highlighted, or its default color otherwise."""
        if midi_number in self.highlighted_keys:
            # The key is part of the current scale and should remain highlighted
            self.highlight_key(midi_number, self.highlight_color)
        else:
            # The key is not part of the current scale and should revert to its default color
            self.reset_key_color(midi_number)

    def find_key_index(self, midi_number):
        """
        Finds the index of the key associated with a given MIDI number.
        
        Args:
        midi_number (int): The MIDI number of the note.

        Returns:
        tuple: (index, is_black), where index is the position of the key in its respective list
               (self.white_keys or self.black_keys), and is_black is a boolean indicating whether
               the key is black (True) or white (False).
        """
        # MIDI numbers for white keys are 0, 2, 4, 5, 7, 9, 11 modulo 12
        # MIDI numbers for black keys are 1, 3, 6, 8, 10 modulo 12
        white_key_indices = [0, 2, 4, 5, 7, 9, 11]
        black_key_indices = [1, 3, 6, 8, 10]

        midi_number_modulo = midi_number % 12
        is_black = midi_number_modulo in black_key_indices

        if is_black:
            # Calculate black key index, considering only black keys
            black_key_position = black_key_indices.index(midi_number_modulo)
            # Count how many complete sets of black keys precede this one
            complete_sets = midi_number // 12 - (self.starting_midi_note // 12)
            # Total black keys before this one = complete sets * number of black keys per octave + position in current set
            total_black_keys_before = complete_sets * len(black_key_indices) + black_key_position
            return total_black_keys_before, True
        else:
            # Similar calculation for white keys
            white_key_position = white_key_indices.index(midi_number_modulo)
            complete_sets = midi_number // 12 - (self.starting_midi_note // 12)
            total_white_keys_before = complete_sets * len(white_key_indices) + white_key_position
            return total_white_keys_before, False

    def activate_key(self, midi_number):
        """Activate a key, changing its color to active color."""
        index, is_black = self.find_key_index(midi_number)
        if index is not None:
            key_list = self.black_keys if is_black else self.white_keys
            self.canvas.itemconfig(key_list[index], fill=self.active_color)
            # Note: Do not add to highlighted_keys here as this is for active state

    # Example of updating highlighted keys when changing scale
    def change_scale(self, new_scale_notes):
        self.highlighted_keys.clear()  # Clear the current set of highlighted keys
        for note in new_scale_notes:
            # Assuming new_scale_notes is a list of MIDI numbers for the new scale
            self.highlighted_keys.add(note)  # Add the MIDI number to the highlighted set
        # You might need to refresh the keyboard visualization here

    def update_scale(self, scale_midi_numbers):
        """Update the set of highlighted keys based on the new scale."""
        self.highlighted_keys.clear()  # Clear the current highlights
        self.highlighted_keys.update(scale_midi_numbers)  # Add the new scale's MIDI numbers
        
        # Re-highlight keys based on the new scale
        for midi_number in scale_midi_numbers:
            self.highlight_key(midi_number)
        # Optionally, reset any keys that are no longer highlighted
        self.reset_non_highlighted_keys()


    def update_keys(self, white_keys, black_keys):
        """Updates the white and black keys managed by this KeyColorManager."""
        self.white_keys = white_keys
        self.black_keys = black_keys
        # Optionally, reset highlighted keys if the keyboard layout changes
        self.highlighted_keys.clear()
