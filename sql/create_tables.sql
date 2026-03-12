CREATE TABLE IF NOT EXISTS vacancies (
    vacancy_id BIGINT PRIMARY KEY,
    search_text TEXT NOT NULL,
    name TEXT,
    employer_name TEXT,
    area_name TEXT,
    published_at TIMESTAMP,
    employment_name TEXT,
    experience_name TEXT,
    schedule_name TEXT,
    salary_from NUMERIC,
    salary_to NUMERIC,
    salary_currency TEXT,
    requirement TEXT,
    responsibility TEXT,
    alternate_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);