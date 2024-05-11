# 送られてきたデータがルールにあっているかをチェックするために必要
from django import forms
from .models import Restaurant


# Restaurantで検索するためのフォームクラスを作る
class RestaurantCategorySearchForm(forms.ModelForm):

    class Meta:
        model   = Restaurant
        fields  = [ "category" ]
