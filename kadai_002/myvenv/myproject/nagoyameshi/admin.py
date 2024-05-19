from django.contrib import admin

# Register your models here.
# == This code was created by https://noauto-nolife.com/post/django-auto-create-models-forms-admin/== #

from django.contrib import admin
from .models import Category,Restaurant,Reservation,Review,Fav,Company

from django.utils.safestring import mark_safe

class CategoryAdmin(admin.ModelAdmin):
    list_display	= [ "id", "name" ]

class RestaurantAdmin(admin.ModelAdmin):
    list_display	= [ "id", "name", "category", "img", "description", "created_date", "update_date", "budget", "capacity", "start", "end" ]

    def img(self,obj):
        return mark_safe('<img src="{}" style="width:100px; height:auto;">'.format(obj.img.url))

class ReservationAdmin(admin.ModelAdmin):
    list_display	= [ "id", "date", "user", "restaurant", "people" ]

class ReviewAdmin(admin.ModelAdmin):
    list_display	= [ "id", "created_date", "user", "restaurant", "comment", "stars" ]

class FavAdmin(admin.ModelAdmin):
    list_display	= [ "id", "created_date", "user", "restaurant" ]

class CompanyAdmin(admin.ModelAdmin):
    list_display	= [ "id", "name", "address", "phone", "history", "terms" ]


admin.site.register(Category,CategoryAdmin)
admin.site.register(Restaurant,RestaurantAdmin)
admin.site.register(Reservation,ReservationAdmin)
admin.site.register(Review,ReviewAdmin)
admin.site.register(Fav,FavAdmin)
admin.site.register(Company,CompanyAdmin)
