from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from .models import District, PriceHistory, Article, CityAnalytics, AnalyticsDataPoint, ZoneAnalyticsDataPoint  # Добавьте PriceHistory
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from django.db.models import F, Window, Avg

import json  # Импортируем для работы с JSON
from django.db.models.functions import Lag

from django.http import JsonResponse, HttpResponseBadRequest
from .models import ZoneAnalyticsDataPoint
from django.db.models import Avg, Subquery, OuterRef, F
from collections import defaultdict
import json  # Добавьте, если еще не импортирован


# ...

def get_zone_class_dynamics_api(request):
    """
    API для получения данных для графика динамики цен по классам жилья,
    сгруппированных по КВАРТАЛАМ.
    """
    zonen_id = request.GET.get('zonen_id')
    property_type = request.GET.get('property_type')

    if not zonen_id or not property_type:
        return HttpResponseBadRequest("Параметры 'zonen_id' и 'property_type' обязательны.")

    try:
        # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Группируем по году и кварталу ---
        queryset = ZoneAnalyticsDataPoint.objects.filter(
            zonen_id=int(zonen_id),
            property_type=property_type
        ).values(
            'year', 'quarter'  # Группируем по этим полям
        ).annotate(
            avg_price=Avg('avg_price_sqm')  # Считаем среднюю цену для каждой группы
        ).order_by('year', 'quarter')

        # Теперь queryset выглядит так:
        # [{'year': 2024, 'quarter': 1, 'avg_price': 500}, {'year': 2024, 'quarter': 2, 'avg_price': 510}, ...]
        # Нам нужно перегруппировать это по классам.

        # Поэтому мы делаем второй, более сложный запрос
        # для группировки сразу и по кварталу, и по классу.

        full_queryset = ZoneAnalyticsDataPoint.objects.filter(
            zonen_id=int(zonen_id),
            property_type=property_type
        ).values(
            'year', 'quarter', 'property_class'  # Группируем сразу по трем полям
        ).annotate(
            avg_price=Avg('avg_price_sqm')
        ).order_by('year', 'quarter')

        # --- Группируем данные в Python ---
        # Структура: {'2024-Q1': {'business': 700, 'comfort': 450}, '2024-Q2': {...}}
        data_by_quarter = defaultdict(dict)
        for point in full_queryset:
            label = f"{point['year']}-Q{point['quarter']}"  # Формируем метку вида "2024-Q1"
            data_by_quarter[label][point['property_class']] = point['avg_price']

        # --- Формируем финальный ответ (эта часть остается почти без изменений) ---
        labels = sorted(data_by_quarter.keys())

        present_classes = set()
        for quarter_data in data_by_quarter.values():
            present_classes.update(quarter_data.keys())

        datasets = []
        for prop_class in sorted(list(present_classes)):
            dataset_data = {
                'label': ZoneAnalyticsDataPoint.PropertyClass(prop_class).label,
                'data': [data_by_quarter[label].get(prop_class) for label in labels]
            }
            datasets.append(dataset_data)

        response_data = {
            'labels': labels,
            'datasets': datasets
        }
        return JsonResponse(response_data)

    except (ValueError, TypeError):
        return HttpResponseBadRequest("Некорректный ID зоны.")

def calculate_market_pulse(city_id, property_type='secondary', property_class='vall'):
    """
    Вспомогательная функция для расчета ключевых показателей для одного города.
    """
    try:
        # Находим две последние по дате уникальные записи (группируя по дате)
        latest_points = AnalyticsDataPoint.objects.filter(
            city_id=city_id,
            property_type=property_type,
            property_class=property_class
        ).values('date').annotate(
            avg_price=Avg('avg_price_sqm')
        ).order_by('-date')[:2]

        if len(latest_points) >= 2:
            # У нас есть как минимум две точки для сравнения
            latest_price = latest_points[0]['avg_price']
            previous_price = latest_points[1]['avg_price']

            if previous_price > 0:
                change_percent = ((latest_price - previous_price) / previous_price) * 100
                change_str = f"{change_percent:+.1f}%"  # Форматируем строку: +1.2% или -0.5%
            else:
                change_str = "N/A"  # Не можем посчитать изменение от нуля

            return {
                'avg_price': latest_price,
                'change': change_str,
            }
        elif len(latest_points) == 1:
            # Есть только одна точка, не с чем сравнивать
            return {
                'avg_price': latest_points[0]['avg_price'],
                'change': "Новые данные",
            }

    except Exception:
        # Ловим любые возможные ошибки, чтобы сайт не падал
        pass

    # Возвращаем заглушку, если данных нет или произошла ошибка
    return {
        'avg_price': 0,
        'change': "Нет данных",
    }


