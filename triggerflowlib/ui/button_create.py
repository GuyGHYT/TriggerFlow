import tkinter as tk


class Button:
    def __init__(self, root, on_lc, on_rc, text, width=10, height=5):
        self.text = text
        self.width = width
        self.height = height
        self.on_lc = on_lc
        self.on_rc = on_rc
        self.root = root

        self.button = tk.Button(
            root, text=self.text, width=self.width, height=self.height
        )
        self.button.pack()

        self.button.bind("<Button-1>", self.on_lc)
        self.button.bind("<Button-3>", self.on_rc)
