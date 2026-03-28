import os
from tinydb import TinyDB, Query

if not os.path.exists("database"):
    os.makedirs("database")
if not os.path.exists("database/db.json"):
    open("database/db.json", "w").close()

db = TinyDB("database/db.json")
BillQuery = Query()
