from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save  # Импортируем сигналы
from django.dispatch import receiver
from django.utils import timezone  # Для работы с датами
from django.utils.text import slugify
from django.urls import reverse
from routines import translit_to_eng

class District(models.Model):
    # --- Старые поля ---
    name = models.CharField(max_length=200, verbose_name="Официальное/полное название")
    geometry = models.JSONField(verbose_name="Геометрия (GeoJSON)")

    # --- НОВЫЕ ПОЛЯ ---
    smart_name = models.CharField(max_length=255, blank=True, verbose_name="Короткое/умное название",
                                  help_text="Например, 'ЦАО, Арбат'")

    region_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="ID Региона")
    city_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="ID Города")
    ao_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="ID АО (адм. округа)")
    raion_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="ID Района")
    zonen_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="ID Зоны (территории)")
    slug = models.SlugField(max_length=255, unique=True,
                            help_text="Уникальный URL-идентификатор. Заполняется латиницей, например, 'tsao-khamovniki'")

    class Meta:
        verbose_name = "Территория (район)"
        verbose_name_plural = "Территории (районы)"
        ordering = ['name']

    def __str__(self):
        # Используем smart_name для отображения, если оно есть, иначе старое имя
        return self.smart_name or self.name

    def get_absolute_url(self):
        """Возвращает канонический URL с учетом города."""
        if self.city_id == 77:
            city_code = 'msk'
        elif self.city_id == 78:
            city_code = 'spb'
        else:
            return None # На случай, если город не определен

        return reverse(f'{city_code}:district', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:  # Создаем слаг только если он еще не задан
            new_slug = translit_to_eng(self.name + '-' + str(self.zonen_id))
            self.slug = slugify(new_slug, allow_unicode=True)
            super().save(*args, **kwargs)
        super().save(*args, **kwargs)


# НОВАЯ МОДЕЛЬ ДЛЯ ИСТОРИИ ЦЕН
class PriceHistory(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="price_history", verbose_name="Район")
    date = models.DateField(verbose_name="Дата")
    avg_price_sqm = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Средняя цена за м²")

    class Meta:
        verbose_name = "История цены"
        verbose_name_plural = "История цен"
        ordering = ['date'] # Сортируем записи по дате

    def __str__(self):
        return f"{self.district.name} - {self.date}: {self.avg_price_sqm}"

class Article(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('published', 'Опубликовано'),
    )

    title = models.CharField(max_length=250, verbose_name="Заголовок")
    content = models.TextField(verbose_name="Содержимое")
    pub_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="articles", verbose_name="Автор")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', verbose_name="Статус")

    # image = models.ImageField(upload_to='articles/', blank=True, null=True, verbose_name="Изображение") # Можно добавить позже

    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name="URL (слаг)")

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ['-pub_date']


    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Возвращает канонический URL для объекта."""

        return reverse('article', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Автоматически создает слаг из заголовка перед сохранением."""

        # ename = translit_to_eng(self.name)


        if not self.slug:  # Создаем слаг только если он еще не задан
            new_slug = translit_to_eng(self.name + '-' + str(self.id))
            self.slug = slugify(new_slug, allow_unicode=True)
            super().save(*args, **kwargs)
        super().save(*args, **kwargs)

    # НОВАЯ МОДЕЛЬ ПРОФИЛЯ ПОЛЬЗОВАТЕЛЯ
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription_expires_on = models.DateField(null=True, blank=True, verbose_name="Подписка активна до")

    @property
    def is_pro(self):
        """Проверяет, активна ли подписка."""
        if self.subscription_expires_on:
            return timezone.now().date() <= self.subscription_expires_on
        return False

    def __str__(self):
        return f'Профиль пользователя {self.user.username}'


class CityAnalytics(models.Model):
    # Уникальный ID города, который мы будем использовать для связи
    city_id = models.IntegerField(unique=True, verbose_name="ID Города")
    city_name = models.CharField(max_length=100, verbose_name="Название города")

    avg_price_sqm = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Средняя цена за м²")
    price_change_percent = models.CharField(max_length=10, verbose_name="Изменение цены (строка)",
                                            help_text="Например, '+1.2%' или '-0.5%'")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Последнее обновление")

    class Meta:
        verbose_name = "Аналитика по городу (витрина)"
        verbose_name_plural = "Аналитика по городам (витрина)"
        ordering = ['city_id']

    def __str__(self):
        return self.city_name




