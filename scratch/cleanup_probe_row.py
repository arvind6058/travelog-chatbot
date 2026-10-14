"""Remove the single driver_locations row created by the unauthenticated-write probe."""
import sqlite3, pathlib

DB = pathlib.Path(__file__).resolve().parent.parent / "backend" / "travelogix.db"
TARGET = "f63be194-f24f-42f4-bba0-7e21d6a29796"

print("DB:", DB, "exists:", DB.exists())
con = sqlite3.connect(str(DB))
cur = con.cursor()
cur.execute("SELECT id, driver_id, latitude, longitude, source FROM driver_locations WHERE id = ?", (TARGET,))
rows = cur.fetchall()
print("rows matching probe id:", rows)
if rows:
    cur.execute("DELETE FROM driver_locations WHERE id = ?", (TARGET,))
    con.commit()
    print("deleted:", cur.rowcount)
else:
    print("nothing to delete")
cur.execute("SELECT COUNT(*) FROM driver_locations")
print("driver_locations remaining:", cur.fetchone()[0])
con.close()
