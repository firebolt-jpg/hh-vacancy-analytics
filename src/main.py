import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
import time


HH_API_URL = "https://api.hh.ru/vacancies"

# Настройки БД — вставьте свои значения
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "hh_analytics",
    "user": "postgres",
    "password": "postgres"
}

# Поисковые запросы для сбора вакансий
SEARCH_QUERIES = [
    "data analyst",
    "python developer",
    "data engineer",
    "bi analyst"
]

# Сколько страниц брать по каждому запросу
MAX_PAGES = 5

# Сколько вакансий на страницу
PER_PAGE = 50


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def create_table():
    query = """
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
    """
    conn = get_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(query)
    finally:
        conn.close()


def parse_datetime(value: str):
    if not value:
        return None

    # Пример: 2025-03-11T12:34:56+0300
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return None


def fetch_vacancies(search_text: str, max_pages: int = 5, per_page: int = 50):
    all_vacancies = []

    headers = {
        "User-Agent": "hh-vacancy-analytics/1.0"
    }

    for page in range(max_pages):
        params = {
            "text": search_text,
            "page": page,
            "per_page": per_page,
            "only_with_salary": False
        }

        response = requests.get(HH_API_URL, params=params, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        items = data.get("items", [])

        if not items:
            break

        for item in items:
            salary = item.get("salary") or {}
            employer = item.get("employer") or {}
            area = item.get("area") or {}
            employment = item.get("employment") or {}
            experience = item.get("experience") or {}
            schedule = item.get("schedule") or {}
            snippet = item.get("snippet") or {}

            vacancy = (
                item.get("id"),
                search_text,
                item.get("name"),
                employer.get("name"),
                area.get("name"),
                parse_datetime(item.get("published_at")),
                employment.get("name"),
                experience.get("name"),
                schedule.get("name"),
                salary.get("from"),
                salary.get("to"),
                salary.get("currency"),
                snippet.get("requirement"),
                snippet.get("responsibility"),
                item.get("alternate_url")
            )
            all_vacancies.append(vacancy)

        print(f"[INFO] Запрос '{search_text}': страница {page + 1}, получено {len(items)} вакансий")

        # Небольшая пауза между запросами
        time.sleep(0.5)

    return all_vacancies


def save_vacancies(vacancies):
    if not vacancies:
        return 0

    query = """
    INSERT INTO vacancies (
        vacancy_id,
        search_text,
        name,
        employer_name,
        area_name,
        published_at,
        employment_name,
        experience_name,
        schedule_name,
        salary_from,
        salary_to,
        salary_currency,
        requirement,
        responsibility,
        alternate_url
    )
    VALUES %s
    ON CONFLICT (vacancy_id) DO NOTHING;
    """

    conn = get_connection()
    inserted_count = 0

    try:
        with conn:
            with conn.cursor() as cur:
                execute_values(cur, query, vacancies)
                inserted_count = cur.rowcount
    finally:
        conn.close()

    return inserted_count


def main():
    print("[INFO] Создание таблицы...")
    create_table()

    total_fetched = 0

    for search_text in SEARCH_QUERIES:
        print(f"[INFO] Сбор вакансий по запросу: {search_text}")
        vacancies = fetch_vacancies(
            search_text=search_text,
            max_pages=MAX_PAGES,
            per_page=PER_PAGE
        )

        fetched_count = len(vacancies)
        total_fetched += fetched_count

        print(f"[INFO] Получено {fetched_count} вакансий по запросу '{search_text}'")

        inserted_count = save_vacancies(vacancies)
        print(f"[INFO] Добавлено в БД: {inserted_count}")

    print(f"[INFO] Всего обработано вакансий: {total_fetched}")
    print("[INFO] Загрузка завершена")


if __name__ == "__main__":
    main()