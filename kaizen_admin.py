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

# Используем st.data_editor для создания структуры таблицы
default_data = {"Имя поля": ["поле1"], "Тип данных": ["Целое число 🔢"]}
data = st.data_editor("Структура таблицы", pd.DataFrame(default_data))
fields = list(zip(data["Имя поля"], [data_types[type] for type in data["Тип данных"]]))

if st.button("Создать таблицу"):
    create_table(table_name, fields)
    st.success(f"Таблица {table_name} успешно создана!")
