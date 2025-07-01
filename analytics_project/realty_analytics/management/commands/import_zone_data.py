# realty_analytics/management/commands/import_zone_data.py

import csv
from django.core.management.base import BaseCommand, CommandError
from realty_analytics.models import ZoneAnalyticsDataPoint, AnalyticsDataPoint
from decimal import Decimal, InvalidOperation
from datetime import datetime
from routines import get_isodate_from_string

class Command(BaseCommand):
    help = 'Массовый импорт данных для ZoneAnalyticsDataPoint из текстового файла ";"'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к файлу для импорта')
        parser.add_argument('--clear', action='store_true', help='Очистить таблицу перед импортом')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        if kwargs['clear']:
            self.stdout.write(self.style.WARNING("Очистка таблицы ZoneAnalyticsDataPoint..."))
            ZoneAnalyticsDataPoint.objects.all().delete()

        self.stdout.write(f"Начинаем импорт из файла: {file_path}")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter=';')

                objects_to_create = []
                # Используем множество для быстрой проверки уникальности внутри файла
                unique_keys_in_file = set()

                for i, row in enumerate(reader, 1):
                    if not row:
                        continue

                    if len(row) != 6:
                        self.stderr.write(
                            self.style.WARNING(f"Строка {i}: Пропускаем, неверное количество колонок: {row}"))
                        continue

                    date_str, city_id_str, zonen_id_str, prop_type, prop_class, price_str = row

                    # --- Валидация и преобразование ---
                    try:
                        date_str = get_isodate_from_string(date_str)  # из обычного в ISO
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                        city_id = int(city_id_str)
                        zonen_id = int(zonen_id_str)
                        price = Decimal(price_str)

                    except (ValueError, InvalidOperation) as e:
                        self.stderr.write(self.style.ERROR(f"Строка {i}: Ошибка преобразования данных: {e}"))
                        continue

                    # Проверка на соответствие choices в модели (защита от неверных данных)
                    if prop_type not in AnalyticsDataPoint.PropertyType.values:
                        self.stderr.write(self.style.ERROR(f"Строка {i}: Неверный тип недвижимости '{prop_type}'"))
                        continue
                    if prop_class not in AnalyticsDataPoint.PropertyClass.values:
                        self.stderr.write(self.style.ERROR(f"Строка {i}: Неверный класс недвижимости '{prop_class}'"))
                        break
                        # continue

                    # --- Логика массового создания ---
                    unique_key = (date_obj, city_id, zonen_id, prop_type, prop_class)
                    if unique_key in unique_keys_in_file:
                        self.stderr.write(self.style.WARNING(f"Строка {i}: Найден дубликат в файле, пропускаем: {row}"))
                        continue

                    unique_keys_in_file.add(unique_key)

                    # Создаем объект, но не сохраняем его в базу сразу
                    datapoint = ZoneAnalyticsDataPoint(
                        date=date_obj,
                        city_id=city_id,
                        zonen_id=zonen_id,
                        property_type=prop_type,
                        property_class=prop_class,
                        avg_price_sqm=price
                    )

                    # Явно вычисляем и присваиваем значения, как это делалось в методе save()
                    datapoint.year = date_obj.year
                    datapoint.month = date_obj.month
                    datapoint.quarter = (date_obj.month - 1) // 3 + 1

                    objects_to_create.append(datapoint)

                # --- Массовая вставка ---
                # ignore_conflicts=True - если запись с таким unique_together уже есть в базе, она будет проигнорирована.
                # Это самый быстрый способ для "добавления новых данных".
                if objects_to_create:
                    ZoneAnalyticsDataPoint.objects.bulk_create(objects_to_create, ignore_conflicts=True)
                    self.stdout.write(self.style.SUCCESS(
                        f"Успешно обработано и добавлено (или проигнорировано) {len(objects_to_create)} записей."))
                else:
                    self.stdout.write(self.style.WARNING("Не найдено новых уникальных записей для импорта."))

        except FileNotFoundError:
            raise CommandError(f"Файл не найден по пути: {file_path}")