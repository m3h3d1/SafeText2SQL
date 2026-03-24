DROP TABLE IF EXISTS patients;

CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL
);

INSERT INTO patients (id, name, age, gender) VALUES
    (1, 'Alice', 14, 'F'),
    (2, 'Bob', 29, 'M'),
    (3, 'Carla', 42, 'F'),
    (4, 'David', 61, 'M'),
    (5, 'Eva', 37, 'F');
