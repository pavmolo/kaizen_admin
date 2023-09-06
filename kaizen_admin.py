# streamlit_app.py
import streamlit as st
import pandas as pd
import psycopg2

# Параметры подключения к базе данных
DATABASE_CONFIG = {
    'dbname': 'c79908_kaizen_it_na4u_ru',
    'user': 'c79908_kaizen_it_na4u_ru',
    'password': st.secrets["database"]["password"],  # Используем секретный пароль из secrets.toml
    'host': 'postgres.c79908.h2'
}

def get_connection():
    """Получение соединения с базой данных."""
    return psycopg2.connect(**DATABASE_CONFIG)

def get_databases():
    """Получение списка баз данных."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT datname FROM pg_database;")
            return [row[0] for row in cursor.fetchall()]

def get_tables(database):
    """Получение списка таблиц для указанной базы данных."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT tablename FROM pg_tables WHERE schemaname='public';")
            return [row[0] for row in cursor.fetchall()]

def get_table_data(table_name):
    """Получение данных из указанной таблицы."""
    with get_connection() as conn:
        return pd.read_sql(f"SELECT * FROM {table_name};", conn)

st.title("Просмотр баз данных и таблиц")

# Выбор базы данных
database = st.selectbox("Выберите базу данных:", get_databases())

# Выбор таблицы
table = st.selectbox("Выберите таблицу:", get_tables(database))

# Отображение данных таблицы
st.write(get_table_data(table))
