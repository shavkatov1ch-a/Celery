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

