from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import User, Result
import json
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

# Загрузка эталонных маршрутов
def load_reference_routes():
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'reference_routes.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

REFERENCE_ROUTES = load_reference_routes()

# Авторизация
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'route_builder/login.html', {'error': 'Неверные учетные данные'})
    return render(request, 'route_builder/login.html')

# Выход
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# Главная страница
@login_required
def index(request):
    # Загрузка данных станций
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'stations.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        stations = json.load(f)
    
    return render(request, 'route_builder/index.html', {
        'start_station': 'Воркута',
        'stations_json': json.dumps(stations),
        'is_admin': request.user.role == 'admin'
    })

# Отправка результата
@login_required
@csrf_exempt
def submit_result(request):
    print("User:", request.user)
    if request.method == 'POST' and request.user.role == 'participant':
        data = json.loads(request.body)
        
        # Сохраняем результат
        result = Result(
            participant=request.user,
            route_data=data,
            total_time=data['total_time'],
            total_distance=data['total_distance']
        )
        
        # Автоматическая проверка
        best_match = None
        best_score = 0
        
        for ref_name, ref_data in REFERENCE_ROUTES.items():
            # Простая проверка: совпадение станций и расстояния
            score = 0
            user_stations = [point['station'] for point in data['route']]
            
            if user_stations == ref_data['stations']:
                score += 50
            elif set(user_stations) == set(ref_data['stations']):
                score += 30
            
            if abs(data['total_distance'] - ref_data['total_distance']) < 10:
                score += 20
                
            if score > best_score:
                best_score = score
                best_match = ref_name
                result.reference_time = ref_data['total_time']
        
        # Если результат лучше эталонного - требует ручной проверки
        if result.reference_time and data['total_time'] < result.reference_time:
            result.is_approved = False
        else:
            result.is_approved = best_score > 40
            
        result.save()
        
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

# Страница администратора
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('index')
    
    participants = User.objects.filter(role='participant')
    results = Result.objects.all().order_by('total_time')
    
    return render(request, 'route_builder/admin_dashboard.html', {
        'participants': participants,
        'results': results
    })

# Страница благодарности
@login_required
def thank_you(request):
    return render(request, 'route_builder/thank_you.html')

@login_required
def approve_result(request, result_id):
    if request.method == 'POST' and request.user.role == 'admin':
        try:
            result = Result.objects.get(id=result_id)
            result.is_approved = True
            result.save()
            return JsonResponse({'status': 'success'})
        except Result.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Result not found'}, status=404)
    return JsonResponse({'status': 'error'}, status=400)