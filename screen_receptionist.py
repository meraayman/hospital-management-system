"""Receptionist dashboard.

- Browse doctors by specialization and see their shifts
- Book a real appointment in a free 30-minute slot
- Register new patients (or reuse an existing one by National ID)
- View / cancel booked appointments
- Reserve room beds for patients and discharge them
"""
from datetime import date, datetime
from tkinter import Frame, Label, Button, StringVar, OptionMenu
from tkinter import messagebox, ttk

import ttkthemes

import db
from config import PRIMARY, BUTTON, TEXT, LIGHT
from ui_helpers import (load_image, make_table, fill_table, selected_values, style_tables,
                        form_entry, run_db, FAILED)

TILE = dict(bd=0, bg=LIGHT, font=("Roboto", 24, "bold"), cursor="hand2", fg=TEXT)


class ReceptionistDashboard:
    def __init__(self, receptionist_id, receptionist_name):
        self.receptionist_id = receptionist_id
        self.action = None

        self.window = ttkthemes.ThemedTk()
        self.window.set_theme("breeze")
        self.window.geometry("1920x1080")
        self.window.title(f"MBA Hospital Dashboard - Receptionist ({receptionist_name})")
        self.window.config(bg=PRIMARY)
        style_tables()

        # Images (kept on self so Tk doesn't garbage-collect them)
        self.logo = load_image(self.window, "Logo.png", (140, 115))
        self.back_img = load_image(self.window, "back_color.png", (30, 30))
        self.logout_img = load_image(self.window, "Log out button.png", (30, 30))

        Label(self.window, image=self.logo, bg=PRIMARY).place(x=30, y=30)
        Label(self.window, text=f"Welcome, {receptionist_name}", font=("Roboto", 22, "bold"),
              bg=PRIMARY, fg="white").place(x=350, y=120)
        Button(self.window, image=self.logout_img, bd=0, bg=PRIMARY, activebackground=PRIMARY,
               cursor="hand2", command=self.logout).place(x=1420, y=70)

        # Left menu
        left = Frame(self.window, bg=PRIMARY)
        left.place(x=0, y=200, width=293, height=252)
        for i, (text, cmd) in enumerate([("Home", self.home),
                                         ("Doctors", self.specializations),
                                         ("Booked Appointments", self.booked_appointments),
                                         ("Rooms", self.rooms)]):
            Button(left, text=text, font=("Roboto", 14, "bold"), width=20, fg=TEXT, bg="white",
                   cursor="hand2", command=cmd).place(x=0, y=50 + 50 * i)

        # Right panel where every page is drawn
        self.right = Frame(self.window, bg="white")
        self.right.place(x=350, y=200, width=1110, height=630)

        self.home()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def logout(self):
        self.action = "logout"
        self.window.destroy()

    def new_page(self, title, back=None):
        for widget in self.right.winfo_children():
            widget.destroy()
        Label(self.right, text=title, font=("Roboto", 24, "bold"),
              bg="white", fg=TEXT).place(x=50, y=40)
        if back:
            Button(self.right, image=self.back_img, bd=0, bg="white", activebackground="white",
                   cursor="hand2", command=back).place(x=1040, y=40)

    def patient_form(self):
        """Draw the patient fields and return a dict of widgets."""
        f = {
            "name": form_entry(self.right, 100, 150, "Full Name"),
            "address": form_entry(self.right, 100, 220, "Address"),
            "national_id": form_entry(self.right, 100, 290, "National ID", width=20),
            "email": form_entry(self.right, 100, 360, "Email"),
            "phone": form_entry(self.right, 500, 220, "Phone Number"),
            "birth": form_entry(self.right, 500, 290, "Birth Date (YYYY-MM-DD)"),
            "gender": StringVar(value="Gender"),
        }
        menu = OptionMenu(self.right, f["gender"], "Male", "Female")
        menu.config(width=10, font=("Roboto", 14), bg=LIGHT, fg=TEXT, bd=0, highlightthickness=0)
        menu.place(x=500, y=150)

        def find():
            nid = f["national_id"].value()
            if not nid:
                messagebox.showwarning("National ID", "Type a National ID first.")
                return
            patient = run_db(db.get_patient, nid)
            if patient is FAILED:
                return
            if not patient:
                messagebox.showinfo("New patient", "No patient with this ID yet.\n"
                                                   "Fill in the form to register them.")
                return
            name, gender, birth, phone, email, _nid, address = patient
            f["name"].set_value(name)
            f["gender"].set(gender or "Gender")
            f["birth"].set_value(birth)
            f["phone"].set_value(phone)
            f["email"].set_value(email)
            f["address"].set_value(address)

        Button(self.right, text="Find", bd=0, bg=BUTTON, fg="white", font=("Roboto", 12, "bold"),
               cursor="hand2", width=6, command=find).place(x=345, y=292)
        return f

    def ensure_patient(self, f):
        """Return (national_id, name) for an existing or newly registered patient, or None."""
        nid = f["national_id"].value()
        if not nid:
            messagebox.showerror("Missing data", "National ID is required.")
            return None

        existing = run_db(db.get_patient, nid)
        if existing is FAILED:
            return None
        if existing:
            return nid, existing[0]

        # New patient -> validate everything
        name, address = f["name"].value(), f["address"].value()
        phone, email, birth = f["phone"].value(), f["email"].value(), f["birth"].value()
        gender = f["gender"].get()

        if not all([name, address, phone, birth]) or gender not in ("Male", "Female"):
            messagebox.showerror("Missing data", "New patient: please fill in name, gender, address, "
                                                 "phone number and birth date.")
            return None
        if not nid.isdigit():
            messagebox.showerror("Invalid National ID", "National ID must contain digits only.")
            return None
        if not phone.replace("+", "").isdigit():
            messagebox.showerror("Invalid phone", "Phone number must contain digits only.")
            return None
        try:
            if datetime.strptime(birth, "%Y-%m-%d").date() > date.today():
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter a valid birth date in YYYY-MM-DD format.")
            return None

        if run_db(db.add_patient, name, gender, birth, phone, email, nid, address) is FAILED:
            return None
        return nid, name

    # ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------
    def home(self):
        self.new_page("Dashboard")
        Button(self.right, text="Doctors", command=self.specializations, **TILE)\
            .place(x=50, y=150, width=300, height=200)
        Button(self.right, text="Booked\nAppointments", command=self.booked_appointments, **TILE)\
            .place(x=400, y=150, width=300, height=200)
        Button(self.right, text="Rooms", command=self.rooms, **TILE)\
            .place(x=750, y=150, width=300, height=200)

    def specializations(self):
        self.new_page("Specialities", back=self.home)
        specs = run_db(db.get_specializations)
        if specs is FAILED:
            return
        for i, (spec_id, spec_name) in enumerate(specs):
            Button(self.right, text=spec_name,
                   command=lambda s=spec_id, n=spec_name: self.doctors(s, n), **TILE)\
                .place(x=50 + (i % 3) * 350, y=150 + (i // 3) * 230, width=300, height=200)

    def doctors(self, spec_id, spec_name):
        self.new_page(f"Available Doctors - {spec_name}", back=self.specializations)
        Label(self.right, text="Double-click a doctor's shift to book an appointment",
              font=("Roboto", 13), bg="white", fg=TEXT).place(x=50, y=85)

        table = make_table(self.right, [
            ("doctor_id", "Doctor ID", 100),
            ("doctor_name", "Doctor Name", 250),
            ("start", "Shift Start", 150),
            ("end", "Shift End", 150),
        ], x=100, y=130, width=900, height=400)

        rows = run_db(db.get_doctor_shifts, spec_id)
        if rows is FAILED:
            return
        fill_table(table, [(r[0], r[1], db.fmt_time(r[2]), db.fmt_time(r[3])) for r in rows])

        def on_double_click(_event):
            values = selected_values(table)
            if values:
                self.book_appointment(values, spec_id, spec_name)

        table.bind("<Double-1>", on_double_click)

    def book_appointment(self, doctor_row, spec_id, spec_name):
        doctor_id, doctor_name, shift_start, shift_end = doctor_row
        self.new_page("Book Appointment", back=lambda: self.doctors(spec_id, spec_name))
        Label(self.right, text=f"{doctor_name}  ·  shift {shift_start} - {shift_end}   "
                               f"(existing patient? type the National ID and press Find)",
              font=("Roboto", 13), bg="white", fg=TEXT).place(x=50, y=90)

        f = self.patient_form()

        # Slot picker
        Label(self.right, text="Appointment", font=("Roboto", 16, "bold"),
              bg="white", fg=TEXT).place(x=100, y=420)
        day_entry = form_entry(self.right, 100, 460, "Date (YYYY-MM-DD)", width=18)
        day_entry.set_value(date.today().isoformat())

        slot_var = StringVar()
        slot_box = ttk.Combobox(self.right, textvariable=slot_var, state="readonly",
                                width=16, font=("Roboto", 13))
        slot_box.place(x=500, y=463)
        slot_map = {}

        def read_day():
            try:
                day = datetime.strptime(day_entry.value(), "%Y-%m-%d").date()
            except ValueError:
                messagebox.showerror("Invalid Date", "Appointment date must be YYYY-MM-DD.")
                return None
            if day < date.today():
                messagebox.showerror("Invalid Date", "You can't book an appointment in the past.")
                return None
            return day

        def load_slots():
            slot_map.clear()
            slot_var.set("")
            slot_box["values"] = ()
            day = read_day()
            if not day:
                return
            slots = run_db(db.get_free_slots, int(doctor_id), shift_start, shift_end, day)
            if slots is FAILED:
                return
            for start, end in slots:
                slot_map[f"{db.fmt_time(start)} - {db.fmt_time(end)}"] = (start, end)
            slot_box["values"] = list(slot_map)
            if slot_map:
                slot_box.current(0)
            else:
                messagebox.showinfo("No free slots", "This shift is fully booked (or already over) "
                                                     "on that date. Try another date.")

        Button(self.right, text="Show Free Slots", bd=0, bg=BUTTON, fg="white",
               font=("Roboto", 12, "bold"), cursor="hand2", command=load_slots).place(x=330, y=462)

        def save():
            day = read_day()
            if not day:
                return
            if slot_var.get() not in slot_map:
                messagebox.showerror("No slot", "Press 'Show Free Slots' and choose a time first.")
                return
            patient = self.ensure_patient(f)
            if not patient:
                return
            nid, patient_name = patient
            start, end = slot_map[slot_var.get()]
            if not messagebox.askyesno("Confirm booking",
                                       f"Book {patient_name} with {doctor_name}\n"
                                       f"on {day} at {slot_var.get()}?"):
                return
            try:
                appt_id = db.book_appointment(int(doctor_id), nid, patient_name, day, start, end)
            except db.BookingError as err:
                messagebox.showwarning("Not booked", str(err))
                load_slots()
                return
            except Exception as err:
                messagebox.showerror("Database Error", str(err))
                return
            messagebox.showinfo("Booked", f"Appointment #{appt_id} booked successfully!")
            self.booked_appointments()

        Button(self.right, text="Book", bd=0, bg=BUTTON, fg="white", font=("Roboto", 14, "bold"),
               cursor="hand2", width=10, height=1, command=save).place(x=950, y=550)

        load_slots()

    def booked_appointments(self):
        self.new_page("Booked Appointments", back=self.home)
        table = make_table(self.right, [
            ("id", "ID", 60),
            ("date", "Date", 120),
            ("patient_id", "Patient ID", 160),
            ("patient", "Patient Name", 170),
            ("doctor_id", "Doctor ID", 90),
            ("doctor", "Doctor Name", 180),
            ("start", "Start", 90),
            ("end", "End", 90),
        ], x=50, y=100, width=1000, height=440)

        def load():
            rows = run_db(db.get_all_appointments)
            if rows is FAILED:
                return
            fill_table(table, [(r[0], str(r[1]), r[2], r[3], r[4], r[5],
                                db.fmt_time(r[6]), db.fmt_time(r[7])) for r in rows])

        def cancel():
            values = selected_values(table)
            if not values:
                messagebox.showwarning("Select", "Select an appointment first.")
                return
            if messagebox.askyesno("Cancel appointment",
                                   f"Cancel appointment #{values[0]} for {values[3]}?"):
                if run_db(db.cancel_appointment, values[0]) is not FAILED:
                    load()

        Button(self.right, text="Cancel Selected", bd=0, bg="#c0392b", fg="white",
               font=("Roboto", 13, "bold"), cursor="hand2", command=cancel).place(x=880, y=560)
        load()

    def rooms(self):
        self.new_page("Rooms", back=self.home)
        Label(self.right, text="Double-click a room to reserve a bed or discharge a patient",
              font=("Roboto", 13), bg="white", fg=TEXT).place(x=50, y=85)
        table = make_table(self.right, [
            ("room", "Room Number", 120),
            ("address", "Location", 230),
            ("beds", "Beds", 70),
            ("occupied", "Occupied", 100),
            ("free", "Free Beds", 100),
            ("people", "People Allowed", 140),
            ("start", "Start Time", 110),
            ("end", "End Time", 110),
        ], x=50, y=130, width=1000, height=440)

        rows = run_db(db.get_rooms)
        if rows is FAILED:
            return
        fill_table(table, [(r[0], r[1], r[2], r[3], int(r[2]) - int(r[3]), r[4],
                            db.fmt_time(r[5]), db.fmt_time(r[6])) for r in rows])

        def on_double_click(_event):
            values = selected_values(table)
            if values:
                self.room_details(int(values[0]))

        table.bind("<Double-1>", on_double_click)

    def room_details(self, room_number):
        room = run_db(db.get_room, room_number)
        if room is FAILED or room is None:
            return
        _num, address, beds, occupied = room[0], room[1], int(room[2]), int(room[3])
        self.new_page(f"Room {room_number}", back=self.rooms)
        Label(self.right, text=f"{address}  ·  {beds} bed(s)  ·  {occupied} occupied  ·  "
                               f"{beds - occupied} free",
              font=("Roboto", 13), bg="white", fg=TEXT).place(x=50, y=90)

        f = self.patient_form()

        # Current occupants
        Label(self.right, text="Patients in this room", font=("Roboto", 16, "bold"),
              bg="white", fg=TEXT).place(x=100, y=410)
        table = make_table(self.right, [
            ("res", "Res. ID", 80),
            ("nid", "National ID", 170),
            ("name", "Patient Name", 220),
            ("in", "Check-in", 180),
        ], x=100, y=445, width=700, height=150)
        occupants = run_db(db.get_room_occupants, room_number)
        if occupants is not FAILED:
            fill_table(table, [(r[0], r[1], r[2], str(r[3])[:16]) for r in occupants])

        def discharge():
            values = selected_values(table)
            if not values:
                messagebox.showwarning("Select", "Select a patient in the table first.")
                return
            if messagebox.askyesno("Discharge", f"Discharge {values[2]} from room {room_number}?"):
                if run_db(db.discharge, values[0]) is not FAILED:
                    self.room_details(room_number)

        def reserve():
            if occupied >= beds:
                messagebox.showwarning("Room full", "All beds in this room are taken.")
                return
            patient = self.ensure_patient(f)
            if not patient:
                return
            nid, patient_name = patient
            if not messagebox.askyesno("Confirm", f"Reserve a bed in room {room_number} for {patient_name}?"):
                return
            try:
                db.reserve_room(room_number, nid)
            except db.BookingError as err:
                messagebox.showwarning("Not reserved", str(err))
                return
            except Exception as err:
                messagebox.showerror("Database Error", str(err))
                return
            messagebox.showinfo("Reserved", f"{patient_name} is now in room {room_number}.")
            self.room_details(room_number)

        Button(self.right, text="Discharge", bd=0, bg="#c0392b", fg="white", font=("Roboto", 13, "bold"),
               cursor="hand2", width=10, command=discharge).place(x=830, y=450)
        Button(self.right, text="Reserve", bd=0, bg=BUTTON, fg="white", font=("Roboto", 14, "bold"),
               cursor="hand2", width=10, height=1, command=reserve).place(x=950, y=550)


def run(receptionist_id, receptionist_name):
    """Open the dashboard. Returns 'logout' if the receptionist logged out."""
    app = ReceptionistDashboard(receptionist_id, receptionist_name)
    app.window.mainloop()
    return app.action
