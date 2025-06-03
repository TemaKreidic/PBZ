import sqlite3
import random

# Создаём/подключаемся к базе данных в памяти (можно заменить ':memory:' на имя файла)
conn = sqlite3.connect(':memory:')
cur = conn.cursor()

# ---------------------------------------
# Часть 1. Создаём таблицу users
# ---------------------------------------
cur.execute("""
DROP TABLE IF EXISTS users
""")

cur.execute("""
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    email TEXT
)
""")

# Вставляем данные (user_id задаём вручную, чтобы соответствовало примеру)
users_data = [
    (1, "Смирнова Анна",       "anna.smirnova@example.com"),
    (2, "Иванов Петр",         "petr.ivanov@example.com"),
    (3, "Козлова Мария",       "maria.kozlova@example.com"),
    (4, "Соколова Екатерина",  "ekaterina.sokolova@example.com"),
    (5, "Попов Алексей",       "alexey.popov@example.com")
]
cur.executemany("""
INSERT INTO users (user_id, username, email)
VALUES (?, ?, ?)
""", users_data)
conn.commit()

# Добавляем столбец «Примечание» (REAL) и заполняем случайными дробными значениями [50..300]
cur.execute("ALTER TABLE users ADD COLUMN Примечание REAL")
conn.commit()

cur.execute("SELECT user_id FROM users")
rows = cur.fetchall()
for (uid,) in rows:
    note_value = round(random.uniform(50, 300), 2)
    cur.execute("""
        UPDATE users
        SET Примечание = ?
        WHERE user_id = ?
    """, (note_value, uid))
conn.commit()

# Создаём представления (views) для Задания 1

# 1) Агрегатные функции (MIN, MAX, AVG, SUM) с двумя знаками после запятой
cur.execute("""
CREATE VIEW view_aggregates AS
SELECT
    printf('%.2f', MIN(Примечание)) AS min_note,
    printf('%.2f', MAX(Примечание)) AS max_note,
    printf('%.2f', AVG(Примечание)) AS avg_note,
    printf('%.2f', SUM(Примечание)) AS sum_note
FROM users
""")

# 2) Подсчёт количества строк, где «Примечание» <= MIN(Примечание)+50
cur.execute("""
CREATE VIEW view_count AS
SELECT
    COUNT(*) AS count_rows
FROM users
WHERE Примечание <= (
    SELECT MIN(Примечание) FROM users
) + 50
""")

# 3) Выбор строк, где user_id <= (AVG(Примечание)/100)
cur.execute("""
CREATE VIEW view_filtered AS
SELECT *
FROM users
WHERE user_id <= (
    SELECT AVG(Примечание) FROM users
) / 100
""")

# Проверим вывод из созданных представлений
print("=== Задание 1: Представление view_aggregates ===")
for row in cur.execute("SELECT * FROM view_aggregates"):
    print(row)

print("\n=== Задание 1: Представление view_count ===")
for row in cur.execute("SELECT * FROM view_count"):
    print(row)

print("\n=== Задание 1: Представление view_filtered ===")
for row in cur.execute("SELECT * FROM view_filtered"):
    print(row)

# ---------------------------------------
# Часть 2. Цепочка из четырёх таблиц
# ---------------------------------------
# Удаляем, если уже есть
cur.execute("DROP TABLE IF EXISTS tableD")
cur.execute("DROP TABLE IF EXISTS tableC")
cur.execute("DROP TABLE IF EXISTS tableB")
cur.execute("DROP TABLE IF EXISTS tableA")

# Создаём таблицы: tableA -> tableB -> tableC -> tableD
cur.execute("""
CREATE TABLE tableA (
    a_id INTEGER PRIMARY KEY AUTOINCREMENT,
    dataA TEXT
)
""")

cur.execute("""
CREATE TABLE tableB (
    b_id INTEGER PRIMARY KEY AUTOINCREMENT,
    a_id INTEGER,
    dataB TEXT,
    FOREIGN KEY(a_id) REFERENCES tableA(a_id)
)
""")

cur.execute("""
CREATE TABLE tableC (
    c_id INTEGER PRIMARY KEY AUTOINCREMENT,
    b_id INTEGER,
    dataC TEXT,
    Примечание REAL,
    FOREIGN KEY(b_id) REFERENCES tableB(b_id)
)
""")

cur.execute("""
CREATE TABLE tableD (
    d_id INTEGER PRIMARY KEY AUTOINCREMENT,
    c_id INTEGER,
    dataD TEXT,
    FOREIGN KEY(c_id) REFERENCES tableC(c_id)
)
""")

# Заполняем таблицы тестовыми данными
cur.execute("INSERT INTO tableA (dataA) VALUES ('A_item1')")
cur.execute("INSERT INTO tableA (dataA) VALUES ('A_item2')")
cur.execute("INSERT INTO tableA (dataA) VALUES ('A_item3')")

cur.execute("INSERT INTO tableB (a_id, dataB) VALUES (1, 'B_item1')")
cur.execute("INSERT INTO tableB (a_id, dataB) VALUES (2, 'B_item2')")
cur.execute("INSERT INTO tableB (a_id, dataB) VALUES (3, 'B_item3')")

# В tableC вставляем случайные Примечание в диапазоне [50..300]
for i in range(1, 4):
    note_val = round(random.uniform(50, 300), 2)
    dataC_val = f"C_item{i}"
    cur.execute("""
        INSERT INTO tableC (b_id, dataC, Примечание)
        VALUES (?, ?, ?)
    """, (i, dataC_val, note_val))

cur.execute("INSERT INTO tableD (c_id, dataD) VALUES (1, 'D_item1')")
cur.execute("INSERT INTO tableD (c_id, dataD) VALUES (2, 'D_item2')")
cur.execute("INSERT INTO tableD (c_id, dataD) VALUES (3, 'D_item3')")

conn.commit()

# Вычислим среднее Примечание в tableC (для наглядности)
cur.execute("SELECT AVG(Примечание) FROM tableC")
avg_note = cur.fetchone()[0]
print(f"\nСреднее значение Примечание в tableC: {avg_note:.2f}\n")

# Задание 2.1: Запрос с оператором JOIN
join_query = """
SELECT
    A.dataA AS a_data,
    D.dataD AS d_data,
    C.Примечание AS c_note
FROM tableA A
JOIN tableB B ON A.a_id = B.a_id
JOIN tableC C ON B.b_id = C.b_id
JOIN tableD D ON C.c_id = D.c_id
WHERE C.Примечание >= (SELECT AVG(Примечание) FROM tableC)
"""

print("=== Задание 2 (JOIN) ===")
for row in cur.execute(join_query):
    print(row)

# Задание 2.2: Запрос с подзапросами (без JOIN)
subquery = """
SELECT
    A.dataA AS a_data,
    D.dataD AS d_data,
    (SELECT Примечание
     FROM tableC
     WHERE tableC.c_id = D.c_id
    ) AS c_note
FROM tableA A, tableD D
WHERE A.a_id IN (
    SELECT b.a_id
    FROM tableB b
    WHERE b.b_id IN (
        SELECT c.b_id
        FROM tableC c
        WHERE c."Примечание" >= (SELECT AVG(Примечание) FROM tableC)
          AND c.c_id IN (SELECT d.c_id FROM tableD d)
    )
)
AND D.c_id IN (
    SELECT c.c_id
    FROM tableC c
    WHERE c."Примечание" >= (SELECT AVG(Примечание) FROM tableC)
)
"""

print("\n=== Задание 2 (подзапросы без JOIN) ===")
for row in cur.execute(subquery):
    print(row)

conn.close()
