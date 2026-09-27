-- =====================================================================
--  MBA Hospital Management System - Database Schema & Sample Data
--  Target: MySQL 8.x
--  Usage : mysql -u root -p < database.sql
--          (or open this file in MySQL Workbench and press the ⚡ button)
--
--  WARNING: this script DROPS and recreates the `hospital` database,
--  so any data you added before will be reset to the sample data.
-- =====================================================================

DROP DATABASE IF EXISTS hospital;
CREATE DATABASE hospital;
USE hospital;

-- ---------------------------------------------------------------------
--  Tables (created in dependency order so every foreign key resolves)
-- ---------------------------------------------------------------------

CREATE TABLE specializations (
    specialization_id   INT,
    specialization_name VARCHAR(20) UNIQUE NOT NULL,
    CONSTRAINT specialization_id_1 PRIMARY KEY (specialization_id)
);

-- pass_word stores a SHA-256 hash (64 hex characters), never the plain password
CREATE TABLE doctors (
    doctor_name       VARCHAR(30) NOT NULL,
    doctor_id         INT,
    specialization_id INT,
    user_name         VARCHAR(20) NOT NULL UNIQUE,
    pass_word         CHAR(64)    NOT NULL,
    CONSTRAINT doctor_id_1 PRIMARY KEY (doctor_id),
    CONSTRAINT specialization_id_2 FOREIGN KEY (specialization_id)
        REFERENCES specializations (specialization_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- Working shifts; appointment slots are generated inside these shifts
CREATE TABLE doctorschedules (
    schedule_id INT AUTO_INCREMENT,
    doctor_id   INT,
    doctor_name VARCHAR(30),
    start_time  TIME,
    end_time    TIME,
    CONSTRAINT schedule_id_1 PRIMARY KEY (schedule_id),
    CONSTRAINT doctor_id_2 FOREIGN KEY (doctor_id)
        REFERENCES doctors (doctor_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE receptionists (
    receptionist_name VARCHAR(30) NOT NULL,
    receptionist_id   INT,
    user_name         VARCHAR(20) NOT NULL UNIQUE,
    pass_word         CHAR(64)    NOT NULL,
    CONSTRAINT receptionist_id_1 PRIMARY KEY (receptionist_id)
);

CREATE TABLE patients (
    patient_full_name      VARCHAR(30),
    gender                 VARCHAR(10),
    B_date                 DATE,
    patient_contact_number VARCHAR(15),
    patient_email          VARCHAR(100) UNIQUE,
    patient_national_id    VARCHAR(14),
    patient_address        VARCHAR(50),
    CONSTRAINT patient_national_id_1 PRIMARY KEY (patient_national_id)
);

CREATE TABLE rooms (
    room_number              INT,
    room_address             VARCHAR(40),
    number_of_beds           INT,
    number_of_people_allowed INT,
    start_time               TIME,
    end_time                 TIME,
    CONSTRAINT room_number_1 PRIMARY KEY (room_number)
);

-- NEW: one row per patient staying in a room.
-- A reservation is active while check_out IS NULL.
-- A room is full when its active reservations = number_of_beds.
CREATE TABLE room_reservations (
    reservation_id      INT AUTO_INCREMENT,
    room_number         INT         NOT NULL,
    patient_national_id VARCHAR(14) NOT NULL,
    check_in            DATETIME    NOT NULL,
    check_out           DATETIME    NULL,
    CONSTRAINT reservation_id_1 PRIMARY KEY (reservation_id),
    CONSTRAINT room_number_2 FOREIGN KEY (room_number)
        REFERENCES rooms (room_number)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT patient_national_id_4 FOREIGN KEY (patient_national_id)
        REFERENCES patients (patient_national_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- appointment_date is NEW so doctors can see their schedule per day
CREATE TABLE appointments (
    appointment_id      INT NOT NULL AUTO_INCREMENT,
    patient_national_id VARCHAR(14),
    patient_name        VARCHAR(30),
    doctor_id           INT,
    appointment_date    DATE NOT NULL,
    start_time          TIME,
    end_time            TIME,
    CONSTRAINT appointment_id_1 PRIMARY KEY (appointment_id),
    CONSTRAINT doctor_id_3 FOREIGN KEY (doctor_id)
        REFERENCES doctors (doctor_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT patient_national_id_3 FOREIGN KEY (patient_national_id)
        REFERENCES patients (patient_national_id)
        ON DELETE SET NULL ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------
--  Sample data
-- ---------------------------------------------------------------------

INSERT INTO specializations (specialization_id, specialization_name) VALUES
(101, 'Cardiology'),
(102, 'Neurology'),
(103, 'Dentistry');

-- Plain passwords (for testing): password123 / securepass456 / mypassword789
INSERT INTO doctors (doctor_name, doctor_id, specialization_id, user_name, pass_word) VALUES
('Dr. John Smith',    1, 101, 'johnsmith',    'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'),
('Dr. Emily Davis',   2, 102, 'emilydavis',   '9878d344400c00f8bab1a4ba1a3488b3ace88aea983e3d94ba1c781e09ba32bb'),
('Dr. Michael Brown', 3, 103, 'michaelbrown', '1e7724923bb42b54b5df6bf30e4bd8d9d4699788ea53483694d309f3d6cd5c0e');

-- Plain passwords (for testing): alicepass123 / securebob456 / chloe789pass / david2023pwd
INSERT INTO receptionists (receptionist_name, receptionist_id, user_name, pass_word) VALUES
('Alice Carter', 1, 'alicecarter', 'e1137263e43e56b8a008470bada685435f65062ca738698afbb337bd3f55addd'),
('Bob Martin',   2, 'bobmartin',   'f4a6464ce106047343f99d45fbf1889d5896b8fd06028580e16b9709788efa26'),
('Chloe Taylor', 3, 'chloetaylor', 'a928d2a6f2be69791208c3f055eda91316f5bb6b62009cbb0502c1149deed405'),
('David Wilson', 4, 'davidwilson', 'bd7e7ce93cec14d12e1c4e495965ac77d327eb16227e78d1945d7e439a1e7548');

INSERT INTO patients (patient_full_name, gender, B_date, patient_contact_number,
                      patient_email, patient_national_id, patient_address) VALUES
('Ethan James',   'Male',   '1995-02-18', '1122334455', 'ejames@mail.com',   '123456789', '123 Maple Street'),
('Sophia Miller', 'Female', '1993-06-10', '2233445566', 'smiller@mail.com',  '987654321', '456 Oak Avenue'),
('Liam Johnson',  'Male',   '1988-09-25', '3344556677', 'ljohnson@mail.com', '543216789', '789 Pine Road'),
('Olivia Brown',  'Female', '2000-12-30', '4455667788', 'obrown@mail.com',   '112358132', '101 Elm Boulevard');

INSERT INTO rooms (room_number, room_address, number_of_beds,
                   number_of_people_allowed, start_time, end_time) VALUES
(101, 'First Floor, East Wing',   2, 4, '08:00:00', '16:00:00'),
(102, 'First Floor, West Wing',   1, 2, '09:00:00', '15:00:00'),
(201, 'Second Floor, North Wing', 3, 6, '10:00:00', '18:00:00'),
(301, 'Third Floor, East Wing',   3, 2, '13:30:00', '20:30:00');

INSERT INTO room_reservations (room_number, patient_national_id, check_in) VALUES
(101, '112358132', CURRENT_TIMESTAMP);   -- Olivia Brown is staying in room 101

-- Dates are relative to the day you run this script so the demo always has data
INSERT INTO appointments (patient_national_id, patient_name, doctor_id, appointment_date, start_time, end_time) VALUES
('123456789', 'Ethan James',   1, CURDATE(),                          '10:00:00', '10:30:00'),  -- Dr. John Smith
('987654321', 'Sophia Miller', 2, CURDATE(),                          '11:00:00', '11:30:00'),  -- Dr. Emily Davis
('543216789', 'Liam Johnson',  3, DATE_ADD(CURDATE(), INTERVAL 1 DAY), '12:00:00', '12:30:00');  -- Dr. Michael Brown

INSERT INTO doctorschedules (doctor_id, doctor_name, start_time, end_time) VALUES
(1, 'Dr. John Smith',    '08:00:00', '12:00:00'),  -- Morning shift
(1, 'Dr. John Smith',    '13:00:00', '17:00:00'),  -- Afternoon shift
(2, 'Dr. Emily Davis',   '09:00:00', '13:00:00'),  -- Morning shift
(2, 'Dr. Emily Davis',   '14:00:00', '18:00:00'),  -- Afternoon shift
(3, 'Dr. Michael Brown', '10:00:00', '14:00:00'),  -- Midday shift
(3, 'Dr. Michael Brown', '15:00:00', '19:00:00');  -- Evening shift
