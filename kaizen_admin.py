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
    
    # Инициализация сессионного состояния
    if 'fields' not in st.session_state:
        st.session_state.fields = []
    
    # Добавление столбцов
    with st.form(key='add_column_form'):
        field_name = st.text_input(f"Имя поля", key=f"field_name_{len(st.session_state.fields)}")
        field_type = st.selectbox(f"Тип поля", list(data_types.keys()), key=f"field_type_{len(st.session_state.fields)}")
        submit_button = st.form_submit_button(label='Добавить столбец')
    
    if submit_button:
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
    def view_tables_page():
        st.title("Просмотр таблиц")
        tables = get_tables()
        selected_table = st.selectbox("Выберите таблицу:", tables)
        if selected_table:
            data = get_table_data(selected_table)
            st.dataframe(data)

# Выбор страницы
page = st.radio("Выберите страницу:", ["Создать таблицу", "Просмотр таблиц"])

if page == "Создать таблицу":
    create_table_page()
elif page == "Просмотр таблиц":
    view_tables_page()
