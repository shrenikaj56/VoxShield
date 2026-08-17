import sqlite3
from pathlib import Path
from utils.config import DB_PATH


def ensure_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id TEXT UNIQUE,
            timestamp TEXT,
            amount REAL,
            beneficiary TEXT,
            transaction_features TEXT,
            transaction_risk INTEGER,
            voice_risk INTEGER,
            behavior_risk INTEGER,
            context_risk INTEGER,
            final_risk INTEGER,
            risk_level TEXT,
            decision TEXT,
            detected_reasons TEXT,
            voice_transcript TEXT,
            behavior_signals TEXT,
            context_signals TEXT,
            evidence_path TEXT
        )
    ''')

    columns = [row[1] for row in conn.execute('PRAGMA table_info(incidents)').fetchall()]
    if 'context_risk' not in columns:
        conn.execute('ALTER TABLE incidents ADD COLUMN context_risk INTEGER')
    if 'context_signals' not in columns:
        conn.execute('ALTER TABLE incidents ADD COLUMN context_signals TEXT')

    conn.commit()
    conn.close()
    return DB_PATH


def store_incident(record):
    ensure_database()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        '''
        INSERT INTO incidents (
            incident_id, timestamp, amount, beneficiary, transaction_features,
            transaction_risk, voice_risk, behavior_risk, context_risk, final_risk,
            risk_level, decision, detected_reasons, voice_transcript,
            behavior_signals, context_signals, evidence_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            record.get('incident_id'), record.get('timestamp'), record.get('amount'),
            record.get('beneficiary'), record.get('transaction_features'),
            record.get('transaction_risk'), record.get('voice_risk'),
            record.get('behavior_risk'), record.get('context_risk'),
            record.get('final_risk'), record.get('risk_level'), record.get('decision'),
            record.get('detected_reasons'), record.get('voice_transcript'),
            record.get('behavior_signals'), record.get('context_signals'),
            record.get('evidence_path')
        )
    )
    conn.commit()
    conn.close()
    return True


def fetch_recent_incidents(limit=20):
    ensure_database()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    if limit is None:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY id DESC"
    ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM incidents ORDER BY id DESC LIMIT ?",
            (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
