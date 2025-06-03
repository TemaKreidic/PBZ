import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
import hashlib
from tkcalendar import DateEntry

class DatabaseManager:
    """
    Класс-обертка для работы с базой данных.
    Инкапсулирует подключение, выполнение запросов и получение данных.
    """
    def __init__(self, connection_params):
        self.connection_params = connection_params
        self.conn = sqlite3.connect(**connection_params)
        self.cursor = self.conn.cursor()

    def get_table_names(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [row[0] for row in self.cursor.fetchall()]

    def execute(self, query, params=()):
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Ошибка БД", f"Произошла ошибка: {e}")
            return False
        return True

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def close(self):
        self.conn.close()

class DatabaseApp:
    """
    Основной класс приложения. Отвечает за интерфейс, 
    работу с виджетами и взаимодействие с базой данных через DatabaseManager.
    """
    def __init__(self, master, connection_params):
        self.master = master
        self.master.title("Военкомат")
        self.master.configure(bg="#f0f0f0")
        self.db = DatabaseManager(connection_params)

        self.setup_styles()
        self.create_header()
        self.create_report_button()

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        self.table_names = self.db.get_table_names()
        for table_name in self.table_names:
            frame = tk.Frame(self.notebook, bg="#f0f0f0")
            self.notebook.add(frame, text=table_name)
            self.create_table_view(frame, table_name)

    def setup_styles(self):
        """Настройка стилей для виджетов приложения."""
        style = ttk.Style(self.master)
        style.theme_use("clam")
        style.configure("TButton", font=("Arial", 10, "bold"), padding=6, background="#4CAF50", foreground="white")
        style.map("TButton", background=[("active", "#45a049")])
        style.configure("TLabel", font=("Arial", 10), background="#f0f0f0", foreground="#333")
        style.configure("TNotebook", background="#f0f0f0")
        style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=[10, 5])
        style.configure("Treeview", font=("Arial", 10), rowheight=25)
        style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

    def create_header(self):
        """Создание заголовка приложения."""
        header_label = tk.Label(self.master, text="Система управления военкоматом",
                                font=("Arial", 16, "bold"), bg="#f0f0f0", fg="#333")
        header_label.pack(side=tk.TOP, fill=tk.X, pady=(10, 5))

    def create_report_button(self):
        """Создание кнопки формирования отчёта."""
        report_button = ttk.Button(self.master, text="Создать отчёт", command=self.generate_report)
        report_button.pack(side=tk.TOP, padx=10, pady=5)

    def create_table_view(self, frame, table_name):
        """
        Создает представление для таблицы базы данных, включая Treeview
        и кнопки для действий (добавить, удалить, изменить, обновить).
        """
        columns_info = self.db.fetchall(f"PRAGMA table_info('{table_name}');")
        columns = [col[1] for col in columns_info]
        tree = ttk.Treeview(frame, columns=columns, show='headings', selectmode='browse')
        tree.pack(expand=True, fill='both', padx=5, pady=5)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        self.populate_treeview(tree, table_name)

        btn_frame = tk.Frame(frame, bg="#f0f0f0")
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Добавить",
                   command=lambda: self.open_row_dialog(tree, table_name, mode="add")).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Удалить",
                   command=lambda: self.delete_row(tree, table_name)).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Изменить",
                   command=lambda: self.open_row_dialog(tree, table_name, mode="edit")).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Обновить",
                   command=lambda: self.populate_treeview(tree, table_name)).grid(row=0, column=3, padx=5)

    def populate_treeview(self, tree, table_name):
        """Заполнение Treeview данными из таблицы."""
        data = self.db.fetchall(f"SELECT * FROM '{table_name}';")
        tree.delete(*tree.get_children())
        for row in data:
            tree.insert('', 'end', values=row)

    def validate_and_transform(self, table_name, columns, values):
        """
        Валидация и преобразование введенных данных для каждой таблицы.
        Например, проверка формата номера телефона или преобразование значения из комбобокса.
        """
        new_values = list(values)
        if table_name == "Граждане":
            if "Телефон" in columns:
                index = columns.index("Телефон")
                phone = new_values[index]
                phone_digits = re.sub(r'\D', '', phone)
                if len(phone_digits) < 12:
                    messagebox.showerror("Ошибка", "Номер телефона должен содержать 12 цифр.")
                    return None
                new_values[index] = f"+{phone_digits[0:3]}-{phone_digits[3:5]}-{phone_digits[5:8]}-{phone_digits[8:10]}-{phone_digits[10:12]}"
        elif table_name in ("Призывники", "Документы", "Отсрочки"):
            if "Гражданин_id" in columns:
                index = columns.index("Гражданин_id")
                citizen_val = new_values[index]
                try:
                    if ":" in citizen_val:
                        new_values[index] = int(citizen_val.split(":")[0].strip())
                    else:
                        new_values[index] = int(citizen_val)
                except ValueError:
                    messagebox.showerror("Ошибка", "Неверный формат id гражданина.")
                    return None
        return new_values

    def open_row_dialog(self, tree, table_name, mode="add"):
        """
        Универсальный диалог для добавления/редактирования записи.
        Если mode == "edit", предварительно заполняются текущие данные выбранной строки.
        """
        is_edit = (mode == "edit")
        if is_edit:
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для изменения.")
                return
            current_values = tree.item(selected)['values']
        else:
            current_values = None

        columns_info = self.db.fetchall(f"PRAGMA table_info('{table_name}');")
        columns = [col[1] for col in columns_info]

        dialog = tk.Toplevel(self.master)
        dialog.title("Изменить строку" if is_edit else "Добавить строку")
        dialog.configure(bg="#f0f0f0")

        entry_widgets = []
        for i, col in enumerate(columns):
            ttk.Label(dialog, text=col).grid(row=i, column=0, padx=10, pady=5, sticky='e')
            widget = None
            # Для полей, связанных с гражданами, используем комбобокс
            if table_name in ("Призывники", "Документы", "Отсрочки") and col == "Гражданин_id":
                citizens = self.db.fetchall("SELECT id, ФИО FROM 'Граждане';")
                citizen_values = [f"{c[0]}: {c[1]}" for c in citizens]
                widget = ttk.Combobox(dialog, state="readonly", values=citizen_values)
                if is_edit and current_values:
                    try:
                        citizen_name = self.db.fetchone("SELECT ФИО FROM 'Граждане' WHERE id = ?;", (current_values[i],))[0]
                        widget.set(f"{current_values[i]}: {citizen_name}")
                    except Exception:
                        widget.set(str(current_values[i]))
            elif table_name == "Граждане" and col == "Дата_рождения":
                widget = DateEntry(dialog, date_pattern='dd.mm.yyyy')
                if is_edit and current_values:
                    widget.set_date(current_values[i])
            elif table_name == "Призывники" and col == "Дата_призыва":
                widget = DateEntry(dialog, date_pattern='dd.mm.yyyy')
                if is_edit and current_values:
                    widget.set_date(current_values[i])
            elif table_name == "Документы" and col == "Дата_выдачи":
                widget = DateEntry(dialog, date_pattern='dd.mm.yyyy')
                if is_edit and current_values:
                    widget.set_date(current_values[i])
            elif table_name == "Отсрочки" and col in ("Дата_выдачи", "Срок_действия"):
                widget = DateEntry(dialog, date_pattern='dd.mm.yyyy')
                if is_edit and current_values:
                    widget.set_date(current_values[i])
            else:
                widget = ttk.Entry(dialog)
                if is_edit and current_values:
                    widget.insert(0, current_values[i])
            widget.grid(row=i, column=1, padx=10, pady=5, sticky='w')
            entry_widgets.append(widget)

        def on_submit():
            new_values = [w.get() for w in entry_widgets]
            validated = self.validate_and_transform(table_name, columns, new_values)
            if validated is None:
                return
            if is_edit:
                # Формирование запроса для обновления записи
                set_clause = ', '.join([f"{col} = ?" for col in columns])
                where_clause = ' AND '.join([f"{col} = ?" for col in columns])
                query = f"UPDATE '{table_name}' SET {set_clause} WHERE {where_clause};"
                if self.db.execute(query, validated + current_values):
                    self.populate_treeview(tree, table_name)
                    dialog.destroy()
            else:
                placeholders = ', '.join(['?' for _ in validated])
                query = f"INSERT INTO '{table_name}' VALUES ({placeholders});"
                if self.db.execute(query, validated):
                    self.populate_treeview(tree, table_name)
                    dialog.destroy()

        ttk.Button(dialog, text="Подтвердить", command=on_submit).grid(row=len(columns), columnspan=2, pady=10)

    def delete_row(self, tree, table_name):
        """Удаление выбранной записи с подтверждением."""
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Пожалуйста, выберите строку для удаления.")
            return
        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту строку?")
        if not confirm:
            return
        values = tree.item(selected)['values']
        columns = tree['columns']
        where_clause = ' AND '.join([f"{col} = ?" for col in columns])
        query = f"DELETE FROM '{table_name}' WHERE {where_clause};"
        if self.db.execute(query, values):
            self.populate_treeview(tree, table_name)

    def generate_report(self):
        """Формирование отчёта по базе данных и сохранение его в файл report.txt."""
        report_window = tk.Toplevel(self.master)
        report_window.title("Отчёт по базе данных")
        report_window.configure(bg="#f0f0f0")
        text_widget = tk.Text(report_window, wrap='word', width=100, height=30, font=("Arial", 10))
        text_widget.pack(expand=True, fill='both', padx=10, pady=10)
        scrollbar = tk.Scrollbar(report_window, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)

        report_lines = []
        report_lines.append("Отчёт по базе данных\n")
        report_lines.append(f"База данных: {self.db.connection_params.get('database')}\n")
        report_lines.append("=" * 80 + "\n\n")
        for table in self.table_names:
            report_lines.append(f"Таблица: {table}\n")
            columns_info = self.db.fetchall(f"PRAGMA table_info('{table}');")
            columns = [col[1] for col in columns_info]
            report_lines.append("Столбцы: " + ", ".join(columns) + "\n")
            count = self.db.fetchone(f"SELECT COUNT(*) FROM '{table}';")[0]
            report_lines.append(f"Количество записей: {count}\n")
            sample_rows = self.db.fetchall(f"SELECT * FROM '{table}' LIMIT 5;")
            if sample_rows:
                report_lines.append("Примеры записей:\n")
                for row in sample_rows:
                    report_lines.append(" | ".join([str(item) for item in row]) + "\n")
            else:
                report_lines.append("Записей нет.\n")
            report_lines.append("-" * 80 + "\n\n")
        text_widget.insert("1.0", "".join(report_lines))
        text_widget.config(state="disabled")
        with open("report.txt", "w", encoding="utf-8") as f:
            f.write("".join(report_lines))

