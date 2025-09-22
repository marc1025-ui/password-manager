import json
title: str | None
username: str | None
password_ct: bytes
nonce: bytes


def add_entry(con: sqlite3.Connection, e: Entry) -> int:
cur = con.execute(
"INSERT INTO entries(url,title,username,password_ct,nonce) VALUES(?,?,?,?,?)",
(e.url, e.title, e.username, e.password_ct, e.nonce),
)
con.commit()
return int(cur.lastrowid)


def get_entry(con: sqlite3.Connection, entry_id: int) -> Optional[Entry]:
row = con.execute(
"SELECT id,url,title,username,password_ct,nonce FROM entries WHERE id=?",
(entry_id,),
).fetchone()
if not row:
return None
return Entry(*row)


def search(con: sqlite3.Connection, q: str) -> Iterable[Entry]:
q_like = f"%{q}%"
rows = con.execute(
"SELECT id,url,title,username,password_ct,nonce FROM entries WHERE url LIKE ? OR title LIKE ? OR username LIKE ? ORDER BY updated_at DESC",
(q_like, q_like, q_like),
).fetchall()
for r in rows:
yield Entry(*r)


def delete(con: sqlite3.Connection, entry_id: int) -> bool:
cur = con.execute("DELETE FROM entries WHERE id=?", (entry_id,))
con.commit()
return cur.rowcount > 0


def save_vault_meta(con: sqlite3.Connection, meta: dict) -> None:
con.execute("DELETE FROM vault_meta")
con.execute(
"INSERT INTO vault_meta(kdf_name,kdf_params,salt,verifier,version) VALUES(?,?,?,?,?)",
(meta["kdf_name"], json.dumps(meta["kdf_params"]), meta["salt"], meta["verifier"], meta["version"]),
)
con.commit()


def load_vault_meta(con: sqlite3.Connection) -> dict | None:
row = con.execute("SELECT kdf_name,kdf_params,salt,verifier,version FROM vault_meta").fetchone()
if not row:
return None
kdf_name, kdf_params, salt, verifier, version = row
return {
"kdf_name": kdf_name,
"kdf_params": json.loads(kdf_params),
"salt": salt,
"verifier": verifier,
"version": version,
}