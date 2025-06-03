import sqlite3
import random

def create_database():
    conn = sqlite3.connect(':memory:')
    cur = conn.cursor()
    
    # Создание таблиц
    cur.executescript("""
    CREATE TABLE users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        email TEXT,
        Примечание REAL
    );
    
    CREATE TABLE tableA (a_id INTEGER PRIMARY KEY AUTOINCREMENT, dataA TEXT);
    CREATE TABLE tableB (b_id INTEGER PRIMARY KEY AUTOINCREMENT, a_id INTEGER, dataB TEXT,
        FOREIGN KEY(a_id) REFERENCES tableA(a_id));
    CREATE TABLE tableC (c_id INTEGER PRIMARY KEY AUTOINCREMENT, b_id INTEGER, dataC TEXT, Примечание REAL,
        FOREIGN KEY(b_id) REFERENCES tableB(b_id));
    CREATE TABLE tableD (d_id INTEGER PRIMARY KEY AUTOINCREMENT, c_id INTEGER, dataD TEXT,
        FOREIGN KEY(c_id) REFERENCES tableC(c_id));
    """)
    
    # Заполнение users
    users_data = [
        (1, "Смирнова Анна", "anna.smirnova@example.com", random.uniform(50, 300)),
        (2, "Иванов Петр", "petr.ivanov@example.com", random.uniform(50, 300))
    ]
    cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users_data)
    
    # Создание триггеров
    cur.executescript("""
    CREATE TRIGGER trigger_insert_update
    AFTER INSERT ON users
    BEGIN
        UPDATE users SET Примечание = Примечание * 1.1 WHERE user_id = NEW.user_id;
    END;
    
    CREATE TRIGGER trigger_delete
    BEFORE DELETE ON users
    BEGIN
        SELECT RAISE(FAIL, 'Удаление запрещено!');
    END;
    """)
    
    # Создание представлений (функций)
    cur.executescript("""
    CREATE VIEW view_aggregates AS
    SELECT MIN(Примечание) AS min_note, MAX(Примечание) AS max_note, AVG(Примечание) AS avg_note, SUM(Примечание) AS sum_note FROM users;
    
    CREATE VIEW view_count AS
    SELECT COUNT(*) AS count_rows FROM users WHERE Примечание <= (SELECT MIN(Примечание) FROM users) + 50;
    
    CREATE VIEW view_filtered AS
    SELECT * FROM users WHERE user_id <= (SELECT AVG(Примечание) FROM users) / 100;
    """)
    conn.commit()
    return conn, cur

def test_triggers_and_functions(cur):
    # Проверка триггера на вставку
    cur.execute("INSERT INTO users VALUES (3, 'Козлова Мария', 'maria.kozlova@example.com', 120.0)")
    cur.execute("SELECT * FROM users WHERE user_id = 3")
    print("После вставки:", cur.fetchone())
    
    # Проверка триггера на удаление
    try:
        cur.execute("DELETE FROM users WHERE user_id = 1")
    except sqlite3.DatabaseError as e:
        print("Ошибка удаления:", e)
    
    # Проверка агрегатных функций
    print("Агрегатные функции:")
    for row in cur.execute("SELECT * FROM view_aggregates"):
        print(row)
    
    print("Строк в диапазоне:")
    for row in cur.execute("SELECT * FROM view_count"):
        print(row)
    
    print("Фильтрованные пользователи:")
    for row in cur.execute("SELECT * FROM view_filtered"):
        print(row)
    
if __name__ == "__main__":
    conn, cur = create_database()
    test_triggers_and_functions(cur)
    conn.close()
