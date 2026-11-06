"""Single-user workout sync API backed by persistent Supabase PostgreSQL.
The HTTP contract is unchanged from the SQLite version (watch app/PWA compatible).
"""
import hmac
import json
import os
import re
from contextlib import contextmanager
from datetime import date as date_type

import psycopg
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

TOKEN = os.environ.get('WORKOUT_TOKEN', '')
DB_URL = os.environ.get('DATABASE_URL', '')
ORIGINS = [x.strip().rstrip('/') for x in os.environ.get('WORKOUT_ORIGINS', '').split(',') if x.strip()]
if len(TOKEN) < 24:
    raise RuntimeError('Set WORKOUT_TOKEN to a random secret of at least 24 characters')
if not DB_URL.startswith(('postgresql://', 'postgres://')):
    raise RuntimeError('Set DATABASE_URL to the Supabase Session Pooler PostgreSQL URL')
if not ORIGINS:
    raise RuntimeError('Set WORKOUT_ORIGINS to your full HTTPS GitHub Pages origin')

app = FastAPI(title='Workout Wear Sync', docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=ORIGINS,
                   allow_methods=['GET', 'PUT', 'POST'],
                   allow_headers=['Authorization', 'Content-Type'])
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')

@contextmanager
def db(write=False):
    # Each request opens its own pooled session. Advisory transaction lock ensures
    # watch set updates and browser revisioned writes cannot interleave.
    with psycopg.connect(DB_URL, connect_timeout=15, autocommit=False) as conn:
        with conn.cursor() as cur:
            if write:
                cur.execute('SELECT pg_advisory_xact_lock(%s)', (250927103,))
            yield cur

def init_schema():
    with db(write=True) as cur:
        cur.execute('''CREATE TABLE IF NOT EXISTS workout_kv (
            k TEXT PRIMARY KEY,
            value JSONB NOT NULL,
            rev INTEGER NOT NULL DEFAULT 1
        )''')

@app.on_event('startup')
def startup():
    init_schema()

def auth(authorization):
    if not authorization or not hmac.compare_digest(authorization, 'Bearer ' + TOKEN):
        raise HTTPException(401, 'Unauthorized')

def read(cur, key):
    cur.execute('SELECT value, rev FROM workout_kv WHERE k = %s', (key,))
    row = cur.fetchone()
    return (row[0], row[1]) if row else (None, 0)

def put(cur, key, data, base_rev=None):
    _, old = read(cur, key)
    if base_rev is not None and old != base_rev:
        raise HTTPException(409, detail={'message': 'Conflict: fetch current state first', 'revision': old})
    rev = old + 1
    cur.execute('''INSERT INTO workout_kv (k, value, rev)
                   VALUES (%s, %s::jsonb, %s)
                   ON CONFLICT(k) DO UPDATE
                   SET value=EXCLUDED.value, rev=EXCLUDED.rev''',
                (key, json.dumps(data, ensure_ascii=False), rev))
    return rev

def validate_date(key):
    if not DATE.fullmatch(key):
        raise HTTPException(400, 'Invalid day')
    try:
        date_type.fromisoformat(key)
    except ValueError:
        raise HTTPException(400, 'Invalid day')

class Revisioned(BaseModel):
    data: dict
    revision: int = Field(ge=0)

class WatchSet(BaseModel):
    date: str
    exercise_id: str = Field(min_length=1, max_length=40)
    index: int = Field(ge=0, le=99)
    kg: float = Field(ge=0, le=2000)
    reps: int = Field(ge=0, le=1000)
    tag: str = ''

class SessionPick(BaseModel):
    date: str
    session: str

@app.get('/api/health')
def health():
    # Health endpoint checks DB availability as well as HTTP server.
    with db() as cur:
        cur.execute('SELECT 1')
    return {'status': 'ok'}

@app.get('/api/state')
def state(authorization: str | None = Header(None)):
    auth(authorization)
    with db() as cur:
        cur.execute('SELECT k, value, rev FROM workout_kv')
        rows = cur.fetchall()
    days = {}; revs = {}; routine_data = None
    for key, value, rev in rows:
        if DATE.fullmatch(key):
            days[key] = value; revs[key] = rev
        elif key == 'routine':
            routine_data = value; revs[key] = rev
    return {'days': days, 'routine': routine_data, 'revisions': revs}

@app.put('/api/day/{date}')
def day(date: str, obj: Revisioned, authorization: str | None = Header(None)):
    auth(authorization); validate_date(date)
    if len(json.dumps(obj.data)) > 100000:
        raise HTTPException(413, 'Too large')
    with db(write=True) as cur:
        rev = put(cur, date, obj.data, obj.revision)
    return {'revision': rev}

@app.put('/api/routine')
def routine(obj: Revisioned, authorization: str | None = Header(None)):
    auth(authorization)
    if len(json.dumps(obj.data)) > 100000:
        raise HTTPException(413, 'Too large')
    with db(write=True) as cur:
        rev = put(cur, 'routine', obj.data, obj.revision)
    return {'revision': rev}

@app.post('/api/watch/set')
def watch_set(obj: WatchSet, authorization: str | None = Header(None)):
    auth(authorization); validate_date(obj.date)
    with db(write=True) as cur:
        b, _ = read(cur, obj.date)
        if not b or not b.get('session'):
            raise HTTPException(400, 'Select session on phone or watch first')
        sets = b.setdefault('sets', {})
        lst = sets.setdefault(obj.exercise_id, [])
        if obj.index > len(lst):
            raise HTTPException(400, 'Set index must not skip entries')
        entry = {'kg': obj.kg, 'reps': obj.reps}
        if obj.tag in ('T', 'W', 'D'): entry['tag'] = obj.tag
        if obj.index == len(lst): lst.append(entry)
        else: lst[obj.index] = entry
        rev = put(cur, obj.date, b)
    return {'revision': rev, 'set': entry}

@app.post('/api/watch/session')
def watch_session(obj: SessionPick, authorization: str | None = Header(None)):
    auth(authorization); validate_date(obj.date)
    if obj.session not in ('A', 'B', 'C', 'D', 'E'):
        raise HTTPException(400, 'Invalid session')
    with db(write=True) as cur:
        b, _ = read(cur, obj.date)
        b = b or {'session': None, 'checks': {}, 'sets': {}, 'alts': {}, 'memo': ''}
        if b.get('session') and b['session'] != obj.session and (b.get('sets') or b.get('checks')):
            raise HTTPException(409, 'Existing workout has data; change in phone app')
        b['session'] = obj.session
        rev = put(cur, obj.date, b)
    return {'revision': rev}

@app.post('/api/watch/check')
def watch_check(obj: WatchSet, authorization: str | None = Header(None)):
    auth(authorization); validate_date(obj.date)
    with db(write=True) as cur:
        b, _ = read(cur, obj.date)
        if not b: raise HTTPException(400, 'No session')
        b.setdefault('checks', {})[obj.exercise_id] = True
        rev = put(cur, obj.date, b)
    return {'revision': rev}
