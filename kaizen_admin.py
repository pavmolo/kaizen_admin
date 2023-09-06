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

fields = []
field_count = st.number_input("Количество полей", min_value=1, max_value=10, value=1)

for i in range(field_count):
    st.subheader(f"Поле {i+1}")
    field_name = st.text_input(f"Имя поля {i+1}", key=f"field_name_{i}")
    field_type = st.selectbox(f"Тип поля {i+1}", ["INTEGER", "VARCHAR", "TEXT", "DATE", "FLOAT"], key=f"field_type_{i}")
    fields.append((field_name, field_type))

if st.button("Создать таблицу"):
    create_table(table_name, fields)
    st.success(f"Таблица {table_name} успешно создана!")
