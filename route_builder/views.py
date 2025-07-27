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

@csrf_exempt  # Временно отключаем CSRF для тестов
@login_required
def submit_result(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print("Received data:", data)  # Для отладки
            
            # Проверяем обязательные поля
            required_fields = ['route', 'total_time', 'total_distance']
            if not all(field in data for field in required_fields):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Отсутствуют обязательные поля'
                }, status=400)
            
            # Сохраняем результат
            result = Result(
                participant=request.user,
                route_data=data['route'],
                total_time=data['total_time'],
                total_distance=data['total_distance']
            )
            
            # Здесь должна быть ваша логика проверки с эталоном
            result.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Результат сохранен'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Неверный формат данных'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({
        'status': 'error',
        'message': 'Метод не разрешен'
    }, status=405)

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