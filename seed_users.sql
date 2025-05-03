CREATE TABLE IF NOT EXISTS users (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    age  INT  NOT NULL,
    email TEXT NOT NULL UNIQUE
);

INSERT INTO users (name, age, email) VALUES
('John Smith',      34, 'john.smith@example.com'),
('Emily Davis',     27, 'emily.davis@example.com'),
('Michael Johnson', 43, 'michael.johnson@example.com'),
('Sarah Lee',       30, 'sarah.lee@example.com'),
('David Martinez',  25, 'david.martinez@example.com'),
('Anna Kim',        38, 'anna.kim@example.com'),
('Robert Brown',    50, 'robert.brown@example.com'),
('Jessica Wilson',  29, 'jessica.wilson@example.com'),
('Daniel Garcia',   32, 'daniel.garcia@example.com'),
('Laura Thompson',  41, 'laura.thompson@example.com');