"""All database access for the MBA Hospital app.

Every SQL query lives here so the screens only deal with the UI.
"""
import hashlib
from datetime import date, datetime, time, timedelta

from config import DB_CONFIG, SLOT_MINUTES


class BookingError(Exception):
    """Raised when a booking breaks a business rule (slot taken, room full...)."""


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_connection():
    import mysql.connector  # imported here so the rest of the module stays importable
    return mysql.connector.connect(**DB_CONFIG)


def _fetch_all(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(buffered=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()


def _fetch_one(sql, params=()):
    rows = _fetch_all(sql, params)
    return rows[0] if rows else None


def _execute(sql, params=()):
    conn = get_connection()
    try:
        cur = conn.cursor(buffered=True)
        cur.execute(sql, params)
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Time helpers (MySQL returns TIME columns as timedelta)
# ---------------------------------------------------------------------------

def to_minutes(value):
    """Convert a TIME value (timedelta / time / 'HH:MM[:SS]') to minutes after midnight."""
    if isinstance(value, timedelta):
        return int(value.total_seconds() // 60)
    if isinstance(value, time):
        return value.hour * 60 + value.minute
    parts = str(value).split(":")
    return int(parts[0]) * 60 + int(parts[1])


def fmt_time(value):
    """Format a TIME value (or minutes) as 'HH:MM'."""
    minutes = value if isinstance(value, int) else to_minutes(value)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _sql_time(minutes):
    return f"{minutes // 60:02d}:{minutes % 60:02d}:00"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


_ROLE_TABLES = {
    "Doctor": ("doctors", "doctor_id", "doctor_name"),
    "Receptionist": ("receptionists", "receptionist_id", "receptionist_name"),
}


def authenticate(role, username, password):
    """Check the credentials ONLY in the table of the selected role.

    Returns (user_id, name) or None if the login is wrong.
    """
    table, id_col, name_col = _ROLE_TABLES[role]
    sql = f"SELECT {id_col}, {name_col} FROM {table} WHERE user_name = %s AND pass_word = %s"
    return _fetch_one(sql, (username, hash_password(password)))


# ---------------------------------------------------------------------------
# Doctors & schedules
# ---------------------------------------------------------------------------

def get_specializations():
    return _fetch_all(
        "SELECT specialization_id, specialization_name FROM specializations ORDER BY specialization_id"
    )


def get_doctor_shifts(specialization_id):
    """Rows: (doctor_id, doctor_name, start_time, end_time)."""
    return _fetch_all(
        "SELECT d.doctor_id, d.doctor_name, s.start_time, s.end_time "
        "FROM doctorschedules s JOIN doctors d ON s.doctor_id = d.doctor_id "
        "WHERE d.specialization_id = %s "
        "ORDER BY d.doctor_name, s.start_time",
        (specialization_id,),
    )


def get_free_slots(doctor_id, shift_start, shift_end, day):
    """Return free slots [(start_min, end_min), ...] for a doctor's shift on a given day."""
    start, end = to_minutes(shift_start), to_minutes(shift_end)
    booked = [
        (to_minutes(s), to_minutes(e))
        for s, e in _fetch_all(
            "SELECT start_time, end_time FROM appointments "
            "WHERE doctor_id = %s AND appointment_date = %s",
            (doctor_id, day.isoformat()),
        )
    ]

    # Don't offer slots that already started today
    earliest = -1
    if day == date.today():
        now = datetime.now()
        earliest = now.hour * 60 + now.minute

    slots = []
    t = start
    while t + SLOT_MINUTES <= end:
        slot_end = t + SLOT_MINUTES
        overlaps = any(t < b_end and b_start < slot_end for b_start, b_end in booked)
        if not overlaps and t > earliest:
            slots.append((t, slot_end))
        t = slot_end
    return slots


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

def get_patient(national_id):
    """Returns (name, gender, birth_date, phone, email, national_id, address) or None."""
    return _fetch_one(
        "SELECT patient_full_name, gender, B_date, patient_contact_number, "
        "patient_email, patient_national_id, patient_address "
        "FROM patients WHERE patient_national_id = %s",
        (national_id,),
    )


def add_patient(name, gender, birth_date, phone, email, national_id, address):
    _execute(
        "INSERT INTO patients (patient_full_name, gender, B_date, patient_contact_number, "
        "patient_email, patient_national_id, patient_address) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (name, gender, birth_date, phone, email or None, national_id, address),
    )


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------

def book_appointment(doctor_id, national_id, patient_name, day, start_min, end_min):
    """Create an appointment after re-checking that the slot is still free."""
    clash = _fetch_one(
        "SELECT appointment_id FROM appointments "
        "WHERE doctor_id = %s AND appointment_date = %s "
        "AND start_time < %s AND end_time > %s",
        (doctor_id, day.isoformat(), _sql_time(end_min), _sql_time(start_min)),
    )
    if clash:
        raise BookingError("This slot was just booked by someone else. Please pick another one.")

    patient_clash = _fetch_one(
        "SELECT appointment_id FROM appointments "
        "WHERE patient_national_id = %s AND appointment_date = %s "
        "AND start_time < %s AND end_time > %s",
        (national_id, day.isoformat(), _sql_time(end_min), _sql_time(start_min)),
    )
    if patient_clash:
        raise BookingError("This patient already has another appointment at that time.")

    return _execute(
        "INSERT INTO appointments (patient_national_id, patient_name, doctor_id, "
        "appointment_date, start_time, end_time) VALUES (%s, %s, %s, %s, %s, %s)",
        (national_id, patient_name, doctor_id, day.isoformat(), _sql_time(start_min), _sql_time(end_min)),
    )


def get_doctor_appointments(doctor_id, day=None):
    """Only the logged-in doctor's appointments; optionally only one day.

    Rows: (appointment_id, date, patient_national_id, patient_name, start_time, end_time)
    """
    sql = (
        "SELECT appointment_id, appointment_date, patient_national_id, patient_name, start_time, end_time "
        "FROM appointments WHERE doctor_id = %s"
    )
    params = [doctor_id]
    if day is not None:
        sql += " AND appointment_date = %s"
        params.append(day.isoformat())
    sql += " ORDER BY appointment_date, start_time"
    return _fetch_all(sql, tuple(params))


def get_all_appointments():
    """Rows: (appointment_id, date, patient_id, patient_name, doctor_id, doctor_name, start, end)."""
    return _fetch_all(
        "SELECT a.appointment_id, a.appointment_date, a.patient_national_id, a.patient_name, "
        "a.doctor_id, d.doctor_name, a.start_time, a.end_time "
        "FROM appointments a JOIN doctors d ON a.doctor_id = d.doctor_id "
        "ORDER BY a.appointment_date, a.start_time"
    )


def cancel_appointment(appointment_id):
    _execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

def get_rooms():
    """Rows: (room_number, address, beds, occupied, people_allowed, start_time, end_time)."""
    return _fetch_all(
        "SELECT r.room_number, r.room_address, r.number_of_beds, COUNT(rr.reservation_id), "
        "r.number_of_people_allowed, r.start_time, r.end_time "
        "FROM rooms r LEFT JOIN room_reservations rr "
        "ON rr.room_number = r.room_number AND rr.check_out IS NULL "
        "GROUP BY r.room_number, r.room_address, r.number_of_beds, "
        "r.number_of_people_allowed, r.start_time, r.end_time "
        "ORDER BY r.room_number"
    )


def get_room(room_number):
    for row in get_rooms():
        if int(row[0]) == int(room_number):
            return row
    return None


def get_room_occupants(room_number):
    """Rows: (reservation_id, national_id, patient_name, check_in)."""
    return _fetch_all(
        "SELECT rr.reservation_id, p.patient_national_id, p.patient_full_name, rr.check_in "
        "FROM room_reservations rr JOIN patients p ON p.patient_national_id = rr.patient_national_id "
        "WHERE rr.room_number = %s AND rr.check_out IS NULL ORDER BY rr.check_in",
        (room_number,),
    )


def reserve_room(room_number, national_id):
    room = get_room(room_number)
    if room is None:
        raise BookingError("Room not found.")
    beds, occupied = int(room[2]), int(room[3])
    if occupied >= beds:
        raise BookingError(f"Room {room_number} is full ({occupied}/{beds} beds taken).")

    current = _fetch_one(
        "SELECT room_number FROM room_reservations "
        "WHERE patient_national_id = %s AND check_out IS NULL",
        (national_id,),
    )
    if current:
        raise BookingError(f"This patient is already staying in room {current[0]}.")

    return _execute(
        "INSERT INTO room_reservations (room_number, patient_national_id, check_in) VALUES (%s, %s, %s)",
        (room_number, national_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def discharge(reservation_id):
    _execute(
        "UPDATE room_reservations SET check_out = %s WHERE reservation_id = %s",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), reservation_id),
    )
