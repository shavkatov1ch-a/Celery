# Django & celery todo

1. Yangi papka yaratib, uni ichida virtual muhit yaratib uni sozlab, kerakli packagelarni o'rnatamiz.
```shell
mkdir celery_todo
cd celery_todo
virtualenv venv
source venv/bin/activate

pip install django
pip install celery[rabbitmq]
```
2. Djangoda project va app yaratish
```shell
django-admin startproject config .
django-admin startapp todo
```
3. config/settings.py ni ichini sozlaymiz
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'todo',
]


# Celery configuration
CELERY_BROKER_URL = 'amqp://localhost'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_BACKEND = 'rpc://'
# CELERY_BROKER_URL = 'amqp://localhost': Bu qator, Celery uchun amqp protokolini qo'llab-quvvatlaydigan va localhost (o'z kompyuterimiz) orqali bog'lanishni ko'rsatadi. "AMQP" (Advanced Message Queuing Protocol) - bu xabar almashish protokoli
# CELERY_ACCEPT_CONTENT = ['json']: Bu qator, Celery tasklariga JSON formatida ma'lumotni ko'rsatishni aytadi. JSON, ob'ektlarni ustida ishlash uchun qulay formatdir.
# CELERY_RESULT_BACKEND = 'rpc://': Bu qator, Celery tasklarining natijalarini qaytarish uchun amaliy interfeys yordamchisini belgilaydi. "rpc://" yordamchisi, natijalarni koding ko'chirish yordamchisi orqali qaytaradi, ya'ni natijalar ob'ektlari bo'lishi mumkin.

# Umuman, bu kiritishlar RabbitMQ bilan Celeryni ishga tushirish uchun kerak bo'lgan sozlashlardir. Raqamli ma'lumotlar protokollari va interfeyslarni ishlatish orqali xavfsiz va ishonchli muloqotlar o'rnatishimizni ta'minlaydi.


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'todo/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

```
4. Rabbitmq serverni ishga tushirish
```shell
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server
sudo systemctl status rabbitmq-server
```
5. config papkamizni ichida celery.pydegan fayl ochamiz va yozamiz
```shell
# config/celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

```
6. todo appni ichida quyidagi kodlar yoziladi va tasks.py nomli fayl ochiladi
```shell
# todo/models.py
from django.db import models


class Todo(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# todo/admin.py
from django.contrib import admin
from .models import Todo
# Register your models here.

@admin.register(Todo)
class TodoAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'completed')
    list_display_links = ('id', 'title')
    search_fields = ('title',)


# todo/tasks.py
from celery import shared_task
from .models import Todo


@shared_task
def create_todo_task(title, description):
    Todo.objects.create(title=title, description=description)
    return "Todo created: {}".format(title)


@shared_task
def update_todo_task(todo_id, title, description, completed):
    todo = Todo.objects.get(id=todo_id)
    todo.title = title
    todo.description = description
    todo.completed = completed
    todo.save()


@shared_task
def delete_todo_task(todo_id):
    Todo.objects.get(id=todo_id).delete()


# todo/views.py
from django.shortcuts import render, redirect
from django.views.generic import ListView
from .models import Todo
from .tasks import create_todo_task, update_todo_task, delete_todo_task


class TodoListView(ListView):
    model = Todo
    template_name = './todo_list.html'
    context_object_name = 'todos'


def create_todo_view(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        create_todo_task.delay(title, description)
        return redirect('todo_list')
    return render(request, './create_todo.html')


def update_todo_view(request, todo_id):
    todo = Todo.objects.get(id=todo_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        completed = request.POST.get('completed') == 'on'
        update_todo_task.delay(todo_id, title, description, completed)
        return redirect('todo_list')
    return render(request, './update_todo.html', {'todo': todo})


def delete_todo_view(request, todo_id):
    delete_todo_task.delay(todo_id)
    return redirect('todo_list')


# todo/urls.py
from django.urls import path
from todo.views import TodoListView, create_todo_view, update_todo_view, delete_todo_view

urlpatterns = [
    path('', TodoListView.as_view(), name='todo_list'),
    path('create/', create_todo_view, name='create_todo'),
    path('update/<int:todo_id>/', update_todo_view, name='update_todo'),
    path('delete/<int:todo_id>/', delete_todo_view, name='delete_todo'),
]

```
7. todo nomli appimizni ichida templates nomli papka ochib ichida html fayllarni yaratamiz
```html
# create_todo.html
<!-- todo/templates/todo/create_todo.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Todo</title>
</head>
<body>
    <h1>Create Todo</h1>
    <form method="post">
        {% csrf_token %}
        <label for="title">Title:</label>
        <input type="text" id="title" name="title" required><br>
        <label for="description">Description:</label>
        <textarea id="description" name="description"></textarea><br>
        <button type="submit">Create</button>
    </form>
    <a href="{% url 'todo_list' %}">Back to Todo List</a>
</body>
</html>

# todo_list.html
<!-- todo/templates/todo/todo_list.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Todo List</title>
</head>
<body>
    <h1>Todo List</h1>
    <ul>
        {% for todo in todos %}
            <li>{{ todo.title }} - {% if todo.completed %}Completed{% else %}Pending{% endif %}</li>
        {% endfor %}
    </ul>
    <a href="{% url 'create_todo' %}">Create New Todo</a>
</body>
</html>

# update_todo.html
<!-- todo/templates/todo/update_todo.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Update Todo</title>
</head>
<body>
    <h1>Update Todo</h1>
    <form method="post">
        {% csrf_token %}
        <label for="title">Title:</label>
        <input type="text" id="title" name="title" value="{{ todo.title }}" required><br>
        <label for="description">Description:</label>
        <textarea id="description" name="description">{{ todo.description }}</textarea><br>
        <input type="checkbox" id="completed" name="completed" {% if todo.completed %}checked{% endif %}>
        <label for="completed">Completed</label><br>
        <button type="submit">Update</button>
    </form>
    <a href="{% url 'todo_list' %}">Back to Todo List</a>
</body>
</html>

```

8. celeryni ishga tushirish
```shell
python manage.py runserver

celery -A config worker -l info

``` 