def get_analytics_chart_data(request):
    """
    Универсальная view для получения данных для графиков.
    Принимает GET-параметры: city_id, property_type, property_class (опционально).
    """
    # Получаем параметры из GET-запроса
    city_id = request.GET.get('city_id')
    zonen_id = request.GET.get('zonen_id')
    property_type = request.GET.get('property_type')
    property_class = request.GET.get('property_class')

            # --- Выбираем, с какой моделью работать ---
    if zonen_id:
        # Если есть zonen_id, работаем с данными по зонам
        try:
            base_queryset = ZoneAnalyticsDataPoint.objects.filter(zonen_id=int(zonen_id))
            # Опционально можно добавить фильтр и по city_id для надежности
            if city_id:
                base_queryset = base_queryset.filter(city_id=int(city_id))
            queryset = base_queryset
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Некорректный ID зоны или города.")

    elif city_id:
        # Если есть ТОЛЬКО city_id, работаем с данными по городам
        try:
            queryset = AnalyticsDataPoint.objects.filter(city_id=int(city_id))
        except (ValueError, TypeError):
            return HttpResponseBadRequest("Некорректный ID города.")
    else:
        # Если не указан ни один из ID, запрос невалидный
        return HttpResponseBadRequest("Необходимо указать city_id или zonen_id.")

        # --- Применяем общие фильтры ---
    if property_type:
        queryset = queryset.filter(property_type=property_type)

    if property_class and property_class != 'all':
        queryset = queryset.filter(property_class=property_class)

        # --- Группировка, агрегация и формирование ответа (общая логика) ---
    chart_data = queryset.values('year', 'month').annotate(
        avg_price=Avg('avg_price_sqm')
    ).order_by('year', 'month')

    labels = [f"{item['month']:02}.{item['year']}" for item in chart_data]
    data_points = [item['avg_price'] for item in chart_data]

    response_data = {
        'labels': labels,
        'data': data_points,
    }

    return JsonResponse(response_data)




def get_price_history_api(request, district_id):
    # Получаем историю цен для конкретного района, отсортированную по дате
    price_history = PriceHistory.objects.filter(district_id=district_id).order_by('date')

    # Формируем данные в формате, удобном для Chart.js
    labels = [item.date.strftime("%d.%m.%Y") for item in price_history] # Даты для оси X
    data_points = [item.avg_price_sqm for item in price_history]      # Цены для оси Y

    response_data = {
        'labels': labels,
        'data': data_points,
    }

    return JsonResponse(response_data)

def get_districts_geojson(request):

    city_id = request.GET.get('city_id')  # Получаем city_id из GET-параметра

    if not city_id:
        return JsonResponse({"error": "city_id is required"}, status=400)
    # Для каждого района (OuterRef('zonen_id')) мы находим последнюю по дате
    # запись в ZoneAnalyticsDataPoint и берем ее цену.
    latest_price_subquery = ZoneAnalyticsDataPoint.objects.filter(
        zonen_id=OuterRef('zonen_id'),
        property_type='secondary'  # или любой другой тип по умолчанию
    ).order_by('-date').values('avg_price_sqm')[:1]

    # Получаем все районы для города и присоединяем к ним вычисленную цену
    districts = District.objects.filter(
        city_id=city_id,
        zonen_id__isnull=False  # Берем только те, у кого есть zonen_id
    ).annotate(
        latest_price=Subquery(latest_price_subquery)
    )

    # Получаем все районы из базы данных старый вариант
    # districts = District.objects.all()
    # if city_id:
    #     districts = districts.filter(city_id=city_id)
    # Собираем структуру GeoJSON
    feature_collection = {
        "type": "FeatureCollection",
        "features": []
    }

    for district in districts:
        feature = {
            "type": "Feature",
            "properties": {
                "name": district.name,
                "smart_name": district.name, # district.smart_name or
                "price": district.latest_price,
                "detail_url": district.get_absolute_url() if district.slug else None,
            },
            "geometry": district.geometry # Берем JSON-геометрию прямо из модели
        }
        feature_collection["features"].append(feature)

    return JsonResponse(feature_collection)


