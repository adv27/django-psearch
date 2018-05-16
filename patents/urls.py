from django.urls import path

from . import views
from .views import FileFieldView

app_name = 'patents'
urlpatterns = [
    path('', views.index, name='index'),
    # path('upload/', views.upload, name='upload'),
    path('upload/', FileFieldView.as_view(), name='upload'),
    path('search/', views.search, name='search'),
    path('show/<str:pat_id>/', views.detail, name='show'),
]

# account function
urlpatterns += [
    path('account/create/', views.create_account, name='account_create'),
    path('account/login/', views.login, name='account_login'),
    path('account/logout/', views.logout, name='account_logout'),
]

# rate function
urlpatterns += [
    path('rate/', views.rate, name='rate'),
]
