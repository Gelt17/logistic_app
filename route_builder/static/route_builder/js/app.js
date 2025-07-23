// Состояние приложения
let route = [];
let currentStation = APP_CONFIG.startStation;
let totalDistance = 0;
let totalTime = 0;

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', () => {
    // Добавляем начальную станцию
    addStation(APP_CONFIG.startStation, 0, 0, false);
    
    // Показываем соседей
    showNeighbors(currentStation);
    
    // Назначаем обработчики
    document.getElementById('undo-btn').addEventListener('click', removeLastStation);
    document.getElementById('export-btn').addEventListener('click', exportRoute);
    
    // Создаем кнопку отправки
    const submitBtn = document.createElement('button');
    submitBtn.id = 'submit-btn';
    submitBtn.className = 'btn';
    submitBtn.textContent = 'Отправить результат';
    submitBtn.addEventListener('click', submitResult);
    document.querySelector('.controls').appendChild(submitBtn);
});

// Функция добавления станции
function addStation(station, distance, time, teamChange) {
    const routeItem = { station, distance, time, teamChange };
    route.push(routeItem);
    currentStation = station;
    totalDistance += distance;
    totalTime += time + (teamChange ? 2 : 0);
    
    updateRouteTable();
    updateTotals();
    showNeighbors(station);
}

// Функция отображения соседних станций
function showNeighbors(station) {
    const neighborsPanel = document.getElementById('neighbors-panel');
    neighborsPanel.innerHTML = '';
    
    const neighbors = APP_CONFIG.stationsData[station];
    if (!neighbors) {
        neighborsPanel.innerHTML = '<p>Нет доступных станций</p>';
        return;
    }
    
    const visitedStations = route.map(item => item.station);
    
    Object.keys(neighbors).forEach(neighbor => {
        if (!visitedStations.includes(neighbor)) {
            const button = document.createElement('button');
            button.className = 'neighbor-btn';
            button.textContent = neighbor;
            
            button.addEventListener('click', () => {
                const distance = neighbors[neighbor];
                const time = distance / 70;
                addStation(neighbor, distance, time, false);
            });
            
            neighborsPanel.appendChild(button);
        }
    });
    
    if (neighborsPanel.children.length === 0) {
        neighborsPanel.innerHTML = '<p>Нет доступных станций</p>';
    }
}

// Функция удаления последней станции
function removeLastStation() {
    if (route.length <= 1) return;
    
    const removedStation = route.pop();
    totalDistance -= removedStation.distance;
    totalTime -= removedStation.time + (removedStation.teamChange ? 2 : 0);
    currentStation = route[route.length - 1].station;
    
    updateRouteTable();
    updateTotals();
    showNeighbors(currentStation);
}

// Функция обновления таблицы маршрута
function updateRouteTable() {
    const tbody = document.querySelector('#route-table tbody');
    tbody.innerHTML = '';
    
    route.forEach((item, index) => {
        const row = document.createElement('tr');
        
        // Станция
        const stationCell = document.createElement('td');
        stationCell.textContent = item.station;
        
        // Время
        const timeCell = document.createElement('td');
        timeCell.textContent = item.time.toFixed(1);
        
        // Расстояние
        const distanceCell = document.createElement('td');
        distanceCell.textContent = item.distance;
        
        // Замена бригады
        const teamCell = document.createElement('td');
        if (index > 0) {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = item.teamChange;
            checkbox.addEventListener('change', (e) => {
                route[index].teamChange = e.target.checked;
                if (e.target.checked) totalTime += 2;
                else totalTime -= 2;
                updateTotals();
            });
            teamCell.appendChild(checkbox);
        }
        
        row.appendChild(stationCell);
        row.appendChild(timeCell);
        row.appendChild(distanceCell);
        row.appendChild(teamCell);
        tbody.appendChild(row);
    });
}

// Функция обновления итогов
function updateTotals() {
    document.getElementById('total-time').textContent = totalTime.toFixed(1);
    document.getElementById('total-distance').textContent = totalDistance;
    document.getElementById('current-station').textContent = currentStation;
}

// Функция экспорта маршрута
function exportRoute() {
    const exportData = {
        route: route,
        total: { time: totalTime, distance: totalDistance }
    };
    
    const jsonString = JSON.stringify(exportData, null, 2);
    const blob = new Blob([jsonString], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `маршрут_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Функция отправки результата
function submitResult() {
    const data = {
        route: route,
        total_time: totalTime,
        total_distance: totalDistance
    };
    
    console.log("Submitting to:", APP_CONFIG.submitUrl);
    console.log("CSRF Token:", APP_CONFIG.csrfToken);
    
    fetch(APP_CONFIG.submitUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': APP_CONFIG.csrfToken
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('HTTP error ' + response.status);
        }
        return response.json();
    })
    .then(data => {
        if (data.status === 'success') {
            window.location.href = APP_CONFIG.thankYouUrl;
        } else {
            alert('Ошибка отправки результата: ' + (data.message || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при отправке результата: ' + error.message);
    });
}