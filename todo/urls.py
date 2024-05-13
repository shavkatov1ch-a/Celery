from django.urls import path
from .views import TodoListView, create_todo_view, update_todo_view, delete_todo_view

urlpatterns = [
    path('', TodoListView.as_view(), name='todo_list'),
    path('create/', create_todo_view, name='create_todo'),
    path('update/<int:todo_id>/', update_todo_view, name='update_todo'),
    path('delete/<int:todo_id>/', delete_todo_view, name='delete_todo'),
]