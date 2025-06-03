import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
import hashlib
from tkcalendar import DateEntry  # Импорт виджета календаря

class DatabaseApp:
    def __init__(self, master, connection_params):
        self.master = master
        self.connection_params = connection_params
        self.master.title("БД")

        # Кнопка для создания отчёта
        report_button = tk.Button(master, text="Создать отчёт", command=self.generate_report)
        report_button.pack(side=tk.TOP, padx=10, pady=10)

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both')

        # Подключаемся к базе данных
        self.conn = sqlite3.connect(**connection_params)
        self.cursor = self.conn.cursor()

        # Получаем имена таблиц
        self.table_names = self.get_table_names()

        # Создаем вкладку для каждой таблицы
        for table_name in self.table_names:
            frame = tk.Frame(self.notebook)
            self.notebook.add(frame, text=table_name)
            self.create_table_view(frame, table_name)

    def get_table_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in self.cursor.fetchall()]
        return table_names

    def create_table_view(self, frame, table_name):
        self.cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = [row[1] for row in self.cursor.fetchall()]

        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        tree.pack(expand=True, fill='both')

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')

        self.populate_treeview(tree, table_name)

        add_button = tk.Button(frame, text="Добавить", command=lambda: self.add_row(tree, table_name))
        add_button.pack(side=tk.LEFT, padx=10)
        delete_button = tk.Button(frame, text="Удалить", command=lambda: self.delete_row(tree, table_name))
        delete_button.pack(side=tk.LEFT, padx=10)
        edit_button = tk.Button(frame, text="Изменить", command=lambda: self.edit_row(tree, table_name))
        edit_button.pack(side=tk.LEFT, padx=10)
        refresh_button = tk.Button(frame, text="Обновить", command=lambda: self.populate_treeview(tree, table_name))
        refresh_button.pack(side=tk.LEFT, padx=10)

    def populate_treeview(self, tree, table_name):
        self.cursor.execute(f"SELECT * FROM '{table_name}';")
        data = self.cursor.fetchall()
        tree.delete(*tree.get_children())
        for row in data:
            tree.insert('', 'end', values=row)

    def validate_and_transform(self, table_name, columns, values):
        """Проверяет и преобразует значения в зависимости от таблицы и поля."""
        new_values = list(values)
        if table_name == "Пользователи":
            if "Email" in columns:
                index = columns.index("Email")
                email = new_values[index].strip()
                if not re.match(r'^[^@]+@(gmail\.com|mail\.ru|inbox\.ru)$', email):
                    messagebox.showerror("Ошибка", "Неверный формат Email. Допустимые домены: gmail.com, mail.ru, inbox.ru.")
                    return None
                new_values[index] = email
            if "Пароль" in columns:
                index = columns.index("Пароль")
                password = new_values[index]
                hashed = hashlib.sha256(password.encode()).hexdigest()
                new_values[index] = hashed

        elif table_name == "Продукты":
            if "Цена" in columns:
                index = columns.index("Цена")
                price_str = new_values[index].strip()
                try:
                    new_values[index] = float(price_str)
                except ValueError:
                    messagebox.showerror("Ошибка", "Цена должна быть числом без букв.")
                    return None

        elif table_name == "Поставщики":
            if "Телефон" in columns:
                index = columns.index("Телефон")
                phone = new_values[index]
                phone_digits = re.sub(r'\D', '', phone)
                if len(phone_digits) != 11:
                    messagebox.showerror("Ошибка", "Номер телефона должен содержать 11 цифр.")
                    return None
                formatted_phone = f"+{phone_digits[0]}-{phone_digits[1:4]}-{phone_digits[4:7]}-{phone_digits[7:9]}-{phone_digits[9:11]}"
                new_values[index] = formatted_phone

        elif table_name == "Заказы":
            # Обработка поля "Пользователь_id"
            if "Пользователь_id" in columns:
                index = columns.index("Пользователь_id")
                user_val = new_values[index]
                if ":" in user_val:
                    try:
                        new_values[index] = int(user_val.split(":")[0].strip())
                    except ValueError:
                        messagebox.showerror("Ошибка", "Неверный формат id пользователя.")
                        return None
                else:
                    try:
                        new_values[index] = int(user_val)
                    except ValueError:
                        messagebox.showerror("Ошибка", "Неверный формат id пользователя.")
                        return None
            # Обработка поля "Сумма"
            if "Сумма" in columns:
                index = columns.index("Сумма")
                sum_str = new_values[index].strip()
                try:
                    new_values[index] = float(sum_str)
                except ValueError:
                    messagebox.showerror("Ошибка", "Сумма должна быть числом.")
                    return None
            # Поле "Дата" предполагается в формате, выбранном через DateEntry (например, dd.mm.yyyy)
        return new_values

    def add_row(self, tree, table_name):
        self.cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = [row[1] for row in self.cursor.fetchall()]

        add_dialog = tk.Toplevel(self.master)
        add_dialog.title("Добавить строку")

        entry_widgets = []
        # Используем enumerate для корректного размещения виджетов
        for index, col in enumerate(columns):
            label = tk.Label(add_dialog, text=col)
            label.grid(row=index, column=0, padx=10, pady=5, sticky='e')
            # Для таблицы "Заказы" создаем специальные виджеты для "Пользователь_id" и "Дата"
            if table_name == "Заказы" and col == "Пользователь_id":
                self.cursor.execute("SELECT id, Имя FROM 'Пользователи';")
                users = self.cursor.fetchall()
                user_values = [f"{user[0]}: {user[1]}" for user in users]
                combobox = ttk.Combobox(add_dialog, state="readonly")
                combobox['values'] = user_values
                combobox.grid(row=index, column=1, padx=10, pady=5, sticky='w')
                entry_widgets.append(combobox)
            elif table_name == "Заказы" and col == "Дата":
                date_entry = DateEntry(add_dialog, date_pattern='dd.mm.yyyy')
                date_entry.grid(row=index, column=1, padx=10, pady=5, sticky='w')
                entry_widgets.append(date_entry)
            else:
                entry = tk.Entry(add_dialog)
                entry.grid(row=index, column=1, padx=10, pady=5, sticky='w')
                entry_widgets.append(entry)

        def insert_row():
            # Получаем значения из виджетов. Для виджетов типа DateEntry и Combobox метод get() работает аналогично.
            values = [widget.get() for widget in entry_widgets]
            validated_values = self.validate_and_transform(table_name, columns, values)
            if validated_values is None:
                return
            placeholders = ', '.join(['?' for _ in validated_values])
            query = f"INSERT INTO '{table_name}' VALUES ({placeholders});"
            self.cursor.execute(query, validated_values)
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            add_dialog.destroy()

        submit_button = tk.Button(add_dialog, text="Подтвердить", command=insert_row)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def delete_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для удаления.")
            return
        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту строку?")
        if not confirm:
            return
        values = tree.item(selected_item)['values']
        where_clause = ' AND '.join([f"{column} = ?" for column in tree['columns']])
        query = f"DELETE FROM '{table_name}' WHERE {where_clause};"
        self.cursor.execute(query, values)
        self.conn.commit()
        self.populate_treeview(tree, table_name)

    def edit_row(self, tree, table_name):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для изменения.")
            return

        values = tree.item(selected_item)['values']
        self.cursor.execute(f"PRAGMA table_info('{table_name}');")
        columns = [row[1] for row in self.cursor.fetchall()]

        edit_dialog = tk.Toplevel(self.master)
        edit_dialog.title("Изменить строку")

        entry_widgets = []
        for index, (col, value) in enumerate(zip(columns, values)):
            label = tk.Label(edit_dialog, text=col)
            label.grid(row=index, column=0, padx=10, pady=5, sticky='e')
            if table_name == "Заказы" and col == "Пользователь_id":
                self.cursor.execute("SELECT id, Имя FROM 'Пользователи';")
                users = self.cursor.fetchall()
                user_values = [f"{user[0]}: {user[1]}" for user in users]
                combobox = ttk.Combobox(edit_dialog, state="readonly")
                combobox['values'] = user_values
                # Пытаемся установить текущее значение (если в базе хранится только id)
                try:
                    self.cursor.execute("SELECT Имя FROM 'Пользователи' WHERE id = ?;", (value,))
                    user_name = self.cursor.fetchone()[0]
                    combobox.set(f"{value}: {user_name}")
                except Exception:
                    combobox.set(str(value))
                combobox.grid(row=index, column=1, padx=10, pady=5, sticky='w')
                entry_widgets.append(combobox)
            elif table_name == "Заказы" and col == "Дата":
                date_entry = DateEntry(edit_dialog, date_pattern='dd.mm.yyyy')
                date_entry.set_date(value)
                date_entry.grid(row=index, column=1, padx=10, pady=5, sticky='w')
                entry_widgets.append(date_entry)
            else:
                entry = tk.Entry(edit_dialog)
                entry.insert(0, value)
                entry.grid(row=index, column=1, padx=10, pady=5, sticky='w')
                entry_widgets.append(entry)

        def update_row():
            new_values = [widget.get() for widget in entry_widgets]
            validated_values = self.validate_and_transform(table_name, columns, new_values)
            if validated_values is None:
                return
            set_clause = ', '.join([f"{column} = ?" for column in columns])
            where_clause = ' AND '.join([f"{column} = ?" for column in columns])
            query = f"UPDATE '{table_name}' SET {set_clause} WHERE {where_clause};"
            self.cursor.execute(query, validated_values + values)
            self.conn.commit()
            self.populate_treeview(tree, table_name)
            edit_dialog.destroy()

        submit_button = tk.Button(edit_dialog, text="Подтвердить", command=update_row)
        submit_button.grid(row=len(columns), columnspan=2, pady=10)

    def generate_report(self):
        report_window = tk.Toplevel(self.master)
        report_window.title("Отчёт по базе данных")
        text_widget = tk.Text(report_window, wrap='word', width=100, height=30)
        text_widget.pack(expand=True, fill='both')
        scrollbar = tk.Scrollbar(report_window, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)

        report_lines = []
        report_lines.append("Отчёт по базе данных\n")
        report_lines.append(f"База данных: {self.connection_params.get('database')}\n")
        report_lines.append("=" * 80 + "\n\n")
        for table in self.table_names:
            report_lines.append(f"Таблица: {table}\n")
            self.cursor.execute(f"PRAGMA table_info('{table}');")
            columns_info = self.cursor.fetchall()
            columns = [col[1] for col in columns_info]
            report_lines.append("Столбцы: " + ", ".join(columns) + "\n")
            self.cursor.execute(f"SELECT COUNT(*) FROM '{table}';")
            count = self.cursor.fetchone()[0]
            report_lines.append(f"Количество записей: {count}\n")
            self.cursor.execute(f"SELECT * FROM '{table}' LIMIT 5;")
            sample_rows = self.cursor.fetchall()
            if sample_rows:
                report_lines.append("Примеры записей:\n")
                for row in sample_rows:
                    row_str = " | ".join([str(item) for item in row])
                    report_lines.append(row_str + "\n")
            else:
                report_lines.append("Записей нет.\n")
            report_lines.append("-" * 80 + "\n\n")
        text_widget.insert("1.0", "".join(report_lines))
        text_widget.config(state="disabled")
        with open("report.txt", "w", encoding="utf-8") as file:
            file.write("".join(report_lines))
        
        

if __name__ == "__main__":
    connection_params = {"database": "mydb.sqlite3"}
    conn = sqlite3.connect(**connection_params)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Пользователи" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Имя" TEXT NOT NULL,
        "Email" TEXT,
        "Пароль" TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Заказы" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Пользователь_id" INTEGER,
        "Дата" TEXT,
        "Сумма" REAL,
        FOREIGN KEY("Пользователь_id") REFERENCES "Пользователи"("id")
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Продукты" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Название" TEXT NOT NULL,
        "Цена" REAL,
        "Описание" TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Категории" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Название" TEXT NOT NULL
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Сотрудники" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Имя" TEXT NOT NULL,
        "Должность" TEXT,
        "Отдел" TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Поставщики" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Название" TEXT NOT NULL,
        "Контактное_лицо" TEXT,
        "Телефон" TEXT
    );
    ''')

    conn.commit()
    conn.close()

    try:
        root = tk.Tk()
        app = DatabaseApp(root, connection_params)
        root.mainloop()
    except sqlite3.Error as err:
        print(f"Error: {err}")
