import tkinter as tk
import math

class CircleOfFifths:
    def __init__(self, canvas, select_key_callback=None):
        self.canvas = canvas
        self.select_key_callback = select_key_callback
        self.keys = ["C", "G", "D", "A", "E", "B", "F#", "C#", "Ab", "Eb", "Bb", "F"]
        self.draw_circle()

    def draw_circle(self):
        centerX, centerY, radius = 700, 50, 40  # Adjusted for visibility within 1400x100 canvas
        for i, key in enumerate(self.keys):
            angle = math.radians(i * 30) - math.radians(90)  # 30 degrees separation
            
            x = centerX + radius * math.cos(angle)
            y = centerY + radius * math.sin(angle)
            self.canvas.create_text(x, y, text=key, tags=("key", key))

        self.canvas.tag_bind("key", "<Button-1>", self.on_key_selected)

    def on_key_selected(self, event):
        # Find which key was clicked and notify PianoApp
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        if "key" in tags:
            key = tags[1]  # Assuming the second tag is the key name
            if self.select_key_callback:
                self.select_key_callback(key)
