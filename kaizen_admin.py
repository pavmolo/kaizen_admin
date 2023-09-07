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

def update_table_data(table_name, key_column, key_value, data):
    """Обновление данных в таблице."""
    set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, list(data.values()) + [key_value])
            conn.commit()


# Интерфесные функции

def create_table_interface():
    st.subheader("Создание новой таблицы")
    table_name = st.text_input("Название таблицы")
    
    if 'fields' not in st.session_state:
        st.session_state.fields = []
    
    with st.form(key='add_column_form'):
        field_name = st.text_input(f"Имя поля", key=f"field_name_{len(st.session_state.fields)}")
        field_type = st.selectbox(f"Тип поля", list(data_types.keys()), key=f"field_type_{len(st.session_state.fields)}")
        add_column_button = st.form_submit_button(label='Добавить столбец')
    
    if add_column_button:
        if field_name and field_type:
            st.session_state.fields.append((field_name, data_types[field_type]))
    
    for field in st.session_state.fields:
        st.write(f"{field[0]} ({field[1]})")
    
    primary_key = st.selectbox("Выберите ключевое поле", [field[0] for field in st.session_state.fields])
    
    if st.button("Создать таблицу"):
        if table_name and st.session_state.fields:
            create_table(table_name, st.session_state.fields, primary_key)
            st.success(f"Таблица {table_name} успешно создана!")
            st.session_state.fields = []

def add_column_interface():
    st.subheader("Добавление нового поля в существующую таблицу")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    column_name = st.text_input("Имя нового поля")
    column_type = st.selectbox("Тип поля", list(data_types.keys()))
    if st.button("Добавить поле"):
        add_column_to_table(table_name, column_name, data_types[column_type])
        st.success(f"Поле {column_name} успешно добавлено в таблицу {table_name}!")

def modify_table_interface():
    st.subheader("Изменение структуры таблицы")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    action = st.radio("Выберите действие", ["Изменить тип данных", "Переименовать столбец"])
    
    if action == "Изменить тип данных":
        column_name = st.selectbox("Выберите столбец", get_table_columns(table_name))
        new_type = st.selectbox("Выберите новый тип данных", list(data_types.keys()))
        if st.button("Применить"):
            change_column_type(table_name, column_name, data_types[new_type])
            st.success(f"Тип данных для {column_name} изменен на {new_type}!")
    
    elif action == "Переименовать столбец":
        old_name = st.selectbox("Выберите столбец", get_table_columns(table_name))
        new_name = st.text_input("Введите новое имя столбца")
        if st.button("Применить"):
            rename_column(table_name, old_name, new_name)
            st.success(f"Столбец {old_name} переименован в {new_name}!")

def add_row_interface():
    st.subheader("Добавление новой строки в таблицу")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    columns = get_table_columns(table_name)
    data_dict = {}
    for col in columns:
        data_dict[col] = st.text_input(f"Введите значение для {col}")
    if st.button("Добавить строку"):
        if all(value for value in data_dict.values()):
            success = insert_into_table(table_name, data_dict)
            if success:
                st.success(f"Строка успешно добавлена в таблицу {table_name}!")
        else:
            st.warning("Пожалуйста, заполните все поля перед сохранением.")

def view_table_interface():
    st.subheader("Просмотр содержимого таблицы")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    data = get_table_data(table_name)
    st.dataframe(data)

def update_row_interface():
    st.subheader("Изменение существующих записей")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    key_column = get_primary_key(table_name)
    key_value = st.selectbox(f"Выберите значение ключевого поля ({key_column}) для изменения", get_unique_values(table_name, key_column))
    if key_value:
        data = get_row_data(table_name, key_column, key_value)
        for column in data.keys():
            data[column] = st.text_input(f"Значение для {column}", data[column])
        if st.button("Обновить запись"):
            update_table_data(table_name, key_column, key_value, data)
            st.success(f"Запись с {key_column} = {key_value} успешно обновлена!")

# Вывод интерфейса


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
