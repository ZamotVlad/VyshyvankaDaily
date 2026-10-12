# tools

- `purge_bootstrap.cjs` - перезбірка урізаного Bootstrap: `npm i purgecss@7 && node purge_bootstrap.cjs`.
- `prepare_image.py` - зображення перед публікацією: `python tools/prepare_image.py photo.png girl-vyshyvanka-vinnytska-oblast`. WebP до 100 КБ, ширина до 1600 px, описова назва латиницею через дефіси (`Gemini_Generated_Image_...` не пройде). Alt описує саме зображення й не дублює `<h1>`.
- `embroidered_map/build.py` - вишита карта України (канва хрестиком, 27 унікальних мотивів у `motifs.py`): `pip install numpy fonttools brotli && python tools/embroidered_map/build.py --lang uk --width 1200 --out karta.png`. Основа для генератора v2 і мапи на `/regions/`.