# НОВАЯ МОДЕЛЬ ДЛЯ АНАЛИТИЧЕСКИХ ДАННЫХ
class AnalyticsDataPoint(models.Model):
    # --- Перечисляемые типы для удобства и надежности ---
    class PropertyType(models.TextChoices):
        NEW_BUILDING = 'new', 'Новостройка'
        SECONDARY = 'secondary', 'Вторичное жилье'
        # COMMERCIAL = 'commercial', 'Коммерческая'

    class PropertyClass(models.TextChoices):
        ECONOMY = 'economy', 'Эконом'
        COMFORT = 'comfort', 'Комфорт'
        BUSINESS = 'business', 'Бизнес'
        PREMIUM = 'premium', 'Премиум'
        VALL = 'vall', 'Вся вторичная'
        PALL = 'pall', 'Вся строящаяся'
        MVN_MASS = 'mass', 'Новая массовая'
        MVN_KACH = 'quality', 'Новая качественная'
        MVN_PREMIUM = 'elite', 'Новая премиум'
        V_SF = 'oldfund', 'Старый Фонд'
        V_STAL = 'stal', 'Сталинки'
        V_SOV = 'sovet', 'Советское массовое'


    # --- Основные поля, которые мы заполняем ---
    date = models.DateField(verbose_name="Дата")
    city_id = models.IntegerField(verbose_name="ID Города")

    property_type = models.CharField(max_length=30, choices=PropertyType.choices, verbose_name="Тип недвижимости")
    property_class = models.CharField(max_length=30, choices=PropertyClass.choices, verbose_name="Класс недвижимости")
    avg_price_sqm = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Средняя цена за м²")

    # --- Автоматически вычисляемые поля ---
    year = models.IntegerField(editable=False, verbose_name="Год")
    quarter = models.IntegerField(editable=False, verbose_name="Квартал")
    month = models.IntegerField(editable=False, verbose_name="Месяц")

    class Meta:
        verbose_name = "Точка аналитических данных"
        verbose_name_plural = "Точки аналитических данных"
        # Обновляем unique_together, чтобы использовать новое поле
        unique_together = ('date', 'city_id', 'property_type', 'property_class')
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - Город ID {self.city_id} - {self.get_property_type_display()}"

    # --- Главная магия: переопределение метода save() ---
    def save(self, *args, **kwargs):
        # Перед сохранением в базу, вычисляем нужные поля
        self.year = self.date.year
        self.month = self.date.month
        # Квартал вычисляется по простому математическому правилу
        self.quarter = (self.date.month - 1) // 3 + 1

        # Вызываем "родительский" метод save, который и сохранит все в базу
        super().save(*args, **kwargs)


# ... импорты и другие модели ...

# НОВАЯ МОДЕЛЬ ДЛЯ ДАННЫХ ПО ЗОНАМ/ТЕРРИТОРИЯМ
class ZoneAnalyticsDataPoint(models.Model):
    # Используем те же choices, что и в AnalyticsDataPoint
    PropertyType = AnalyticsDataPoint.PropertyType
    PropertyClass = AnalyticsDataPoint.PropertyClass

    # --- Основные поля ---
    date = models.DateField(verbose_name="Дата точки данных")
    zonen_id = models.IntegerField(db_index=True, verbose_name="ID Зоны/Территории")
    city_id = models.IntegerField(db_index=True, verbose_name="ID Города")

    property_type = models.CharField(max_length=20, choices=PropertyType.choices, verbose_name="Тип недвижимости")
    property_class = models.CharField(max_length=20, choices=PropertyClass.choices, verbose_name="Класс недвижимости")
    avg_price_sqm = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Средняя цена за м²")

    # --- Автоматически вычисляемые поля ---
    year = models.IntegerField(editable=False, verbose_name="Год")
    quarter = models.IntegerField(editable=False, verbose_name="Квартал")
    month = models.IntegerField(editable=False, verbose_name="Месяц")

    class Meta:
        verbose_name = "Точка данных по зоне"
        verbose_name_plural = "Точки данных по зонам"
        # Обновляем unique_together, чтобы включить city_id для гарантии уникальности
        unique_together = ('date', 'city_id', 'zonen_id', 'property_type', 'property_class')
        ordering = ['-date']

    def __str__(self):
        # Обновляем строковое представление
        return f"{self.date} - Город ID {self.city_id} / Зона ID {self.zonen_id}"

    # Метод save() для автоматического вычисления дат
    def save(self, *args, **kwargs):
        self.year = self.date.year
        self.month = self.date.month
        self.quarter = (self.date.month - 1) // 3 + 1
        super().save(*args, **kwargs)

# АВТОМАТИЧЕСКОЕ СОЗДАНИЕ ПРОФИЛЯ
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()