# streamlit_app.py
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

def create_table(table_name, fields):
    """Создание таблицы с указанными полями."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            fields_str = ", ".join([f"{name} {type}" for name, type in fields])
            cursor.execute(f"CREATE TABLE {table_name} ({fields_str});")
        conn.commit()

st.title("Управление базой данных")

# Создание новой таблицы
st.subheader("Создание новой таблицы")

table_name = st.text_input("Имя таблицы")

# Словарь для соответствия русских названий и SQL типов данных
data_types = {
    "Целое число 🔢": "INTEGER",
    "Текст 🅰️": "VARCHAR",
    "Длинный текст 📝": "TEXT",
    "Дата 📅": "DATE",
    "Дробное число 📊": "FLOAT"
}

# Имитация таблицы
st.write("Имитация таблицы:")
columns = st.beta_columns(2)
fields = []

# Добавление столбцов
add_column = st.button("Добавить столбец")
if add_column:
    field_name = columns[0].text_input(f"Имя поля", key=f"field_name")
    field_type = columns[1].selectbox(f"Тип поля", list(data_types.keys()), key=f"field_type")
    fields.append((field_name, data_types[field_type]))

# Отображение имитации таблицы
for field in fields:
    st.write(f"{field[0]} ({field[1]})")

# Создание таблицы
if st.button("Создать таблицу"):
    create_table(table_name, fields)
    st.success(f"Таблица {table_name} успешно создана!")
