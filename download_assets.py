"""Скачивает фото в папку assets/ рядом со страницами. Запустить один раз: python download_assets.py"""
import os, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
# если рядом есть папка public (проект с сервером), фото кладём в public/assets
OUT = os.path.join(BASE, 'public' if os.path.isdir(os.path.join(BASE, 'public')) else '', 'assets')
PHOTOS = {'park-1.jpg': 32203742, 'park-2.jpg': 18378553, 'park-3.jpg': 31930726, 'park-4.jpg': 26871796}  # id на pexels.com

os.makedirs(OUT, exist_ok=True)
bad = 0
for name, pid in PHOTOS.items():
    url = f'https://images.pexels.com/photos/{pid}/pexels-photo-{pid}.jpeg?auto=compress&cs=tinysrgb&w=1600'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.pexels.com/', 'Accept': 'image/*'})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            if not r.headers.get('Content-Type', '').startswith('image/') or len(data) < 5000:
                raise ValueError('получен не файл изображения')
        with open(os.path.join(OUT, name), 'wb') as f:
            f.write(data)
        print('OK    ', name, f'{len(data) // 1024} КБ')
    except Exception as e:
        bad += 1
        print('ОШИБКА', name, '-', e)
print('Папка:', OUT)
print('Готово.' if not bad else f'Не скачалось: {bad}. Проверьте интернет и запустите ещё раз.')
