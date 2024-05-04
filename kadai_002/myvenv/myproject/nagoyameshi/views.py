from django.shortcuts import render
from django.views import View
from .models import Restaurant

from django.db.models import Q

class IndexView(View):

    def get(self, request, *args, **kwargs):
        restaurants = Restaurant.objects.all()
        context={}
        #context["restaurants"]  = Restaurant.objects.all()

         # クエリを初期化
        query = Q()

        if "search" in request.GET:
            words =request.GET["search"].replace("　"," ").split(" ")
            for word in words:
                if word=="":
                    continue 
                else:
                    query &=Q(name__contains=word)
            context["restaurants"] = Restaurant.objects.filter(query)
        else:
            print("?search=はありません。検索はしていません。")
            context["restaurants"]  = Restaurant.objects.all()


        return render(request,"nagoyameshi/index.html",context)


index   = IndexView.as_view()
