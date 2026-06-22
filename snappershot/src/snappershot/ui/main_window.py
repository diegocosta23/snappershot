from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from snappershot.controller.main_controller import MainController


class MainWindow:

    def __init__(self):

        self.controller = MainController()

        self.root = tk.Tk()
        self.root.title("SnapperShot")
        self.root.geometry("620x360")

        ttk.Label(
            self.root,
            text="Company / Ticker",
        ).pack(pady=(20, 5))

        self.company_entry = ttk.Entry(
            self.root,
            width=35,
        )
        self.company_entry.pack()

        ttk.Button(
            self.root,
            text="Capture",
            command=self.capture,
        ).pack(pady=20)

        self.status = tk.StringVar(value="Ready")

        ttk.Label(
            self.root,
            textvariable=self.status,
        ).pack()

    def capture(self):

        company = self.company_entry.get()

        self.status.set("Working...")

        self.root.update_idletasks()

        ok = self.controller.capture_company(company)

        if ok:
            self.status.set("Finished")
            messagebox.showinfo(
                "SnapperShot",
                "Capture completed.",
            )
        else:
            self.status.set("Failed")
            messagebox.showerror(
                "SnapperShot",
                "Capture failed.",
            )

    def run(self):

        self.root.mainloop()