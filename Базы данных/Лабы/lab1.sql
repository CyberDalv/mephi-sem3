DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    id INTEGER PRIMARY KEY,
    name VARCHAR(64) NOT NULL
);

CREATE TABLE patients (
    card_number BIGINT PRIMARY KEY,
    last_name VARCHAR(200) NOT NULL,
    first_name VARCHAR(200) NOT NULL,
    middle_name VARCHAR(200) NOT NULL,
    admission_reason VARCHAR(2000) NOT NULL DEFAULT 'Черепно-мозговая травма',
    policy_number BIGINT NOT NULL UNIQUE CHECK (policy_number >= 0 AND policy_number <= 1000000000),
    diagnosis VARCHAR(2000) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES countries(id),

    CONSTRAINT patients_fio_uq UNIQUE (last_name, first_name, middle_name)
);