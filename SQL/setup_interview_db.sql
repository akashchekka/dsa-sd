PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS employee_projects;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;
DROP TABLE IF EXISTS departments;

CREATE TABLE departments (
    department_id INTEGER PRIMARY KEY,
    department_name TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL,
    annual_budget NUMERIC NOT NULL CHECK (annual_budget > 0)
);

CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    employee_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    department_id INTEGER NOT NULL,
    manager_id INTEGER,
    job_title TEXT NOT NULL,
    hire_date TEXT NOT NULL CHECK (hire_date = date(hire_date)),
    salary NUMERIC NOT NULL CHECK (salary > 0),
    performance_rating INTEGER CHECK (performance_rating BETWEEN 1 AND 5),
    employment_status TEXT NOT NULL DEFAULT 'active'
        CHECK (employment_status IN ('active', 'leave', 'terminated')),
    FOREIGN KEY (department_id) REFERENCES departments (department_id),
    FOREIGN KEY (manager_id) REFERENCES employees (employee_id)
);

CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY,
    project_name TEXT NOT NULL UNIQUE,
    owning_department_id INTEGER NOT NULL,
    start_date TEXT NOT NULL CHECK (start_date = date(start_date)),
    end_date TEXT CHECK (end_date IS NULL OR end_date = date(end_date)),
    budget NUMERIC NOT NULL CHECK (budget > 0),
    project_status TEXT NOT NULL
        CHECK (project_status IN ('planned', 'active', 'completed', 'cancelled')),
    CHECK (end_date IS NULL OR end_date >= start_date),
    FOREIGN KEY (owning_department_id) REFERENCES departments (department_id)
);

