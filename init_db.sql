-- Run this on your RDS MySQL instance
CREATE DATABASE IF NOT EXISTS meditrack;
USE meditrack;

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id   INT PRIMARY KEY AUTO_INCREMENT,
    equipment_name VARCHAR(100) NOT NULL,
    serial_number  VARCHAR(50)  NOT NULL UNIQUE,
    department     VARCHAR(100) NOT NULL,
    purchase_date  DATE,
    status         VARCHAR(30)  NOT NULL DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS maintenance_log (
    log_id            INT PRIMARY KEY AUTO_INCREMENT,
    equipment_id      INT          NOT NULL,
    maintenance_date  DATE         NOT NULL,
    technician_name   VARCHAR(100) NOT NULL,
    issue_reported    TEXT,
    resolution_notes  TEXT,
    next_due_date     DATE,
    FOREIGN KEY (equipment_id) REFERENCES equipment(equipment_id)
);

-- Seed data: one overdue item for dashboard demo
INSERT INTO equipment (equipment_name, serial_number, department, purchase_date, status)
VALUES ('Ventilator', 'VNT-001', 'ICU', '2022-01-15', 'Active');

INSERT INTO maintenance_log (equipment_id, maintenance_date, technician_name,
    issue_reported, resolution_notes, next_due_date)
VALUES (1, '2023-06-01', 'Ravi Kumar',
    'Routine calibration', 'All parameters within spec', '2024-01-01');