# def Showtemp(request, city_code):
#     return HttpResponse("Интерактивная карта СПб" + city_code)

def ShowMap(request, city_code):

    if city_code == 'msk':
        city_id = 77
        city_name = "Москвы"
        map_center = [55.751244, 37.618423]
  # Центр Москвы
        map_zoom = 10
    elif city_code == 'spb':
        city_id = 78
        city_name = "Санкт-Петербурга"
        map_center =  [59.934280, 30.335099] # Центр Санкт-Петербурга
        map_zoom = 10
    else:
        from django.http import Http404
        raise Http404("Город не найден")

    map_config = {
        'center': map_center,
        'zoom': map_zoom,
    }

    context = {
        'city_id': city_id,
        'city_name': city_name,
        'city_code': city_code,  # Передаем для использования в шаблоне
        # Передаем словарь, сконвертированный в JSON-строку
        'map_config_json': json.dumps(map_config),

    }
    context.update(get_districts())
    return render(request, 'realty_analytics/map-analytics.html', context)


def ShowTariffs(request):
    return render(request, 'realty_analytics/tariffs.html')

def ShowJournal(request):

    # Показываем только опубликованные статьи, отсортированные по дате
    articles = Article.objects.filter(status='published').order_by('-pub_date')
    context = {
        'articles': articles
    }
    return render(request, 'realty_analytics/journal.html', context)


def ShowArticle(request, slug):

        # Показываем одну статью, но тоже только если она опубликована
    article = get_object_or_404(Article, slug=slug, status='published')
    context = {
        'article': article
    }
    return render(request, 'realty_analytics/article.html', context)


def ShowAbout(request):
    context = (get_districts())
    return render(request, 'realty_analytics/about.html', context)

def ShowDistrict(request, slug, city_code): #в оригинале - district_detail_view
    city_id = 77 if city_code == 'msk' else 78

    # Ищем район по слагу И по city_id для надежности
    district = get_object_or_404(District, slug=slug, city_id=city_id)

    # is_accessible = request.user.is_authenticated and hasattr(request.user,
    #                                                           'profile') and request.user.profile.is_pro
    is_accessible = True #Пускаем всех

    key_metrics = {}
    if district.zonen_id:
        latest_points = ZoneAnalyticsDataPoint.objects.filter(
            zonen_id=district.zonen_id,
            property_type=ZoneAnalyticsDataPoint.PropertyType.SECONDARY,
            property_class='vall'
        ).values('date', 'avg_price_sqm').order_by('-date')[:2]



        if len(latest_points) >= 2:
            latest_price_data = latest_points[0]
            previous_price_data = latest_points[1]

            key_metrics['avg_price'] = latest_price_data['avg_price_sqm']

            # --- НОВОЕ: Получаем и форматируем название месяца ---
            # Месяцы на русском языке
            months = ["январе", "феврале", "марте", "апреле", "мае", "июне",
                      "июле", "августе", "сентябре", "октябре", "ноябре", "декабре"]
            key_metrics['month_name'] = months[latest_price_data['date'].month - 1]

            if previous_price_data['avg_price_sqm'] > 0:
                change = ((latest_price_data['avg_price_sqm'] - previous_price_data['avg_price_sqm']) /
                          previous_price_data['avg_price_sqm']) * 100
                key_metrics['change'] = f"{change:+.1f}%"
            else:
                key_metrics['change'] = "N/A"
        elif len(latest_points) == 1:
            latest_price_data = latest_points[0]
            key_metrics['avg_price'] = latest_price_data['avg_price_sqm']
            months = ["январе", "феврале", ...]  # (дублируем для полноты)
            key_metrics['month_name'] = months[latest_price_data['date'].month - 1]
            key_metrics['change'] = "Новые данные"

    context = {
        'district': district,
        'city_code': city_code,
        'is_accessible': is_accessible,
        'key_metrics': key_metrics,
        'district_geometry_json': json.dumps(district.geometry)
    }
    context.update(get_districts())


    return render(request, 'realty_analytics/district.html', context)