if __name__ == "__main__":
    connection_params = {"database": "military_draft.sqlite3"}
    # Создаем таблицы, если они отсутствуют
    conn = sqlite3.connect(**connection_params)
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Граждане" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "ФИО" TEXT NOT NULL,
        "Дата_рождения" TEXT,
        "Адрес" TEXT,
        "Телефон" TEXT,
        "Email" TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Призывники" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Гражданин_id" INTEGER,
        "Дата_призыва" TEXT,
        "Статус" TEXT,
        FOREIGN KEY("Гражданин_id") REFERENCES "Граждане"("id")
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Документы" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Гражданин_id" INTEGER,
        "Тип_документа" TEXT,
        "Номер" TEXT,
        "Дата_выдачи" TEXT,
        FOREIGN KEY("Гражданин_id") REFERENCES "Граждане"("id")
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Сотрудники" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "ФИО" TEXT NOT NULL,
        "Должность" TEXT,
        "Отдел" TEXT
    );
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS "Отсрочки" (
        "id" INTEGER PRIMARY KEY AUTOINCREMENT,
        "Гражданин_id" INTEGER,
        "Причина" TEXT,
        "Дата_выдачи" TEXT,
        "Срок_действия" TEXT,
        FOREIGN KEY("Гражданин_id") REFERENCES "Граждане"("id")
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
