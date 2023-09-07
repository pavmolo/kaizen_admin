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
def view_tables_page():
    st.title("Просмотр таблиц базы данных")

    # Получение списка таблиц
    tables = get_tables()

    for table_name in tables:
        st.subheader(f"Таблица: {table_name}")

        # Получение данных из таблицы
        data = get_table_data(table_name)

        # Определение ключевого столбца
        key_column = get_primary_key(table_name)

        # Если ключевой столбец найден, добавьте иконку ключа к нему
        if key_column and key_column in data.columns:
            data = data.rename(columns={key_column: f"🔑 {key_column}"})

        # Выведите обновленный DataFrame в Streamlit
        st.dataframe(data)
        st.write("---")  # Разделитель между таблицами


st.title("Управление базой данных")

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
def create_table_page():
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
    
   # Интерфейс для создания новой таблицы
def create_table_interface():
    st.subheader("Создание новой таблицы")
    table_name = st.text_input("Имя таблицы")
    # ... [Ваш код для добавления полей]
    primary_key = st.selectbox("Выберите ключевое поле", [field[0] for field in st.session_state.fields])
    # ... [Ваш код для отображения имитации таблицы]
    if st.button("Создать таблицу"):
        create_table(table_name, st.session_state.fields, primary_key)
        st.success(f"Таблица {table_name} успешно создана!")

# Интерфейс для добавления нового поля в существующую таблицу
def add_column_interface():
    st.subheader("Добавление нового поля в существующую таблицу")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    column_name = st.text_input("Имя нового поля")
    column_type = st.selectbox("Тип поля", ["INTEGER", "VARCHAR", "TEXT", "DATE", "FLOAT"])
    if st.button("Добавить поле"):
        add_column_to_table(table_name, column_name, column_type)
        st.success(f"Поле {column_name} успешно добавлено в таблицу {table_name}!")

def get_table_columns(table_name):
    """Получение списка столбцов для указанной таблицы."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}';")
            return [row[0] for row in cursor.fetchall()]


# Интерфейс для добавления новой строки в таблицу
def add_row_interface():
    st.subheader("Добавление новой строки в таблицу")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    columns = get_table_columns(table_name)
    data = {}
    for column in columns:
        data[column] = st.text_input(f"Значение для {column}")
    if st.button("Добавить строку"):
        insert_into_table(table_name, data)
        st.success(f"Строка успешно добавлена в таблицу {table_name}!")

# Интерфейс для просмотра содержимого таблицы
def view_table_interface():
    st.subheader("Просмотр содержимого таблицы")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    data = get_table_data(table_name)
    st.dataframe(data)

# Интерфейс для изменения существующих записей
def update_row_interface():
    st.subheader("Изменение существующих записей")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    key_column = get_primary_key(table_name)
    key_value = st.text_input(f"Введите значение ключевого поля ({key_column}) для изменения")
    if st.button(f"Загрузить данные для {key_column} = {key_value}"):
        data = get_row_data(table_name, key_column, key_value)
        for column, value in data.items():
            data[column] = st.text_input(f"Новое значение для {column}", value)
        if st.button("Обновить запись"):
            update_table_data(table_name, key_column, key_value, data)
            st.success(f"Запись с {key_column} = {key_value} успешно обновлена!")

# Интерфейс для удаления строки из таблицы
def delete_row_interface():
    st.subheader("Удаление строки из таблицы")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    key_column = get_primary_key(table_name)
    key_value = st.text_input(f"Введите значение ключевого поля ({key_column}) для удаления")
    if st.button("Удалить строку"):
        delete_from_table(table_name, key_column, key_value)
        st.success(f"Строка с {key_column} = {key_value} успешно удалена!")

# Интерфейс для удаления таблицы
def delete_table_interface():
    st.subheader("Удаление таблицы")
    table_name = st.selectbox("Выберите таблицу для удаления", get_tables())
    if st.button(f"Удалить таблицу {table_name}?"):
        drop_table(table_name)
        st.success(f"Таблица {table_name} успешно удалена!")

# Главный интерфейс
def main_interface():
    st.title("Управление базой данных")
    page = st.radio("Выберите действие", ["Создать таблицу", "Добавить поле", "Добавить строку", "Просмотр таблицы", "Изменить строку", "Удалить строку", "Удалить таблицу"])
    if page == "Создать таблицу":
        create_table_interface()
    elif page == "Добавить поле":
        add_column_interface()
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