def get_districts():
    try:
        moscow_pulse = calculate_market_pulse(city_id=77, property_type='secondary')
        moscow_districts = District.objects.filter(city_id=77)[:5]
        # moscow_districts = District.objects.filter(city_id=77).exclude(raion_id__isnull=True)[:5]
        # Заглушка популярных районов
    except CityAnalytics.DoesNotExist:
        moscow_data = None
        moscow_districts = []

        # 3. Получаем готовые данные для Санкт-Петербурга
    try:
        spb_pulse = calculate_market_pulse(city_id=78, property_type='secondary')
        spb_districts = District.objects.filter(city_id=78)[:5]

    except CityAnalytics.DoesNotExist:
        spb_data = None
        spb_districts = []


    context = {
        'moscow_pulse': moscow_pulse,
        'moscow_districts': moscow_districts,
        'spb_pulse': spb_pulse,
        'spb_districts': spb_districts,
    }

    return context

def AnHome(request):

    """
    Отрисовывает главную страницу с динамическими данными.
    """

    # 1. Получаем последние 3 опубликованные статьи
    latest_articles = Article.objects.filter(status='published').order_by('-pub_date')[:3]
    context = {
         'latest_articles': latest_articles,
    }
    context.update(get_districts())


    # 2. Получаем готовые данные для Москвы
    # try:
    #     moscow_pulse = calculate_market_pulse(city_id=77, property_type='secondary')
    #     moscow_districts = District.objects.filter(city_id=77)[:5]
    #     # moscow_districts = District.objects.filter(city_id=77).exclude(raion_id__isnull=True)[:5]
    # # Заглушка популярных районов
    # except CityAnalytics.DoesNotExist:
    #     moscow_data = None
    #     moscow_districts = []
    #
    # # 3. Получаем готовые данные для Санкт-Петербурга
    # try:
    #     spb_pulse = calculate_market_pulse(city_id=78, property_type='secondary')
    #     spb_districts = District.objects.filter(city_id=78)[:5]
    #
    # except CityAnalytics.DoesNotExist:
    #         spb_data = None
    #         spb_districts = []

    # context = {
    #     'latest_articles': latest_articles,
    #     'moscow_pulse': moscow_pulse,
    #     'moscow_districts': moscow_districts,
    #     'spb_pulse': spb_pulse,
    #     'spb_districts': spb_districts,
    # }

    return render(request, 'realty_analytics/index.html', context)

    # try:
    #     spb_latest_price = PriceHistory.objects.filter(district_id=2).latest('date').avg_price_sqm
    # except PriceHistory.DoesNotExist:
    #     spb_latest_price = 7000

    # market_pulse = {
    #     'moscow_data': {
    #         'avg_price': moscow_latest_price,
    #         'change': "+1.2%",  # Заглушка, в реальности нужно считать
    #         'popular_districts': popular_districts,
    #     },
    #     'spb_data': {
    #         'avg_price': spb_latest_price,
    #         'change': "-0.5%"  # Заглушка
    #     }
    # }
    #
    # # Передаем все данные в шаблон
    # context = {
    #     'latest_articles': latest_articles,
    #     'popular_districts': popular_districts,
    #     'market_pulse': market_pulse,
    # }
    #
    # return render(request, 'realty_analytics/index.html', context)




def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user) # Автоматически входим после регистрации
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

class CustomLoginView(LoginView):
    # def get(self, request):
    #     form = CustomUserCreationForm()
    #     return render(request, 'registration/register.html', {'form': form})

    # def post(self, request, *args, **kwargs):
    template_name = 'registration/login.html' # Указываем наш шаблон
    # Вы можете добавить дополнительные параметры, если нужно

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home') # Куда перенаправить после выхода

@login_required
def profile_view(request):
    # Профиль уже связан с user, поэтому мы можем получить его напрямую
    return render(request, 'realty_analytics/profile.html')



