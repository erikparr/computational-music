from music21 import scale, pitch

class MusicTheory:
    key_signature_map = {
        "C": 0, "G": 7, "D": 2, "A": 9, "E": 4, "B": 11, 
        "F#": 6, "Gb": 6, "Db": 1, "Ab": 8, "Eb": 3, "Bb": 10, "F": 5,
        "C#": 1,  # Adding C#
    }

    @staticmethod
    def get_notes_for_key(key_name):
        # Debugging output
        print(f"get_notes_for_key: Processing key {key_name}")
        major_scale = scale.MajorScale(key_name)
        notes = [n.pitchClass for n in major_scale.pitches]
        unique_notes = sorted(set(notes))
        print(f"get_notes_for_key: Key {key_name}, Pitch Classes: {unique_notes}")
        return unique_notes

    @staticmethod
    def get_scale_notes(key_name, scale_type):
        # Debugging output
        print(f"get_scale_notes: Processing scale {scale_type} for key {key_name}")
        scale_class = getattr(scale, scale_type, None)
        if not scale_class:
            print(f"get_scale_notes: Scale type '{scale_type}' is not recognized.")
            raise ValueError(f"Scale type '{scale_type}' is not recognized.")
        selected_scale = scale_class(key_name)
        notes = [n.pitchClass for n in selected_scale.getPitches()]
        note_names = [n.name for n in selected_scale.getPitches()]
        unique_notes = sorted(set(notes))
        print(f"get_scale_notes: Scale {scale_type} for Key: {key_name}, Pitch Classes: {unique_notes}, Note Names: {note_names}")
        return unique_notes

    @staticmethod
    def convert_notes_to_midi(key_name, note_names):
        """Converts a list of note names to their corresponding MIDI numbers based on a given key."""
        # Debugging output
        print(f"Converting note names to MIDI: {note_names} in key {key_name}")

        midi_numbers = []
        for name in note_names:
            p = pitch.Pitch(name)
            midi_numbers.append(p.midi)
        
        # Debugging: Print the MIDI numbers
        print(f"Converted MIDI numbers: {midi_numbers}")
        return midi_numbers
