from django.urls import path
from .views import FileFieldView
from . import views

app_name = 'patents'
urlpatterns = [
    path('', views.index, name='index'),
    # path('upload/', views.upload, name='upload'),
    path('upload/', FileFieldView.as_view(), name='upload'),
    path('search/', views.search, name='search'),
    path('show/<str:pat_id>/', views.show, name='show')
]
