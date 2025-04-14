-- Create the "companies" table to store company information.
CREATE TABLE companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT, -- Optional: Company address.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the "machines" table to store machines or vehicles.
CREATE TABLE machines (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL, -- Machine name or model.
    type VARCHAR(50) NOT NULL,  -- For example: 'truck' or 'fixed'.
    company_id INTEGER NOT NULL, -- Foreign key referencing companies.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Create the "maintenances" table to record scheduled and executed maintenance tasks.
CREATE TABLE maintenances (
    id SERIAL PRIMARY KEY,
    machine_id INTEGER NOT NULL,  -- Foreign key referencing machines.
    type VARCHAR(50) NOT NULL,      -- Maintenance type (e.g., "oil change", "revision").
    scheduled_date DATE NOT NULL,   -- Date scheduled for the maintenance.
    executed_date DATE,             -- Date the maintenance was executed; can be null if not done.
    notes TEXT,                     -- Optional notes.
    FOREIGN KEY (machine_id) REFERENCES machines(id)
);

-- Create the "users" table for authentication and integration purposes.
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50),               -- Optional: Role (e.g., 'admin', 'user').
    company_id INTEGER,             -- Optional: Associate the user with a company.
    FOREIGN KEY (company_id) REFERENCES companies(id)
);


INSERT INTO companies (name, address) VALUES ('ACME Inc.', '123 Main St');
INSERT INTO machines (name, type, company_id) VALUES ('Truck Model X', 'truck', 1);
INSERT INTO maintenances (machine_id, type, scheduled_date) VALUES (1, 'oil change', '2025-01-01');


