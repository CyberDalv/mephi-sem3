-- Задание 1
CREATE TABLE staff (
    id integer PRIMARY KEY,
    name varchar(64) NOT NULL CHECK (name <> ''),
    department varchar(64) NOT NULL CHECK (department <> '')
);

-- Задание 2
CREATE SEQUENCE staff_id_seq
    START WITH 12
    INCREMENT BY 8
    CACHE 100
    CYCLE;

-- Задание 3
INSERT INTO staff (id, name, department)
VALUES (nextval('staff_id_seq'), 'Ivan Makarenko', 'Director');

-- Задание 4
INSERT INTO staff (id, name, department)
SELECT nextval('staff_id_seq'), e.last_name,
       COALESCE(d.department_name, 'No department')
FROM employees e
LEFT JOIN departments d ON d.department_id = e.department_id
ORDER BY e.employee_id;

-- Задание 5
UPDATE staff
SET department = 'Innovations department'
WHERE id < 40;

-- Задание 6
DELETE FROM staff
WHERE name LIKE '%K%';

-- Задание 7
-- Идентификатор менеджера задаётся в базовой части запроса (сейчас 100).
WITH RECURSIVE subordinates AS (
    SELECT employee_id, first_name, last_name, job_id
    FROM employees
    WHERE manager_id = 100
    UNION ALL
    SELECT e.employee_id, e.first_name, e.last_name, e.job_id
    FROM employees e
    JOIN subordinates s ON e.manager_id = s.employee_id
) CYCLE employee_id SET is_cycle USING path
SELECT s.employee_id, s.first_name, s.last_name, j.job_title
FROM subordinates s
LEFT JOIN jobs j ON j.job_id = s.job_id
WHERE NOT s.is_cycle
ORDER BY s.employee_id;