"""Сервер Urbanistika: регистрация, вход, прогресс. Flask + SQLite. Запуск: python old_app.py"""
import hmac, os, re, secrets, sqlite3, time
from collections import defaultdict, deque
from flask import Flask, abort, g, jsonify, redirect, request, send_file, session
from werkzeug.security import check_password_hash, generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
PUB = os.path.join(BASE, 'public')
DB = os.environ.get('URB_DB', os.path.join(BASE, 'data.db'))
SECURE = os.environ.get('URB_SECURE') == '1'  # включить, когда сайт работает по HTTPS


def secret():
    if os.environ.get('URB_SECRET'):
        return os.environ['URB_SECRET']
    p = os.path.join(BASE, '.secret_key')
    if not os.path.exists(p):
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as f:
            f.write(secrets.token_hex(32))
    return open(p).read().strip()


app = Flask(__name__, static_folder=None)
app.config.update(SECRET_KEY=secret(), MAX_CONTENT_LENGTH=8 * 1024, SESSION_COOKIE_NAME='urb_session',
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', SESSION_COOKIE_SECURE=SECURE,
                  PERMANENT_SESSION_LIFETIME=7 * 24 * 3600)


# ---------- база данных (только параметризованные запросы) ----------
def db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop('db', None)
    if d:
        d.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE,
      name TEXT NOT NULL, city TEXT NOT NULL, pw TEXT NOT NULL, created INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS progress(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      lesson TEXT NOT NULL, done_at INTEGER NOT NULL, PRIMARY KEY(user_id, lesson));''')
    c.close()


# ---------- вспомогательное ----------
hits = defaultdict(deque)  # ограничение попыток в памяти (сбрасывается при перезапуске)


def blocked(key, limit, window):
    q, now = hits[key], time.time()
    while q and q[0] < now - window:
        q.popleft()
    return len(q) >= limit


def hit(key):
    hits[key].append(time.time())


def err(msg, code=400, fields=None):
    r = jsonify(error=msg, fields=fields or {})
    r.status_code = code
    return r


EMAIL = re.compile(r'^[^@\s]{1,64}@[^@\s]{1,189}\.[^@\s]{2,}$')
LESSON = re.compile(r'^m\d{1,2}-\d{1,3}$')
CTRL = re.compile(r'[\x00-\x1f\x7f]')


def clean(v, lo, hi):
    if not isinstance(v, str) or CTRL.search(v):
        return None
    v = v.strip()
    return v if lo <= len(v) <= hi else None


DUMMY = generate_password_hash('dummy-password-for-timing')


def start_session(uid):
    session.clear()  # новая сессия при входе — защита от фиксации сессии
    session.permanent = True
    session['uid'], session['csrf'] = uid, secrets.token_urlsafe(32)


def current():
    uid = session.get('uid')
    return db().execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone() if uid else None


def pub(u):
    return {'name': u['name'], 'email': u['email'], 'city': u['city']}


def csrf_ok():
    s = session.get('csrf', '')
    return bool(s) and hmac.compare_digest(request.headers.get('X-CSRF-Token', ''), s)


def ip():
    return request.remote_addr or '?'


# ---------- защита запросов и заголовки ----------
@app.before_request
def guard():
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        o = request.headers.get('Origin')
        if o and o != request.host_url.rstrip('/'):
            return err('Запрос отклонён', 403)
        if request.path.startswith('/api/') and not request.is_json:
            return err('Неверный формат запроса', 415)


CSP = ("default-src 'none'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; "
       "font-src https://fonts.gstatic.com; img-src 'self' https://images.pexels.com data:; connect-src 'self'; "
       "base-uri 'none'; form-action 'self'; frame-ancestors 'none'")


@app.after_request
def headers(r):
    r.headers.update({'Content-Security-Policy': CSP, 'X-Content-Type-Options': 'nosniff', 'X-Frame-Options': 'DENY',
                      'Referrer-Policy': 'no-referrer', 'Cross-Origin-Opener-Policy': 'same-origin',
                      'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'})
    if request.path.startswith('/api/'):
        r.headers['Cache-Control'] = 'no-store'
    if SECURE:
        r.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return r


MSG = {404: 'Не найдено', 405: 'Метод не поддерживается', 413: 'Слишком большой запрос', 500: 'Ошибка сервера'}
for _c in MSG:
    app.register_error_handler(_c, lambda e, c=_c: err(MSG[c], c))


# ---------- API ----------
@app.post('/api/register')
def register():
    if blocked('reg:' + ip(), 10, 3600):
        return err('Слишком много попыток. Попробуйте позже.', 429)
    hit('reg:' + ip())
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        return err('Неверные данные')
    name, email, city, pw = clean(d.get('name'), 2, 60), clean(d.get('email'), 5, 254), clean(d.get('city'), 2,
                                                                                              100), d.get('password')
    f = {}
    if not name: f['name'] = 'Введите имя (2–60 символов)'
    if not email or not EMAIL.match(email): f['email'] = 'Введите корректный email'
    if not city: f['city'] = 'Укажите город и район'
    if not isinstance(pw, str) or not 8 <= len(pw) <= 128 or not re.search(r'[^\W\d_]', pw) or not re.search(r'\d', pw):
        f['password'] = 'Минимум 8 символов, буква и цифра'
    if f:
        return err('Проверьте поля', 400, f)
    try:
        cur = db().execute('INSERT INTO users(email,name,city,pw,created) VALUES(?,?,?,?,?)',
                           (email.lower(), name, city, generate_password_hash(pw), int(time.time())))
        db().commit()
    except sqlite3.IntegrityError:
        return err('Проверьте поля', 400, {'email': 'Этот email уже зарегистрирован'})
    start_session(cur.lastrowid)
    return jsonify(user={'name': name, 'email': email.lower(), 'city': city}, csrf=session['csrf']), 201


@app.post('/api/login')
def login():
    d = request.get_json(silent=True)
    d = d if isinstance(d, dict) else {}
    email, pw = clean(d.get('email'), 1, 254), d.get('password')
    bad = err('Неверный email или пароль', 401)
    if not email or not isinstance(pw, str) or len(pw) > 128:
        return bad
    k1, k2 = 'login:%s:%s' % (ip(), email.lower()), 'loginip:' + ip()
    if blocked(k1, 5, 900) or blocked(k2, 30, 900):
        return err('Слишком много попыток. Попробуйте через 15 минут.', 429)
    u = db().execute('SELECT * FROM users WHERE email=?', (email,)).fetchone()
    ok = check_password_hash(u['pw'] if u else DUMMY, pw)  # время ответа не выдаёт, есть ли такой email
    if not (u and ok):
        hit(k1);
        hit(k2)
        return bad
    start_session(u['id'])
    return jsonify(user=pub(u), csrf=session['csrf'])


@app.get('/api/me')
def me():
    u = current()
    return jsonify(user=pub(u), csrf=session['csrf']) if u else err('Требуется вход', 401)


@app.post('/api/logout')
def logout():
    if not csrf_ok():
        return err('Запрос отклонён', 403)
    session.clear()
    return jsonify(ok=True)


@app.get('/api/progress')
def get_progress():
    u = current()
    if not u:
        return err('Требуется вход', 401)
    rows = db().execute('SELECT lesson FROM progress WHERE user_id=?', (u['id'],)).fetchall()
    return jsonify(done=[r['lesson'] for r in rows])


@app.post('/api/progress')
def set_progress():
    u = current()
    if not u:
        return err('Требуется вход', 401)
    if not csrf_ok():
        return err('Запрос отклонён', 403)
    d = request.get_json(silent=True)
    lesson = d.get('lesson') if isinstance(d, dict) else None
    if not isinstance(lesson, str) or not LESSON.match(lesson):
        return err('Неверный урок')
    db().execute('INSERT OR IGNORE INTO progress(user_id,lesson,done_at) VALUES(?,?,?)',
                 (u['id'], lesson, int(time.time())))
    db().commit()
    return jsonify(ok=True)


# ---------- страницы ----------
@app.get('/')
def index():
    return redirect('/register.html')


MIME = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml',
        '.png': 'image/png', '.jpg': 'image/jpeg', '.ico': 'image/x-icon'}  # свои типы: в Windows они бывают неверными
ROOT = os.path.realpath(PUB)


@app.get('/<path:p>')
def files(p):
    full = os.path.realpath(os.path.join(ROOT, p))
    if (p.startswith('api/') or any(x.startswith('.') for x in p.split('/'))
            or not full.startswith(ROOT + os.sep) or not os.path.isfile(full)):  # выход за public невозможен
        abort(404)
    return send_file(full, mimetype=MIME.get(os.path.splitext(full)[1].lower()))


init_db()
if __name__ == '__main__':
    print('Папка страниц:', ROOT, '| register.html найден:', os.path.isfile(os.path.join(ROOT, 'register.html')))
    app.run('127.0.0.1', 8000, debug=False)
