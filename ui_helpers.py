"""Small reusable UI pieces shared by all screens."""
import os
from tkinter import Entry, Frame, Scrollbar, HORIZONTAL, VERTICAL, BOTTOM, RIGHT, X, Y, BOTH, CENTER
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from config import IMG_DIR, TEXT, LIGHT

FAILED = object()  # returned by run_db when the database call failed


def load_image(master, filename, size):
    """Open an image from the Images folder, resize it and make it Tk-ready."""
    img = Image.open(os.path.join(IMG_DIR, filename)).resize(size)
    return ImageTk.PhotoImage(img, master=master)


def run_db(func, *args):
    """Call a db function and show a friendly error box if MySQL fails."""
    try:
        return func(*args)
    except Exception as err:  # mysql.connector.Error, connection refused, etc.
        messagebox.showerror("Database Error", f"Could not reach the database:\n\n{err}")
        return FAILED


class PlaceholderEntry(Entry):
    """Entry with grey hint text that disappears when you click in it.

    Use .value() to read what the user typed ('' if they typed nothing).
    """

    def __init__(self, master, placeholder, is_password=False, **kwargs):
        super().__init__(master, **kwargs)
        self.placeholder = placeholder
        self.is_password = is_password
        self._placeholder_on = False
        self.reset()
        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def reset(self):
        self.delete(0, "end")
        self.config(show="")
        self.insert(0, self.placeholder)
        self._placeholder_on = True

    def set_value(self, text):
        if text in (None, ""):
            self.reset()
            return
        self.delete(0, "end")
        self.config(show="*" if self.is_password else "")
        self.insert(0, str(text))
        self._placeholder_on = False

    def value(self):
        return "" if self._placeholder_on else self.get().strip()

    def _on_focus_in(self, _event):
        if self._placeholder_on:
            self.delete(0, "end")
            self._placeholder_on = False
            if self.is_password:
                self.config(show="*")

    def _on_focus_out(self, _event):
        if not self.get():
            self.reset()


def form_entry(parent, x, y, placeholder, width=25):
    """Grey input box used on the receptionist forms."""
    entry = PlaceholderEntry(parent, placeholder, width=width, fg=TEXT, border=0,
                             bg=LIGHT, font=("Roboto", 14))
    entry.place(x=x, y=y, height=35)
    return entry


def style_tables():
    style = ttk.Style()
    style.configure("Treeview", font=("Helvetica", 12), rowheight=30,
                    background="white", fieldbackground="lightgray")
    style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"))


def make_table(parent, columns, x, y, width, height):
    """Create a scrollable table.

    columns: list of (key, heading, column_width)
    """
    frame = Frame(parent, bg="white")
    frame.place(x=x, y=y, width=width, height=height)

    scroll_x = Scrollbar(frame, orient=HORIZONTAL)
    scroll_y = Scrollbar(frame, orient=VERTICAL)
    table = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings",
                         xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)
    scroll_x.config(command=table.xview)
    scroll_y.config(command=table.yview)
    scroll_x.pack(side=BOTTOM, fill=X)
    scroll_y.pack(side=RIGHT, fill=Y)
    table.pack(fill=BOTH, expand=True)

    for key, heading, col_width in columns:
        table.heading(key, text=heading)
        table.column(key, width=col_width, anchor=CENTER)

    table.tag_configure("oddrow", background="lightblue")
    table.tag_configure("evenrow", background="white")
    return table


def fill_table(table, rows):
    table.delete(*table.get_children())
    for index, row in enumerate(rows):
        tag = "oddrow" if index % 2 == 0 else "evenrow"
        table.insert("", "end", values=row, tags=(tag,))


def selected_values(table):
    """Values of the highlighted row, or None."""
    item = table.focus()
    if not item:
        return None
    return table.item(item, "values")
