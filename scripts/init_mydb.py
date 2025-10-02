# scripts/init_mydb.py
import os, sqlite3, datetime as dt
DB = os.path.join("backend","data","mydb.db")
os.makedirs(os.path.dirname(DB), exist_ok=True)
con = sqlite3.connect(DB); cur = con.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS customers(
    id INTEGER PRIMARY KEY, name TEXT NOT NULL, city TEXT )""")
cur.execute("""CREATE TABLE IF NOT EXISTS orders(
    id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL,
    amount REAL NOT NULL, created_at TEXT NOT NULL, status TEXT NOT NULL,
    FOREIGN KEY(customer_id) REFERENCES customers(id))""")

cur.executemany("INSERT INTO customers(id,name,city) VALUES(?,?,?)",
                [(1,"Aditi","Mumbai"),(2,"Rahul","Bengaluru")])
now = dt.datetime.utcnow().isoformat()
cur.executemany("INSERT INTO orders(id,customer_id,amount,created_at,status) VALUES(?,?,?,?,?)",
                [(1,1,99.0,now,"paid"),(2,2,42.5,now,"pending")])
con.commit(); con.close()
print("Created:", os.path.abspath(DB))
