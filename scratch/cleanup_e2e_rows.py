"""
Remove ONLY the rows created by the end-to-end verification run:
  * customers matching 'e2e-<digits>@example.com' / 'other-<digits>@example.com'
  * the shipment TLX-85471E31 registered for the e2e customer
  * their conversations, messages, events and audit rows

Everything else in the development database is left untouched.
Order matters: foreign keys are now enforced.
"""
import pathlib
import re
import sqlite3

DB = pathlib.Path(__file__).resolve().parent.parent / "backend" / "travelogix.db"
EMAIL_RE = r"^(e2e|other)-[0-9]+@example\.com$"
TRACKING = "TLX-85471E31"

con = sqlite3.connect(str(DB))
con.execute("PRAGMA foreign_keys=ON")
cur = con.cursor()

cur.execute("SELECT id, email FROM users WHERE email GLOB 'e2e-*@example.com' OR email GLOB 'other-*@example.com'")
users = [(uid, email) for uid, email in cur.fetchall() if re.match(EMAIL_RE, email)]
print("test customers found:", users)
if not users:
    print("nothing to clean")
    raise SystemExit(0)

ids = [uid for uid, _ in users]
emails = [email for _, email in users]
placeholders = ",".join("?" * len(ids))
email_placeholders = ",".join("?" * len(emails))

shipments = cur.execute(
    f"SELECT id, tracking_id FROM shipments WHERE customer_id IN ({placeholders}) OR tracking_id = ?",
    (*ids, TRACKING),
).fetchall()
print("test shipments found:", shipments)
shipment_ids = [s[0] for s in shipments]

if shipment_ids:
    sp = ",".join("?" * len(shipment_ids))
    cur.execute(f"DELETE FROM shipment_events WHERE shipment_id IN ({sp})", shipment_ids)
    print("  deleted shipment_events:", cur.rowcount)
    cur.execute(f"DELETE FROM shipment_driver_assignments WHERE shipment_id IN ({sp})", shipment_ids)
    print("  deleted assignments:", cur.rowcount)
    cur.execute(f"DELETE FROM shipments WHERE id IN ({sp})", shipment_ids)
    print("  deleted shipments:", cur.rowcount)

conversations = cur.execute(
    f"SELECT id FROM conversations WHERE customer_email IN ({email_placeholders})", emails
).fetchall()
if conversations:
    cids = [c[0] for c in conversations]
    cp = ",".join("?" * len(cids))
    cur.execute(f"DELETE FROM ai_messages WHERE conversation_id IN ({cp})", cids)
    print("  deleted ai_messages:", cur.rowcount)
    cur.execute(f"DELETE FROM conversations WHERE id IN ({cp})", cids)
    print("  deleted conversations:", cur.rowcount)

cur.execute(f"DELETE FROM audit_logs WHERE actor IN ({email_placeholders})", emails)
print("  deleted audit_logs:", cur.rowcount)
cur.execute(f"DELETE FROM users WHERE id IN ({placeholders})", ids)
print("  deleted users:", cur.rowcount)

con.commit()

cur.execute("SELECT COUNT(*) FROM users")
cur.execute("SELECT COUNT(*) FROM shipments")
print("remaining users:", cur.execute("SELECT COUNT(*) FROM users").fetchone()[0])
print("remaining shipments:", cur.execute("SELECT COUNT(*) FROM shipments").fetchone()[0])
con.close()
