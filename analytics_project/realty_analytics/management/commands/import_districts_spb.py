import json
from django.core.management.base import BaseCommand
from realty_analytics.models import District
from routines import create_acronym, translit_to_eng, make_smart_raion
from django.utils.text import slugify

class Command(BaseCommand):
    help = 'Импортирует территории районов из файла GeoJSON'

    def add_arguments(self, parser):
        parser.add_argument('geojson_file', type=str, help='Путь к файлу GeoJSON')

    def handle(self, *args, **kwargs):
        file_path = kwargs['geojson_file']
        self.stdout.write(f"Начинаем импорт из файла: {file_path}")

        # Очищаем старые данные, чтобы избежать дубликатов
        # District.objects.all().delete()
        # self.stdout.write("Старые данные о районах удалены.")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        districts_to_create = []
        for feature in data['features']:
            properties = feature['properties']
            geometry = feature['geometry']




            # --- ВАЖНО: СОПОСТАВЛЕНИЕ ПОЛЕЙ ---
            # Здесь вы должны указать, какое поле из GeoJSON
            # соответствует какому полю в вашей модели Django.
            # Названия полей в `properties` зависят от вашего исходного .tab файла.
            # Откройте GeoJSON в текстовом редакторе, чтобы посмотреть их.

            # если spb

            district_data = {
                'name': properties.get('name', ''),  # Пример: поле NAME в GeoJSON -> name в модели
                'smart_name': properties.get('name', ''),
                'region_id': -2,
                'zonen_id': properties.get('id'),

                'city_id': 78,
                'ao_id': properties.get('AO_ID'),
                'raion_id': properties.get('RAION_ID'),

                'slug': slugify(translit_to_eng(properties.get('name', '') + '-' + str(properties.get('id'))), allow_unicode=True),
                'geometry': geometry  # Геометрию берем целиком
            }
            # если msk



            # district_data = {
            #     'name': properties.get('NAME', ''),  # Пример: поле NAME в GeoJSON -> name в модели
            #     'smart_name': make_smart_raion(properties.get('NAME', '')), # Пример: поле NAME в GeoJSON -> name в модели  create_acronym(properties.get('ADMIN_L5')),
            #     'region_id': -1,
            #     'city_id': 77,
            #     'ao_id': -1,
            #     'zonen_id': properties.get('OSM_ID'),
            #
            #     'raion_id': properties.get('RAION_ID'),
            #
            #     'slug' : slugify(translit_to_eng(properties.get('NAME', '') + '-' + str(properties.get('OSM_ID'))), allow_unicode=True),
            #
            #     'geometry': geometry  # Геометрию берем целиком
            # }
            districts_to_create.append(District(**district_data))

        # Создаем все объекты одним запросом к базе данных - это очень быстро
        District.objects.bulk_create(districts_to_create)

        self.stdout.write(self.style.SUCCESS(f"Успешно импортировано {len(districts_to_create)} районов."))