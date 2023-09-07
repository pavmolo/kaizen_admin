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

def get_referenced_table(table_name, column_name):
    """Получение таблицы, на которую ссылается внешний ключ."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT cl.relname AS referenced_table
                FROM pg_constraint AS con
                JOIN pg_class AS cl ON con.confrelid = cl.oid
                JOIN pg_attribute AS att ON att.attnum = ANY(con.conkey)
                WHERE con.conrelid = '{table_name}'::regclass AND att.attname = '{column_name}';
            """)
            result = cursor.fetchone()
            referenced_table = result[0] if result else None
            return referenced_table


def add_foreign_key(table_name, column_name, reference_table, reference_column):
    """Добавление внешнего ключа к столбцу."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            sql = f"ALTER TABLE {table_name} ADD FOREIGN KEY ({column_name}) REFERENCES {reference_table}({reference_column});"
            cursor.execute(sql)
            conn.commit()
def get_foreign_keys(table_name):
    """Получение списка столбцов, которые являются внешними ключами для указанной таблицы."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT kcu.column_name 
                FROM information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name='{table_name}';
            """)
            return [row[0] for row in cursor.fetchall()]

def get_unique_values(table_name, column_name):
    """Получение уникальных значений из указанного столбца таблицы."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT DISTINCT {column_name} FROM {table_name};")
            return [row[0] for row in cursor.fetchall()]
            
data_types = {
    "Целое число 🔢": "INTEGER",
    "Текст 🅰️": "VARCHAR",
    "Длинный текст 📝": "TEXT",
    "Дата 📅": "DATE",
    "Дробное число 📊": "FLOAT"
}
DATA_TYPE_TO_ICON = {
    "INTEGER": "🔢",
    "VARCHAR": "🅰️",
    "TEXT": "📝",
    "DATE": "📅",
    "FLOAT": "📊"
}
# Словарь, устанавливающий соответствие между типами данных и функциями ввода Streamlit
DATA_TYPE_TO_INPUT = {
    "TEXT": st.text_input,
    "VARCHAR": st.text_input,
    "DATE": st.date_input,
    "FLOAT": st.number_input,
    "INTEGER": st.number_input
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

def get_column_data_type(table_name, column_name):
    """Получение типа данных для указанного столбца."""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT data_type FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = '{column_name}';")
            result = cursor.fetchone()
            return result[0].upper() if result else None


def update_table_data(table_name, key_column, key_value, data):
    """Обновление данных в таблице."""
    set_clause = ", ".join([f"{column} = %s" for column in data.keys()])
    sql = f"UPDATE {table_name} SET {set_clause} WHERE {key_column} = %s;"
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, list(data.values()) + [key_value])
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
        foreign_keys = get_foreign_keys(table_name)

        # Если ключевой столбец найден, добавьте иконку ключа к нему
        if key_column and key_column in data.columns:
            data = data.rename(columns={key_column: f"🔑 {key_column}"})

        # Добавление иконки скрепки к столбцам с внешними ключами
        for fk in foreign_keys:
            if fk in data.columns:
                data = data.rename(columns={fk: f"📎 {fk}"})

        # Выведите обновленный DataFrame в Streamlit
        st.dataframe(data)
        st.write("---")  # Разделитель между таблицами

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
    action = st.radio("Выберите действие", ["Изменить тип данных", "Переименовать столбец", "Добавить внешний ключ"])
    
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

    elif action == "Добавить внешний ключ":
            column_name = st.selectbox("Выберите столбец для внешнего ключа", get_table_columns(table_name))
            reference_table = st.selectbox("Выберите таблицу-источник", get_tables())
            reference_column = st.selectbox("Выберите столбец в таблице-источнике", get_table_columns(reference_table))
            if st.button("Добавить внешний ключ"):
                add_foreign_key(table_name, column_name, reference_table, reference_column)
                st.success(f"Внешний ключ для {column_name} успешно добавлен!")


def add_row_interface():
    st.subheader("Добавление новой строки в таблицу")
    table_name = st.selectbox("Выберите таблицу", get_tables())
    columns = get_table_columns(table_name)
    
    with st.form(key='add_row_form'):
        data_dict = {}
        for col in columns:
            col_data_type = get_column_data_type(table_name, col)
            icon = DATA_TYPE_TO_ICON.get(col_data_type, "")
            referenced_table = get_referenced_table(table_name, col)
            
            if referenced_table:
                ref_primary_key = get_primary_key(referenced_table)
                possible_values = get_unique_values(referenced_table, ref_primary_key)
                data_dict[col] = st.selectbox(f"Выберите значение для {col} {icon}", possible_values)
            else:
                input_function = DATA_TYPE_TO_INPUT.get(col_data_type, st.text_input)
                data_dict[col] = input_function(f"Введите значение для {col} {icon}")
        
        submit_button = st.form_submit_button("Добавить строку")
        if submit_button:
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
        with st.form(key='update_row_form'):
            for column in data.keys():
                col_data_type = get_column_data_type(table_name, column)
                icon = DATA_TYPE_TO_ICON.get(col_data_type, "")
                referenced_table = get_referenced_table(table_name, column)
                
                if referenced_table:
                    data[column] = st.selectbox(f"Выберите значение для {column} {icon}", get_unique_values(referenced_table, get_primary_key(referenced_table)), index=get_unique_values(referenced_table, get_primary_key(referenced_table)).index(data[column]))
                else:
                    input_function = DATA_TYPE_TO_INPUT.get(col_data_type, st.text_input)
                    data[column] = input_function(f"Значение для {column} {icon}", data[column])
            
            submit_button = st.form_submit_button("Обновить запись")
            if submit_button:
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
        view_tables_page()
    elif page == "Изменить строку":
        update_row_interface()
    elif page == "Удалить строку":
        delete_row_interface()
    elif page == "Удалить таблицу":
        delete_table_interface()

if __name__ == "__main__":
    main_interface()
