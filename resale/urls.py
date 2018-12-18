from django.contrib import admin
from django.urls import path

from alerts import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('update/', views.update, name='update'),
    path('send/', views.send, name='send')
]
