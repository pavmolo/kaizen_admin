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

# Инициализация сессионного состояния
if 'fields' not in st.session_state:
    st.session_state.fields = []

# Добавление столбцов
if st.button("Добавить столбец"):
    field_name = st.text_input(f"Имя поля", key=f"field_name_{len(st.session_state.fields)}")
    field_type = st.selectbox(f"Тип поля", list(data_types.keys()), key=f"field_type_{len(st.session_state.fields)}")
    if field_name and field_type:
        st.session_state.fields.append((field_name, data_types[field_type]))
# Отображение добавленных столбцов
for field in st.session_state.fields:
    st.write(f"{field[0]} ({field[1]})")

# Выбор ключевого поля
primary_key = st.selectbox("Выберите ключевое поле", [field[0] for field in st.session_state.fields])

# Отображение имитации таблицы в виде датафрейма
df = pd.DataFrame(columns=[field[0] for field in st.session_state.fields])
st.dataframe(df)

# Создание таблицы
if st.button("Создать таблицу"):
    create_table(table_name, st.session_state.fields, primary_key)
    st.success(f"Таблица {table_name} успешно создана!")
