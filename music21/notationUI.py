import abjad

def display_chord(notes):
    # Create a chord from the list of notes
    chord = abjad.Chord(notes, (1, 4))  # Duration (1, 4) represents a quarter note

    # Create a staff and add the chord to it
    staff = abjad.Staff()
    staff.append(chord)

    # Show the staff
    abjad.show(staff)

# Example usage
notes = ["c'", "e'", "g'"]  # A C major chord in the treble clef
display_chord(notes)
