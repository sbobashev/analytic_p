from django.contrib import admin
from .models import District, PriceHistory, Article, Profile, CityAnalytics, AnalyticsDataPoint, ZoneAnalyticsDataPoint


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'pub_date')
    list_filter = ('status', 'pub_date', 'author')
    search_fields = ('title', 'content')


@admin.register(AnalyticsDataPoint)
class AnalyticsDataPointAdmin(admin.ModelAdmin):
    list_display = ('date', 'city_id', 'property_type', 'property_class', 'avg_price_sqm')
    list_filter = ('year', 'quarter', 'city_id', 'property_type', 'property_class')
    ordering = ('-date',)


@admin.register(ZoneAnalyticsDataPoint)
class ZoneAnalyticsDataPointAdmin(admin.ModelAdmin):
    # Добавляем city_id в отображение и фильтры
    list_display = ('date', 'city_id', 'zonen_id', 'property_type', 'property_class', 'avg_price_sqm')
    list_filter = ('year', 'city_id', 'zonen_id', 'property_type', 'property_class')
    search_fields = ('zonen_id', 'city_id')
    ordering = ('-date',)


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('smart_name', 'name', 'city_id', 'ao_id', 'raion_id', 'zonen_id')
    list_filter = ('city_id', 'ao_id')
    search_fields = ('name', 'smart_name')

admin.site.register(Profile)
admin.site.register(PriceHistory)
admin.site.register(CityAnalytics)

