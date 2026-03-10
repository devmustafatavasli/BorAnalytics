-- migrations/009_events_table.sql

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_date DATE NOT NULL,
    event_year INT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    title VARCHAR(300) NOT NULL,
    affected_product VARCHAR(20),
    affected_country VARCHAR(3),
    magnitude VARCHAR(20),
    source_url VARCHAR(500) NOT NULL UNIQUE,
    source_name VARCHAR(100) NOT NULL,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_year ON events(event_year);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
