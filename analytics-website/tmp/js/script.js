document.addEventListener('DOMContentLoaded', () => {
    //Бургер в меню
    initBurgerMenu()
     // Вызываем инициализацию карты
    initDistrictMap();
    initAnalyticsMap()
});



/**
 * Функция для инициализации логики мобильного меню (бургера).
 */
function initBurgerMenu() {
// Находим кнопку-бургер и навигацию в документе
    const burger = document.getElementById('burger-menu');
    const nav = document.querySelector('.main-nav');
    const body = document.body;

    // Если на странице нет бургера или навигации, ничего не делаем
    if (!burger || !nav) {
        return;
    }

    burger.addEventListener('click', () => {
        burger.classList.toggle('is-open');
        nav.classList.toggle('is-open');
        body.classList.toggle('no-scroll');
    });
}


/**
 * Функция для инициализации интерактивной карты на странице района.
 * (Версия с данными, определенными в коде, без загрузки из файла)
 */
function initDistrictMap() {
    const mapContainer = document.getElementById('district-map');
    if (!mapContainer) {
        return; // Выходим, если на странице нет карты
    }

    // --- ДАННЫЕ ДЛЯ ПОЛИГОНА (определяем как константу) ---
    // Координаты для полигона (более точные, чем в первой версии)
    // Важно: Leaflet использует формат [широта, долгота]
    const districtPolygon = [
        [55.742, 37.531],
        [55.750, 37.560],
        [55.748, 37.589],
        [55.728, 37.600],
        [55.708, 37.570],
        [55.718, 37.555],
        [55.742, 37.531]
    ];

    // --- ДАННЫЕ ДЛЯ МАРКЕРОВ ---
    const districtMarkers = [
        {
            coords: [55.733, 37.564],
            title: "Станция метро 'Парк культуры'",
            description: "Крупный транспортный узел"
        },
        {
            coords: [55.745, 37.580],
            title: "Храм Христа Спасителя",
            description: "Главный кафедральный собор"
        },
        {
            coords: [55.715, 37.553],
            title: "Новолужнецкий проезд",
            description: "Спортивный кластер 'Лужники'"
        }
    ];

    // 1. ИНИЦИАЛИЗИРУЕМ КАРТУ И УСТАНАВЛИВАЕМ ВИД ВРУЧНУЮ
    const map = L.map('district-map', {
        attributionControl: false
    }).setView([55.733, 37.57], 13); // Задаем центр и зум

    // Добавляем слой с картой OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // 2. СОЗДАЕМ ПОЛИГОН ИЗ НАШЕЙ КОНСТАНТЫ
    L.polygon(districtPolygon, {
        color: '#800000',
        weight: 2,
        fillColor: '#800000',
        fillOpacity: 0.2
    }).addTo(map)
      .bindPopup('<b>Район Хамовники</b><br>Границы района.');

    // 3. ДОБАВЛЯЕМ МАРКЕРЫ НА КАРТУ
    districtMarkers.forEach(markerData => {
        const marker = L.marker(markerData.coords).addTo(map);
        marker.bindPopup(`<b>${markerData.title}</b><br>${markerData.description}`);
    });

    // Добавляем свой контрол атрибуции
    L.control.attribution({
        prefix: false,
        position: 'bottomright'
    }).addAttribution('© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>').addTo(map);
}


/**
 * Функция для инициализации полноэкранной аналитической карты.
 * (Версия с встроенными данными для обхода CORS)
 */
function initAnalyticsMap() {
    const mapContainer = document.getElementById('analytics-map');
    if (!mapContainer) {
        return;
    }

    // Инициализируем карту с общим видом на Москву
    const map = L.map('analytics-map').setView([55.75, 37.62], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let geojsonLayer; // Переменная для хранения слоя с районами

    // Загружаем данные по всем районам
    fetch('/api/districts/')
        .then(response => response.json())
        .then(data => {
            geojsonLayer = L.geoJSON(data, {
                style: { // Стиль по умолчанию
                    color: '#800000',
                    weight: 2,
                    fillOpacity: 0.1
                },
                // onEachFeature - функция, которая выполняется для каждого района
                onEachFeature: function(feature, layer) {
                    // 1. Добавляем всплывающее окно с названием района
                    layer.bindPopup(feature.properties.name);

                    // 2. Добавляем интерактивность при наведении мыши
                    layer.on({
                        mouseover: function(e) {
                            // При наведении делаем полигон ярче
                            const hoveredLayer = e.target;
                            hoveredLayer.setStyle({
                                weight: 3,
                                fillOpacity: 0.4
                            });
                        },
                        mouseout: function(e) {
                            // При уводе мыши возвращаем стиль по умолчанию
                            geojsonLayer.resetStyle(e.target);
                        }
                    });
                }
            }).addTo(map);
        });
}