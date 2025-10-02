# scripts/init_db.py
import sqlite3, os, datetime as dt

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "app.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS customers(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  city TEXT
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders(
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL,
  amount REAL NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL,
  FOREIGN KEY(customer_id) REFERENCES customers(id)
);
""")

cur.execute("DELETE FROM customers;")
cur.execute("DELETE FROM orders;")

customers = [
  (1, "Aditi", "Mumbai"),
  (2, "Rahul", "Bengaluru"),
  (3, "Priya", "Chennai"),
  (4, "Vikram", "Pune"),
]
cur.executemany("INSERT INTO customers(id,name,city) VALUES(?,?,?)", customers)

now = dt.datetime.utcnow()
orders = []
for i in range(1, 31):
    orders.append((i, (i % 4) + 1, round(50 + i*3.2, 2),
                   (now - dt.timedelta(days=i)).isoformat(),
                   ["pending","paid","refunded"][i % 3]))
cur.executemany("INSERT INTO orders(id,customer_id,amount,created_at,status) VALUES(?,?,?,?,?)", orders)

conn.commit()
conn.close()
print("DB initialized at:", os.path.abspath(DB_PATH))
