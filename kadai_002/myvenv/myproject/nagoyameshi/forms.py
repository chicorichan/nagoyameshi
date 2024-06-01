# 送られてきたデータがルールにあっているかをチェックするために必要
from django import forms
from .models import Restaurant, Review, Fav

# Restaurantで検索するためのフォームクラスを作る
class RestaurantCategorySearchForm(forms.ModelForm):

    class Meta:
        model   = Restaurant
        fields  = [ "category" ]

class BudgetSearchForm(forms.ModelForm):

    class Meta:
        model   = Restaurant
        fields  = [ "budget" ]


# Reviewのバリデーション用のフォームを作る
class ReviewForm(forms.ModelForm):

    class Meta:
        model   = Review
        fields  = ["user","restaurant","comment","stars"]

# Fav のバリデーション用のフォームを作る
class FavForm(forms.ModelForm):
    
    class Meta:
        model   = Fav
        fields  = ["user","restaurant"]