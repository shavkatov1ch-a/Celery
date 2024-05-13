from django.contrib import admin
from .models import Todo

class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'created')
    list_filter = ('title', 'created')



admin.site.register(Todo, TodoAdmin)

