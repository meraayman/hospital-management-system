"""Central settings for the MBA Hospital app.

Change DB_CONFIG to match your own MySQL installation — this is the ONLY
place the database credentials are written.
"""
import os

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "1234",      # <-- put your MySQL root password here
    "database": "hospital",
}

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "Images")

# Appointment slot length in minutes
SLOT_MINUTES = 30

# Theme colours (taken from the original design)
PRIMARY = "#32acc7"    # window background
BUTTON = "#0088a6"     # main buttons
TEXT = "#006B82"       # dark teal text
LIGHT = "#E8E8E8"      # tiles / input background