CREATE TABLE employee_projects (
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    assigned_date TEXT NOT NULL CHECK (assigned_date = date(assigned_date)),
    role_name TEXT NOT NULL,
    allocation_percent INTEGER NOT NULL CHECK (allocation_percent BETWEEN 1 AND 100),
    hourly_rate NUMERIC NOT NULL CHECK (hourly_rate > 0),
    PRIMARY KEY (employee_id, project_id),
    FOREIGN KEY (employee_id) REFERENCES employees (employee_id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects (project_id) ON DELETE CASCADE
);

INSERT INTO departments (
    department_id,
    department_name,
    location,
    annual_budget
) VALUES
    (1, 'Engineering', 'Bengaluru', 4200000),
    (2, 'Data Science', 'Hyderabad', 2800000),
    (3, 'Product', 'Bengaluru', 1900000),
    (4, 'Sales', 'Mumbai', 2400000),
    (5, 'Human Resources', 'Gurugram', 900000),
    (6, 'Legal', 'Gurugram', 750000);

-- Top-level leaders are inserted first so later rows can reference them.
INSERT INTO employees (
    employee_id,
    employee_name,
    email,
    department_id,
    manager_id,
    job_title,
    hire_date,
    salary,
    performance_rating,
    employment_status
) VALUES
    (1, 'Aarav Sharma', 'aarav.sharma@example.com', 1, NULL, 'VP Engineering', '2017-03-15', 240000, 5, 'active'),
    (2, 'Diya Patel', 'diya.patel@example.com', 2, NULL, 'Director of Data', '2018-07-09', 225000, 4, 'active'),
    (3, 'Kabir Singh', 'kabir.singh@example.com', 3, NULL, 'Director of Product', '2019-01-21', 210000, 5, 'active'),
    (4, 'Meera Iyer', 'meera.iyer@example.com', 4, NULL, 'VP Sales', '2016-11-02', 235000, 4, 'active'),
    (5, 'Rohan Gupta', 'rohan.gupta@example.com', 5, NULL, 'HR Director', '2020-05-18', 170000, 4, 'active'),
    (6, 'Ananya Rao', 'ananya.rao@example.com', 1, 1, 'Engineering Manager', '2019-08-12', 185000, 5, 'active'),
    (7, 'Vikram Joshi', 'vikram.joshi@example.com', 1, 1, 'Engineering Manager', '2020-02-24', 180000, 4, 'active'),
    (8, 'Ishita Das', 'ishita.das@example.com', 2, 2, 'Data Science Manager', '2020-09-14', 178000, 5, 'active'),
    (9, 'Arjun Nair', 'arjun.nair@example.com', 3, 3, 'Senior Product Manager', '2021-04-05', 165000, 4, 'active'),
    (10, 'Saanvi Mehta', 'saanvi.mehta@example.com', 4, 4, 'Regional Sales Manager', '2019-12-10', 160000, 3, 'active'),
    (11, 'Neel Verma', 'neel.verma@example.com', 1, 6, 'Senior Software Engineer', '2021-06-28', 150000, 5, 'active'),
    (12, 'Tara Kulkarni', 'tara.kulkarni@example.com', 1, 6, 'Software Engineer', '2022-10-17', 122000, 4, 'active'),
    (13, 'Aditya Bose', 'aditya.bose@example.com', 1, 7, 'Senior Site Reliability Engineer', '2020-07-06', 155000, 4, 'active'),
    (14, 'Nisha Kapoor', 'nisha.kapoor@example.com', 1, 7, 'Software Engineer', '2023-02-13', 118000, NULL, 'leave'),
    (15, 'Rahul Menon', 'rahul.menon@example.com', 2, 8, 'Senior Data Scientist', '2021-03-22', 148000, 5, 'active'),
    (16, 'Pooja Shah', 'pooja.shah@example.com', 2, 8, 'Data Analyst', '2023-07-03', 98000, 4, 'active'),
    (17, 'Karan Malhotra', 'karan.malhotra@example.com', 2, 8, 'Machine Learning Engineer', '2022-01-31', 142000, 3, 'active'),
    (18, 'Lavanya Reddy', 'lavanya.reddy@example.com', 3, 9, 'Product Manager', '2022-05-16', 130000, 5, 'active'),
    (19, 'Manav Chawla', 'manav.chawla@example.com', 4, 10, 'Account Executive', '2022-08-08', 105000, 4, 'active'),
    (20, 'Aisha Khan', 'aisha.khan@example.com', 4, 10, 'Account Executive', '2023-01-09', 102000, 2, 'active'),
    (21, 'Dev Mishra', 'dev.mishra@example.com', 5, 5, 'Recruiter', '2022-11-21', 92000, 4, 'active'),
    (22, 'Simran Kaur', 'simran.kaur@example.com', 1, 6, 'Software Engineer', '2021-09-27', 125000, 3, 'terminated'),
    (23, 'Yash Jain', 'yash.jain@example.com', 3, 9, 'Associate Product Manager', '2024-01-15', 95000, NULL, 'active');

INSERT INTO projects (
    project_id,
    project_name,
    owning_department_id,
    start_date,
    end_date,
    budget,
    project_status
) VALUES
    (1, 'Checkout Modernization', 1, '2024-01-08', NULL, 850000, 'active'),
    (2, 'Fraud Detection Platform', 2, '2023-09-18', NULL, 720000, 'active'),
    (3, 'Mobile App Redesign', 3, '2023-04-10', '2024-03-29', 460000, 'completed'),
    (4, 'Observability Upgrade', 1, '2024-02-12', NULL, 390000, 'active'),
    (5, 'Customer Churn Model', 2, '2024-05-06', NULL, 310000, 'active'),
    (6, 'Enterprise Expansion', 4, '2024-01-15', '2024-12-20', 540000, 'completed'),
    (7, 'Developer Portal', 1, '2025-02-03', NULL, 275000, 'planned'),
    (8, 'Pricing Experiment', 3, '2024-06-03', '2024-09-30', 180000, 'cancelled'),
    (9, 'Hiring Analytics', 5, '2024-08-05', NULL, 160000, 'active'),
    (10, 'Contract Automation', 6, '2025-01-13', NULL, 210000, 'planned');

INSERT INTO employee_projects (
    employee_id,
    project_id,
    assigned_date,
    role_name,
    allocation_percent,
    hourly_rate
) VALUES
    (6, 1, '2024-01-08', 'Technical Lead', 40, 120),
    (11, 1, '2024-01-08', 'Backend Engineer', 80, 105),
    (12, 1, '2024-01-15', 'Backend Engineer', 70, 82),
    (18, 1, '2024-01-08', 'Product Manager', 30, 88),
    (8, 2, '2023-09-18', 'Data Lead', 35, 116),
    (13, 2, '2023-10-02', 'Platform Engineer', 30, 108),
    (15, 2, '2023-09-18', 'Data Scientist', 75, 101),
    (17, 2, '2023-09-25', 'ML Engineer', 80, 96),
    (9, 3, '2023-04-10', 'Product Lead', 50, 102),
    (12, 3, '2023-05-01', 'API Engineer', 25, 80),
    (18, 3, '2023-04-10', 'Product Manager', 70, 86),
    (7, 4, '2024-02-12', 'Technical Sponsor', 20, 118),
    (13, 4, '2024-02-12', 'SRE Lead', 70, 110),
    (11, 4, '2024-03-04', 'Backend Engineer', 20, 105),
    (8, 5, '2024-05-06', 'Data Lead', 25, 116),
    (15, 5, '2024-05-06', 'Data Scientist', 60, 101),
    (16, 5, '2024-05-13', 'Data Analyst', 80, 65),
    (17, 5, '2024-05-06', 'ML Engineer', 35, 96),
    (4, 6, '2024-01-15', 'Executive Sponsor', 10, 145),
    (10, 6, '2024-01-15', 'Sales Lead', 60, 92),
    (19, 6, '2024-01-22', 'Account Executive', 90, 58),
    (20, 6, '2024-01-22', 'Account Executive', 90, 56),
    (6, 7, '2025-02-03', 'Technical Lead', 20, 120),
    (12, 7, '2025-02-03', 'Full Stack Engineer', 30, 84),
    (23, 8, '2024-06-03', 'Product Analyst', 50, 54),
    (16, 8, '2024-06-03', 'Experiment Analyst', 20, 65),
    (5, 9, '2024-08-05', 'Executive Sponsor', 10, 108),
    (21, 9, '2024-08-05', 'Domain Specialist', 50, 58),
    (16, 9, '2024-08-12', 'Data Analyst', 20, 65);

CREATE INDEX idx_employees_department_id
    ON employees (department_id);

CREATE INDEX idx_employees_manager_id
    ON employees (manager_id);

CREATE INDEX idx_employees_salary
    ON employees (salary);

CREATE INDEX idx_projects_department_status
    ON projects (owning_department_id, project_status);

CREATE INDEX idx_employee_projects_project_id
    ON employee_projects (project_id);
