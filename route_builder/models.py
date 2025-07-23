from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('participant', 'Участник'),
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='participant'
    )
    created_by = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL
    )
    
    # Указываем уникальные имена для обратных связей
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name="route_builder_user_set",  # Уникальное имя
        related_query_name="route_builder_user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="route_builder_user_set",  # Уникальное имя
        related_query_name="route_builder_user",
    )
        
class Result(models.Model):
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='results')
    route_data = models.JSONField()  # Сохраняем весь маршрут
    total_time = models.FloatField()
    total_distance = models.FloatField()
    reference_time = models.FloatField(null=True, blank=True)  # Эталонное время
    is_approved = models.BooleanField(default=False)  # Результат проверен
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['total_time']  # Сортировка по времени