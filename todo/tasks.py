from celery import shared_task
from .models import Todo

@shared_task
def create_todo_task(title, description):
    Todo.objects.create(title=title, description=description)
    return "Todo created: {}". format(title)


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
