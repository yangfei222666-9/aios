import sqlite3
import os
import sys

dbs = [
    r"C:\Users\A\.openclaw\workspace\aios\aios.db",
    r"C:\Users\A\.openclaw\workspace\aios\agent_system\aios.db",
    r"C:\Users\A\.openclaw\workspace\aios\storage\aios.db",
]

for db in dbs:
    if os.path.exists(db):
        before = os.path.getsize(db)
        try:
            conn = sqlite3.connect(db)
            conn.execute("VACUUM")
            conn.close()
            after = os.path.getsize(db)
            print(f"VACUUM OK: {os.path.basename(db)} {before//1024}KB -> {after//1024}KB")
        except Exception as e:
            print(f"VACUUM FAILED: {db}: {e}")
    else:
        print(f"NOT FOUND: {db}")
