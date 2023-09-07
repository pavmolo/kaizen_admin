import streamlit as st
import pandas as pd
import psycopg2

# Параметры подключения к базе данных
DATABASE_CONFIG = {
    'dbname': 'kaizen_it_administration_aport',
    'user': 'pavmolo',
    'password': st.secrets["database"]["password"],
    'host': '45.86.182.111'
}

def get_connection():
    """Получение соединения с базой данных."""
    return psycopg2.connect(**DATABASE_CONFIG)

def get_tables():
    """Получение списка таблиц для указанной базы данных."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT tablename FROM pg_tables WHERE schemaname='public';")
            return [row[0] for row in cursor.fetchall()]

def get_table_data(table_name):
    """Получение данных из указанной таблицы."""
    with get_connection() as conn:
        return pd.read_sql(f"SELECT * FROM {table_name};", conn)

def create_table(table_name, fields, primary_key):
    """Создание таблицы в базе данных."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            fields_str = ", ".join([f"{name} {type}" for name, type in fields])
            sql = f"CREATE TABLE {table_name} ({fields_str}, PRIMARY KEY ({primary_key}));"
            cursor.execute(sql)
            conn.commit()

def get_primary_key(table_name):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT a.attname
                FROM   pg_index i
                JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                     AND a.attnum = ANY(i.indkey)
                WHERE  i.indrelid = '{table_name}'::regclass
                AND    i.indisprimary;
            """)
            result = cursor.fetchone()
            return result[0] if result else None

data_types = {
    "Целое число 🔢": "INTEGER",
    "Текст 🅰️": "VARCHAR",
    "Длинный текст 📝": "TEXT",
    "Дата 📅": "DATE",
    "Дробное число 📊": "FLOAT"
}

def change_column_type(table_name, column_name, new_type):
    """Изменение типа данных столбца."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type};")
            conn.commit()

def rename_column(table_name, old_name, new_name):
    """Переименование столбца."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name};")
            conn.commit()

def get_table_columns(table_name):
    """Получение списка столбцов для указанной таблицы."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}';")
            return [row[0] for row in cursor.fetchall()]

def insert_into_table(table_name, data_dict):
    """Вставка данных в таблицу."""
    columns = ", ".join(data_dict.keys())
    values = ", ".join(["%s"] * len(data_dict))
    sql = f"INSERT INTO {table_name} ({columns}) VALUES ({values});"
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                cursor.execute(sql, list(data_dict.values()))
                conn.commit()
                return True
            except psycopg2.errors.UniqueViolation:
                conn.rollback()  # Откатываем транзакцию
                st.error(f"Ошибка: Запись с таким ключевым значением уже существует в таблице {table_name}.")
                return False

def get_row_data(table_name, key_column, key_value):
    """Получение данных из указанной строки таблицы на основе значения ключевого поля."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {key_column} = %s;", (key_value,))
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))

def get_unique_values(table_name, column_name):
    """Получение уникальных значений из столбца."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name};")
            return [row[0] for row in cursor.fetchall()]

def update_table_data(table_name, key_column, key_value, data):
    """Обновление данных в таблице."""
    set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, list(data.values()) + [key_value])
            conn.commit()

# ... [Продолжение вашего кода]

# Главный интерфейс
def main_interface():
    st.title("Управление базой данных")
    page = st.radio("Выберите действие", ["Создать таблицу", "Добавить поле", "Изменить поля", "Добавить строку", "Просмотр таблицы", "Изменить строку", "Удалить строку", "Удалить таблицу"])
    if page == "Создать таблицу":
        create_table_interface()
    elif page == "Добавить поле":
        add_column_interface()
    elif page == "Изменить поля":
        modify_table_interface()
    elif page == "Добавить строку":
        add_row_interface()
    elif page == "Просмотр таблицы":
        view_table_interface()
    elif page == "Изменить строку":
        update_row_interface()
    elif page == "Удалить строку":
        delete_row_interface()
    elif page == "Удалить таблицу":
        delete_table_interface()

if __name__ == "__main__":
    main_interface()
