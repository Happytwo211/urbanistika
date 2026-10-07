# Urbanistika — личный кабинет

## Запуск
    pip install -r requirements.txt
    python app.py
Откройте http://127.0.0.1:8000 (двойным щелчком по html-файлам открывать нельзя: нужен сервер).
База (data.db) и секретный ключ (.secret_key) создаются сами при первом запуске. Не публикуйте их и не коммитьте.

## Фото
Один раз выполните `python download_assets.py` (нужен интернет): фото скачаются в `public/assets/` и больше не зависят от внешних сайтов.

## Структура
- app.py — сервер и API (/api/register, /api/login, /api/me, /api/logout, /api/progress)
- landing/landing.html — лендинг (главная страница). Заявки из формы попадают в таблицу applications в data.db
- public/ — страницы и скрипты; modules.js — модули и уроки

## Перед выкладкой в интернет
1. HTTPS обязателен. Запускайте с переменной URB_SECURE=1 (Secure-cookie и HSTS).
2. Секрет задавайте переменной URB_SECRET, а не файлом.
3. Запускайте через gunicorn/waitress за nginx или Caddy, а не через app.run.
4. За прокси добавьте werkzeug ProxyFix, иначе ограничение попыток будет считать все запросы с одного адреса.
5. Делайте резервные копии data.db.
Пока нет: подтверждения email, восстановления и смены пароля.
