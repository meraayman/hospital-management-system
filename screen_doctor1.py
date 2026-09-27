"""Doctor dashboard - a doctor only sees HIS/HER OWN appointments."""
from datetime import date
from tkinter import Frame, Label, Button

import ttkthemes

import db
from config import PRIMARY, TEXT
from ui_helpers import load_image, make_table, fill_table, style_tables, run_db, FAILED


def run(doctor_id, doctor_name):
    """Open the dashboard. Returns 'logout' if the doctor logged out."""
    window = ttkthemes.ThemedTk()
    window.set_theme("breeze")
    window.geometry("1920x1080")
    window.title(f"MBA Hospital Dashboard - {doctor_name}")
    window.config(bg=PRIMARY)
    style_tables()

    state = {"action": None}

    # Header -------------------------------------------------------------
    logo = load_image(window, "Logo.png", (140, 115))
    Label(window, image=logo, bg=PRIMARY).place(x=30, y=30)
    Label(window, text=f"Welcome, {doctor_name}", font=("Roboto", 22, "bold"),
          bg=PRIMARY, fg="white").place(x=350, y=120)

    logout_img = load_image(window, "Log out button.png", (30, 30))

    def logout():
        state["action"] = "logout"
        window.destroy()

    Button(window, image=logout_img, bd=0, bg=PRIMARY, activebackground=PRIMARY,
           cursor="hand2", command=logout).place(x=1420, y=70)

    # Right panel with the table ------------------------------------------
    right = Frame(window, bg="white")
    right.place(x=350, y=200, width=1110, height=630)

    title = Label(right, text="My Appointments", font=("Roboto", 24, "bold"), bg="white", fg=TEXT)
    title.place(x=50, y=40)
    info = Label(right, text="", font=("Roboto", 13), bg="white", fg=TEXT)
    info.place(x=50, y=85)

    table = make_table(right, [
        ("id", "ID", 70),
        ("date", "Date", 130),
        ("patient_id", "Patient ID", 170),
        ("patient", "Patient Name", 220),
        ("start", "Start Time", 120),
        ("end", "End Time", 120),
    ], x=50, y=130, width=1000, height=440)

    def load(today_only):
        day = date.today() if today_only else None
        rows = run_db(db.get_doctor_appointments, doctor_id, day)
        if rows is FAILED:
            return
        fill_table(table, [
            (r[0], str(r[1]), r[2], r[3], db.fmt_time(r[4]), db.fmt_time(r[5])) for r in rows
        ])
        title.config(text="Today's Appointments" if today_only else "All My Appointments")
        if rows:
            info.config(text=f"{len(rows)} appointment(s)")
        else:
            info.config(text="No appointments today." if today_only else "You have no appointments yet.")

    # Left menu -----------------------------------------------------------
    left = Frame(window, bg=PRIMARY)
    left.place(x=0, y=200, width=293, height=252)
    Button(left, text="Today's Appointments", cursor="hand2", font=("Roboto", 14, "bold"),
           width=20, fg=TEXT, bg="white", command=lambda: load(True)).place(x=0, y=50)
    Button(left, text="All Appointments", cursor="hand2", font=("Roboto", 14, "bold"),
           width=20, fg=TEXT, bg="white", command=lambda: load(False)).place(x=0, y=100)

    load(today_only=True)
    window.mainloop()
    return state["action"]
