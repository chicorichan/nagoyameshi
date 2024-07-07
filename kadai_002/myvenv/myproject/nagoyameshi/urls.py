from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static

app_name    = "nagoyameshi"
urlpatterns = [
    path('', views.index, name="index"),
    path('restaurant/<int:pk>/', views.restaurant, name="restaurant"),
    path('review/<int:pk>/', views.review, name="review"),
    path('review_edit/<int:pk>/', views.review_edit, name="review_edit"),
    path('review_delete/<int:pk>/', views.review_delete, name="review_delete"),

    path('Fav/<int:pk>/', views.fav, name="fav"),
    path('mypage/', views.mypage, name="mypage"),
    path('reservation/<int:pk>/', views.reservation, name="reservation"),
    path('reservation_cancel/<int:pk>/', views.reservation_cancel, name="reservation_cancel"),
    
    path("checkout/", views.checkout, name="checkout"),
    path("success/", views.success, name="success"),
    path("portal/", views.portal, name="portal"),
    path('premium/', views.premium, name="premium"),
]

#画像のURL設定
if settings.DEBUG:
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)