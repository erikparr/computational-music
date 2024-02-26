import tkinter as tk
from tkinter import filedialog
from music21 import converter, duration, environment

class RepairScore:
    def __init__(self, master):
        self.master = master
        self.master.title("Repair Score")
        self.score = None
        self.create_widgets()

    def create_widgets(self):
        load_button = tk.Button(self.master, text="Load Score", command=self.load_score)
        load_button.pack()

        simplify_button = tk.Button(self.master, text="Simplify Durations", command=self.simplify_durations)
        simplify_button.pack()

        save_button = tk.Button(self.master, text="Save Score", command=self.save_score)
        save_button.pack()

    def load_score(self):
        file_path = filedialog.askopenfilename(filetypes=[("MusicXML files", "*.mxl"), ("MIDI files", "*.mid"), ("MusicXML files", "*.xml")])
        if file_path:
            self.score = converter.parse(file_path)
            print("Score loaded.")

    def simplify_durations(self):
        if self.score:
            self.simplify_score_durations(self.score)
            print("Durations simplified.")

    def simplify_score_durations(self, score):
        for part in score.parts:
            for measure in part.getElementsByClass('Measure'):
                for elem in measure.notesAndRests:
                    simplified_duration = self.simplify_duration(elem.duration)
                    elem.duration = simplified_duration

    def flatten_rhythms(self, score):
        for part in score.parts:
            for measure in part.getElementsByClass('Measure'):
                for elem in measure.notesAndRests:
                    if elem.duration.isComplex or elem.duration.tuplets:
                        # Simplify the duration to a regular rhythm
                        # This is a basic example; you might need a more sophisticated method
                        elem.duration = duration.Duration(1 / 4)  # Set to a quarter note as an example
                        
    def simplify_durations(self):
        if self.score:
            self.flatten_rhythms(self.score)
            print("Rhythms flattened.")

    def save_score(self):
        if self.score:
            file_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("MusicXML files", "*.xml")])
            if file_path:
                self.score.write('musicxml', file_path)
                print("Score saved successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = RepairScore(root)
    root.mainloop()
