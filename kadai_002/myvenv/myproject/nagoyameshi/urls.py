from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name    = "nagoyameshi"
urlpatterns = [
    path('', views.index, name="index"),
    path('restaurant/<int:pk>/', views.restaurant, name="restaurant"),
    path('review/<int:pk>/', views.review, name="review"),
    path('Fav/<int:pk>/', views.fav, name="fav"),
    #path('mypage'/mypage, name="mypage")
]

#画像のURL設定
if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)