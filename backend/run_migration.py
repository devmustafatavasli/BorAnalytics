import os
import sys
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from db.database import engine

def run():
    with engine.begin() as conn:
        with open("../migrations/009_events_table.sql", "r") as f:
            conn.execute(text(f.read()))

if __name__ == "__main__":
    run()
