document.addEventListener('DOMContentLoaded', () => {
    //Бургер в меню
    initBurgerMenu();
     // Вызываем инициализацию карты
    initDistrictMap();
    initAnalyticsMap();
    initPriceChart();

    //это графики на главной
    initIndexChart('moscow-price-chart');
    initIndexChart('spb-price-chart');
    initDistrictChart('district-chart');
    initMultiLineChart('class-dynamics-chart');

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





 // --- ДАННЫЕ ДЛЯ МАРКЕРОВ ---
//    const districtMarkers = [
//        {
//            coords: [55.733, 37.564],
//            title: "Станция метро 'Парк культуры'",
//            description: "Крупный транспортный узел"
//        },
//        {
//            coords: [55.745, 37.580],
//            title: "Храм Христа Спасителя",
//            description: "Главный кафедральный собор"
//        },
//        {
//            coords: [55.715, 37.553],
//            title: "Новолужнецкий проезд",
//            description: "Спортивный кластер 'Лужники'"
//        }
//    ];
/**
 * Инициализирует карту на странице района, используя геометрию из data-атрибута.
 */
function initDistrictMap() {
    const mapContainer = document.getElementById('district-map');
    if (!mapContainer) {
        return; // Если элемента нет, ничего не делаем
    }
    const districtName = mapContainer.dataset.name;

    // --- НОВОЕ: Получаем и парсим геометрию ---
    const geometryString = mapContainer.dataset.geometry;
    if (!geometryString) {
        console.error("Атрибут data-geometry не найден или пуст.");
        return;
    }

    let districtGeometry;
    try {
        districtGeometry = JSON.parse(geometryString); // Превращаем JSON-строку обратно в объект
    } catch (e) {
        console.error("Ошибка парсинга JSON геометрии:", e);
        return;
    }

    // Инициализируем карту
    const map = L.map('district-map', {
        attributionControl: false
    });

    // Добавляем слой с картой OSM
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // --- НОВОЕ: Рисуем полигон на основе реальных данных ---
    const districtLayer = L.geoJSON(districtGeometry, {
        style: {
            color: '#800000',
            weight: 2,
            fillColor: '#800000',
            fillOpacity: 0.2
        }
    }).addTo(map)
//      .bindPopup(`<b>{{ district.smart_name|default:district.name }}</b>`); // Это не сработает, нужно передавать имя
    districtLayer.bindPopup(`<b>${districtName}</b>`); // Используем переменную JS

    // Автоматически масштабируем карту, чтобы полигон помещался
    if (districtLayer.getBounds().isValid()) {
        map.fitBounds(districtLayer.getBounds());
    }
}


/**
 * Функция для инициализации графика истории цен.
 */
function initPriceChart() {
    const chartCanvas = document.getElementById('price-chart');
    const mainContent = document.querySelector('.main-content'); // Ищем блок с data-атрибутом

    // Если на странице нет холста для графика или блока с ID, выходим
    if (!chartCanvas || !mainContent || !mainContent.dataset.districtId) {
        return;
    }

    const districtId = mainContent.dataset.districtId; // Получаем ID района

    // Запрашиваем данные с нашего нового API
    fetch(`/api/price-history/${districtId}/`)
        .then(response => response.json())
        .then(data => {
            // Если данные пришли, рисуем график
            const ctx = chartCanvas.getContext('2d');
            new Chart(ctx, {
                type: 'line', // Тип графика - линия
                data: {
                    labels: data.labels, // Метки по оси X (даты)
                    datasets: [{
                        label: 'Средняя цена за м²',
                        data: data.data, // Данные по оси Y (цены)
                        borderColor: '#800000', // Цвет линии (наш бордовый)
                        backgroundColor: 'rgba(128, 0, 0, 0.1)', // Цвет заливки под линией
                        borderWidth: 2,
                        tension: 0.1, // Сглаживание линии
                        fill: true,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false, // Позволяет графику заполнять контейнер
                    scales: {
                        y: {
                            beginAtZero: false // Не начинать ось Y с нуля
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Ошибка загрузки данных для графика:', error));
}


/**
 * Инициализирует график с несколькими линиями (динамика по классам).
 * @param {string} canvasId - ID элемента <canvas>.
 */
/**
 * Инициализирует график с несколькими линиями (динамика по классам).
 * @param {string} canvasId - ID элемента <canvas>.
 */
function initMultiLineChart(canvasId) {
    const chartCanvas = document.getElementById(canvasId);
    if (!chartCanvas) return;

    const zonenId = chartCanvas.dataset.zonenId;
    const propertyType = chartCanvas.dataset.propertyType;
    if (!zonenId || !propertyType) return;

    const apiUrl = `/api/zone-class-dynamics/?zonen_id=${zonenId}&property_type=${propertyType}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(chartData => {
            if (chartData.labels && chartData.labels.length > 0) {

                // Зададим массив цветов для линий
                const lineColors = ['#800000', '#4682B4', '#38A169', '#FF8C00', '#6A5ACD'];

                // Добавляем цвета и другие стили к каждому набору данных
                const styledDatasets = chartData.datasets.map((dataset, index) => {
                    return {
                        ...dataset, // копируем 'label' и 'data'
                        borderColor: lineColors[index % lineColors.length], // Берем цвет по кругу
                        borderWidth: 2,
                        tension: 0.2,
                        fill: false,
                        pointRadius: 2,
                        pointBackgroundColor: lineColors[index % lineColors.length]
                    };
                });

                const ctx = chartCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.labels,
                        datasets: styledDatasets
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: true,
                                position: 'top',
                            },
                            // --- НОВОЕ: Кастомизация всплывающих подсказок ---
                            tooltip: {
                                callbacks: {
                                    title: function(tooltipItems) {
                                        // tooltipItems[0].label будет '2024-Q1'
                                        const label = tooltipItems[0].label;
                                        const [year, quarter] = label.split('-Q');
                                        return `${quarter}-й квартал ${year} г.`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false,
                                ticks: {
                                    callback: value => (value / 1000) + 'k'
                                }
                            }
                        }
                    }
                });

            }
        })
        .catch(error => console.error('Ошибка загрузки данных для мульти-графика:', error));
}

/**
 * Функция для инициализации полноэкранной аналитической карты.
 * (Версия с встроенными данными для обхода CORS)
 */
function initAnalyticsMap() {
    const mapContainer = document.getElementById('analytics-map');
    if (!mapContainer) return;

    // --- НОВОЕ: Получаем и парсим JSON-конфигурацию ---
    const cityId = mapContainer.dataset.cityId;
    const mapConfigString = mapContainer.dataset.mapConfig;

    if (!cityId || !mapConfigString) {
        console.error("Не хватает data-атрибутов для инициализации карты.");
        return;
    }

    let mapConfig;
    try {
        // JSON.parse - это надежный способ, не зависящий от локали
        mapConfig = JSON.parse(mapConfigString);
    } catch (e) {
        console.error("Ошибка парсинга JSON конфигурации карты:", e);
        return;
    }

    // 2. Инициализируем карту с данными из распарсенного объекта
    const map = L.map('analytics-map').setView(mapConfig.center, mapConfig.zoom);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // 3. Загружаем данные GeoJSON
    const apiUrl = `/api/districts/?city_id=${cityId}`;
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            const geojsonLayer = L.geoJSON(data, {
                style: {
                    color: '#800000',
                    weight: 2,
                    fillColor: '#800000',
                    fillOpacity: 0.1
                },
                onEachFeature: function(feature, layer) {
                    const props = feature.properties;
                    const tooltipContent = `<b>${props.smart_name}</b>`;

                    // 4. Используем bindTooltip для подсказки при наведении
                    layer.bindTooltip(tooltipContent, {
                        sticky: true, // Подсказка следует за курсором
                        className: 'district-tooltip' // Добавим класс для стилизации
                    });

                    // 5. Добавляем обработчики событий
                    layer.on({
                        mouseover: function(e) {
                            e.target.setStyle({ weight: 3, fillOpacity: 0.4 });
                        },
                        mouseout: function(e) {
                            geojsonLayer.resetStyle(e.target);
                        },
                        click: function(e) {
                            // Если в данных есть URL, переходим по нему
                            if (props.detail_url) {
                                window.location.href = props.detail_url;
                            }
                        }
                    });
                }
            }).addTo(map);
        });
}


function initAnalyticsMap_old() {
    const mapContainer = document.getElementById('analytics-map');
    if (!mapContainer) {
        return;
    }
    const cityId = mapContainer.dataset.cityId; // Получаем ID города
    if (!cityId) return;
    const apiUrl = `/api/districts/?city_id=${cityId}`;

    // Инициализируем карту с общим видом на Москву

    const map = L.map('analytics-map').setView([55.75, 37.62], 10);


//    if cityId = 78  {
//    const map = L.map('analytics-map').setView([60, 30], 10);
//    }

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    let geojsonLayer; // Переменная для хранения слоя с районами

    // Загружаем данные по всем районам
    fetch(apiUrl)
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
/**
 * Универсальная функция для инициализации графика на главной странице.
 * @param {string} canvasId - ID элемента <canvas> для графика.
 */
function initIndexChart(canvasId) {
    const chartCanvas = document.getElementById(canvasId);
    if (!chartCanvas) {
        return; // Если элемента нет на странице, выходим
    }

    // Получаем параметры из data-атрибутов
    const cityId = chartCanvas.dataset.cityId;
    const propertyType = chartCanvas.dataset.propertyType;
    const propertyClass = chartCanvas.dataset.propertyClass;

    if (!cityId || !propertyType) {
        console.error('Не заданы data-атрибуты city-id или property-type для', canvasId);
        return;
    }

    // Формируем URL для запроса
    const apiUrl = `/api/analytics-chart/?city_id=${cityId}&property_type=${propertyType}&property_class=${propertyClass}`;
    console.log(apiUrl)
    // Запрашиваем данные
    fetch(apiUrl)
        .then(response => response.json())
        .then(chartData => {
            if (chartData.labels && chartData.labels.length > 0) {
                const ctx = chartCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: 'Средняя цена за м²',
                            data: chartData.data,
                            borderColor: '#800000',
                            borderWidth: 2,
                            tension: 0.2,
                            fill: false, // Отключаем заливку для более чистого вида
                            pointRadius: 2, // Уменьшаем точки
                            pointBackgroundColor: '#800000',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false // Скрываем легенду, т.к. график один
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false,
                                ticks: {
                                    callback: function(value, index, values) {
                                        // Форматируем числа (например, 550k)
                                        return (value / 1000) + 'k';
                                    }
                                }
                            }
                        }
                    }
                });
            } else {
                console.warn('Получены пустые данные для графика', canvasId);
            }
        })
        .catch(error => console.error('Ошибка загрузки данных для графика:', error));
}


function initDistrictChart(canvasId) {
    const chartCanvas = document.getElementById(canvasId);
    if (!chartCanvas) return;

    const zonenId = chartCanvas.dataset.zonenId;
    const propertyType = chartCanvas.dataset.propertyType;
    const propertyClass = chartCanvas.dataset.propertyClass;
    if (!zonenId || !propertyType) return;

    // Формируем URL с zonen_id
    const apiUrl = `/api/analytics-chart/?zonen_id=${zonenId}&property_type=${propertyType}&property_class=${propertyClass}`;

    // ... остальной код fetch и new Chart() идентичен initIndexChart ...
    // Запрашиваем данные
    fetch(apiUrl)
        .then(response => response.json())
        .then(chartData => {
            if (chartData.labels && chartData.labels.length > 0) {
                const ctx = chartCanvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: chartData.labels,
                        datasets: [{
                            label: 'Средняя цена за м²',
                            data: chartData.data,
                            borderColor: '#800000',
                            borderWidth: 2,
                            tension: 0.2,
                            fill: false, // Отключаем заливку для более чистого вида
                            pointRadius: 2, // Уменьшаем точки
                            pointBackgroundColor: '#800000',
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false // Скрываем легенду, т.к. график один
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false,
                                ticks: {
                                    callback: function(value, index, values) {
                                        // Форматируем числа (например, 550k)
                                        return (value / 1000) + 'k';
                                    }
                                }
                            }
                        }
                    }
                });
            } else {
                console.warn('Получены пустые данные для графика', canvasId);
            }
        })
        .catch(error => console.error('Ошибка загрузки данных для графика:', error));

}
