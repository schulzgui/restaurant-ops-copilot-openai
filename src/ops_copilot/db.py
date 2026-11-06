"""Transactional proposals, optimistic versions, outbox and hash-linked audit."""
import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from .domain import DomainError, bounded_text, validate_proposal
from .seed import fixtures


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS orders(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, idem TEXT UNIQUE NOT NULL, digest TEXT NOT NULL, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, body TEXT NOT NULL, previous TEXT NOT NULL, hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbox(proposal_id TEXT PRIMARY KEY, attempts INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL DEFAULT 'pending');
                CREATE TABLE IF NOT EXISTS receipts(proposal_id TEXT PRIMARY KEY, body TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, body TEXT NOT NULL);
                PRAGMA user_version=1;
            """)
            for order in fixtures():
                db.execute("INSERT OR IGNORE INTO orders VALUES (?,?)", (order["id"], canonical(order)))

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def _event(self, db, event):
        previous = db.execute("SELECT hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        previous = previous[0] if previous else "0" * 64
        body = canonical({"time": time.time(), **event})
        digest = hashlib.sha256((previous + body).encode()).hexdigest()
        db.execute("INSERT INTO audit(body,previous,hash) VALUES (?,?,?)", (body, previous, digest))

    def orders(self):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT body FROM orders ORDER BY id")]

    def order(self, order_id):
        with self.connection() as db:
            row = db.execute("SELECT body FROM orders WHERE id=?", (order_id,)).fetchone()
        if row is None:
            raise DomainError("Pedido inexistente")
        return json.loads(row[0])

    def propose(self, order_id, template, policy_id, key):
        key = bounded_text(key, "idempotency_key", 150)
        digest = hashlib.sha256(canonical([order_id, template, policy_id]).encode()).hexdigest()
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT digest,body FROM proposals WHERE idem=?", (key,)).fetchone()
            if old:
                if old[0] != digest:
                    raise DomainError("Chave de idempotência reutilizada com conteúdo diferente")
                return json.loads(old[1])
            row = db.execute("SELECT body FROM orders WHERE id=?", (order_id,)).fetchone()
            if not row:
                raise DomainError("Pedido inexistente")
            order = json.loads(row[0])
            proposal = {"id": str(uuid.uuid4()), "order_id": order_id, "order_version": order["version"], "version": 1, "state": "pending_review", "synthetic": True, **validate_proposal(order, template, policy_id)}
            db.execute("INSERT INTO proposals VALUES (?,?,?,?)", (proposal["id"], key, digest, canonical(proposal)))
            self._event(db, {"type": "proposal_created", "proposal": proposal})
            return proposal

    def proposals(self):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT body FROM proposals ORDER BY rowid DESC")]

    def review(self, proposal_id, decision, reviewer, version):
        reviewer = bounded_text(reviewer, "reviewer", 80)
        if decision not in {"approve", "reject"} or type(version) is not int:
            raise DomainError("Decisão ou versão inválida")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM proposals WHERE id=?", (proposal_id,)).fetchone()
            if not row:
                raise DomainError("Proposta inexistente")
            p = json.loads(row[0])
            if p["state"] != "pending_review" or p["version"] != version:
                raise DomainError("Proposta já revisada ou versão desatualizada")
            order = json.loads(db.execute("SELECT body FROM orders WHERE id=?", (p["order_id"],)).fetchone()[0])
            if decision == "approve":
                if p["order_version"] != order["version"]:
                    raise DomainError("Pedido mudou; gere outra proposta")
                validate_proposal(order, p["template"], p["policy_id"])
            p.update(state="approved" if decision == "approve" else "rejected", reviewer=reviewer, version=p["version"] + 1)
            db.execute("UPDATE proposals SET body=? WHERE id=?", (canonical(p), proposal_id))
            if decision == "approve":
                db.execute("INSERT INTO outbox(proposal_id) VALUES (?)", (proposal_id,))
            self._event(db, {"type": "review", "proposal_id": proposal_id, "decision": decision, "reviewer": reviewer})
            return p

    def dispatch(self, fail=False):
        """Local-only simulated sink; receipt and outbox commit atomically."""
        processed = []
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            for item in db.execute("SELECT * FROM outbox WHERE state='pending' ORDER BY rowid LIMIT 20").fetchall():
                pid = item["proposal_id"]
                p = json.loads(db.execute("SELECT body FROM proposals WHERE id=?", (pid,)).fetchone()[0])
                order = json.loads(db.execute("SELECT body FROM orders WHERE id=?", (p["order_id"],)).fetchone()[0])
                if p["state"] != "approved" or p["order_version"] != order["version"]:
                    db.execute("UPDATE outbox SET state='stale' WHERE proposal_id=?", (pid,))
                    p.update(state="stale", version=p["version"] + 1)
                    db.execute("UPDATE proposals SET body=? WHERE id=?", (canonical(p), pid))
                    self._event(db, {"type": "dispatch_stale", "proposal_id": pid})
                    continue
                if fail:
                    attempts = item["attempts"] + 1
                    state = "dead_letter" if attempts >= 3 else "pending"
                    db.execute("UPDATE outbox SET attempts=?,state=? WHERE proposal_id=?", (attempts, state, pid))
                    self._event(db, {"type": "dispatch_failed", "proposal_id": pid, "attempts": attempts})
                    continue
                receipt = {"proposal_id": pid, "destination": "local_simulated_sink", "external_message_sent": False, "message": p["message"]}
                db.execute("INSERT OR IGNORE INTO receipts VALUES (?,?)", (pid, canonical(receipt)))
                db.execute("UPDATE outbox SET state='delivered' WHERE proposal_id=?", (pid,))
                p.update(state="simulated_delivery", version=p["version"] + 1)
                db.execute("UPDATE proposals SET body=? WHERE id=?", (canonical(p), pid))
                self._event(db, {"type": "simulated_delivery", "proposal_id": pid})
                processed.append(receipt)
        return processed

    def requeue(self, proposal_id, reviewer):
        reviewer = bounded_text(reviewer, "reviewer", 80)
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            n = db.execute("UPDATE outbox SET state='pending',attempts=0 WHERE proposal_id=? AND state='dead_letter'", (proposal_id,)).rowcount
            if n != 1:
                raise DomainError("Item não está na fila de falhas")
            self._event(db, {"type": "requeue", "proposal_id": proposal_id, "reviewer": reviewer})

    def update_order(self, order_id, **fields):
        """Test/admin API only. Changing business state invalidates old approvals."""
        if set(fields) - {"status", "delay_minutes", "issue"}:
            raise DomainError("Campo desconhecido")
        with self.connection() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT body FROM orders WHERE id=?", (order_id,)).fetchone()
            if not row:
                raise DomainError("Pedido inexistente")
            order = json.loads(row[0]); order.update(fields); order["version"] += 1
            db.execute("UPDATE orders SET body=? WHERE id=?", (canonical(order), order_id))
            self._event(db, {"type": "order_updated", "order_id": order_id, "version": order["version"]})

    def save_run(self, run):
        with self.connection() as db:
            db.execute("INSERT INTO runs VALUES (?,?)", (run["id"], canonical(run)))

    def dashboard(self):
        with self.connection() as db:
            return {"orders": self.orders(), "proposals": self.proposals(), "runs": [json.loads(r[0]) for r in db.execute("SELECT body FROM runs ORDER BY rowid DESC LIMIT 20")], "outbox": [dict(r) for r in db.execute("SELECT * FROM outbox")], "receipts": [json.loads(r[0]) for r in db.execute("SELECT body FROM receipts")]}

    def audit(self):
        with self.connection() as db:
            rows = [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY seq")]
        previous = "0" * 64
        for row in rows:
            if row["previous"] != previous or hashlib.sha256((previous + row["body"]).encode()).hexdigest() != row["hash"]:
                return {"valid": False, "events": len(rows)}
            previous = row["hash"]
        return {"valid": True, "events": len(rows), "head": previous, "entries": rows}
