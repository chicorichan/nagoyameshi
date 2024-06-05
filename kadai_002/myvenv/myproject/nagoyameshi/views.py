from django.shortcuts import render, redirect
from django.views import View
from .models import Restaurant,Category,Review,Fav
from .forms import RestaurantCategorySearchForm,ReviewForm,FavForm

# ページネーション
from django.core.paginator import Paginator 
from django.db.models import Q

class IndexView(View):

    def get(self, request, *args, **kwargs):
        restaurants = Restaurant.objects.all()
        context={}
        #context["restaurants"]  = Restaurant.objects.all()

        #categoryの全データをcontextに含める
        context["categories"]   = Category.objects.all()
        #バリデーションをするにはnagoyameshiにforms.pyが必要

         # クエリを初期化
        query = Q()

        if "search" in request.GET:
            words =request.GET["search"].replace("　"," ").split(" ")
            for word in words:
                if word=="":
                    continue 
                else:
                    query &=Q(name__contains=word)

        """"                    
            context["restaurants"] = Restaurant.objects.filter(query)
        else:
            print("?search=はありません。検索はしていません。")
            context["restaurants"]  = Restaurant.objects.all()
        """
        form = RestaurantCategorySearchForm(request.GET)

        if form.is_valid():
            #指定されたcategoryを取り出す。
            cleaned = form.clean()

            #category未指定字は条件は追加しない
            if cleaned["category"]:
                query &=Q(category=cleaned["category"])

        #検索されているときも、されていないときも.filter(query)でＯＫ
        #context["restaurants"] = Restaurant.objects.filter(query)
        restaurants     = Restaurant.objects.filter(query)

        # =====ページネーション処理======================

        # 複数のデータを、3個おきにページ区切りにする。
        paginator       = Paginator(restaurants,3)

        # 1ページ分の3件のデータがコンテキストに入る。ページの上限を超えた場合、最後のページが出力される。
        # ページの指定があれば、そのページのデータを表示
        if "page" in request.GET:
            restaurants = paginator.get_page(request.GET["page"])
        # もしページの指定がなければ、1ページめを表示。
        else:
            restaurants = paginator.get_page(1)


        # ページと検索のパラメータを両立させたリンクを作っている
        # request.GET.urlencode() には category=1&search= が入っている。 request.GETは実質辞書型なので {"category":1,"search":""}
        # ↑ に、 page=2を追加したい。
        # request.GET["page"] = 2 で、 {"category":1,"search":"","page":2}としたい。
        # request.GET.urlencode() をすると、 category=1&search=&page=2 になる。

        # ただし、 request.GET["page"] = 2 とすることはできない。
        # request は書き換えできないオブジェクト。だから、まずは、.copy() でコピーのオブジェクトを作る。

        # requestオブジェクトのコピーを作る。
        copied  = request.GET.copy()

        # 飲食店データに前のページはあるか？あれば、リンクを作る。
        if restaurants.has_previous():
            # 1つ前のページ番号をセットする。 copied は {"category":1,"search":"","page":2}
            copied["page"]                      = restaurants.previous_page_number()
            #                                            ↓ category=1&search=&page=2
            restaurants.previous_page_link      = "?" + copied.urlencode()

            # copied は {"category":1,"search":"","page":1}
            copied["page"]                      = 1
            #                                            ↓ category=1&search=&page=1                       
            restaurants.first_page_link         = "?" + copied.urlencode()

        if restaurants.has_next():
            # copied は {"category":1,"search":"","page":4}
            copied["page"]                      = restaurants.next_page_number()
            #                                            ↓ category=1&search=&page=4             
            restaurants.next_page_link          = "?" + copied.urlencode()

            # copied は {"category":1,"search":"","page":10}
            copied["page"]                      = restaurants.paginator.num_pages
            #                                            ↓ category=1&search=&page=10                     
            restaurants.end_page_link           = "?" + copied.urlencode()

        context["restaurants"]  = restaurants

        """
        # name="comment" を取得する場合
        if "comment" in request.GET:
            print( request.GET["comment"] ) 
            # ↑このやり方だと、同じname属性が複数ある場合、最後の一つしか取れない。

            # 複数ある場合、全部をリスト型にして取得するには？
            print( request.GET.getlist("comment") )
        

        if "category_multi" in request.GET:
            print( request.GET.getlist("category_multi") )
            # 検索処理をする。
            
            for category in request.GET.getlist("category_multi"):
                # バリデーション
                query |=Q(category=category)
        
        form = RestaurantCategorySearchForm(request.GET)

        if form.is_valid():
            #指定されたcategoryを取り出す。
            cleaned = form.clean()

            #category未指定字は条件は追加しない
            if cleaned["category"]:
                query &=Q(category=cleaned["category"])
        """
        return render(request,"nagoyameshi/index.html",context)

index   = IndexView.as_view()

# 詳細ページを表示するビューを作る。
class RestaurantView(View):
    def get(self, request, pk, *args, **kwargs):

        # 1件分のRestaurantを出す。pkを使って検索する。
        print(pk)
        context = {}
        context["restaurant"]   = Restaurant.objects.filter(id=pk).first()
        # 飲食店に紐づくレビューを表示させる。Reviewモデルを使う
        # 例: Restaurantのidが1のデータを取り出したい場合、filter()はどうなる？
        # Review.objects.filter(restaurant=1)

        # なのでRestaurantのid(モデルのフィールド)がpk(URLのパスコンバータ)のデータを取り出したい場合
        #Review.objects.filter(restaurant=pk)になる
        context["reviews"]      = Review.objects.filter(restaurant=pk)

        return render(request, "nagoyameshi/restaurant.html", context)
    
restaurant  = RestaurantView.as_view()

#飲食店のレビューを受け付けるビュー
class ReviewView(View):
    def post(self, request, pk, *args, **kwargs):

        copied = request.POST.copy()

        # 送られてきたデータではなく、サーバー側でデータをセットして保存できる。
        copied["restaurant"]  = pk
        copied["user"]  = request.user

        #copied["comment"]       = "サーバー側でコメントがセットされました。"
        # 編集されたデータをバリデーションに掛ける。
        form = ReviewForm(copied)
        if form.is_valid():
            form.save()
        else:
            print("保存失敗")
            print(form.errors)

       #投稿した後は、飲食店詳細ページにリダイレクトする。
        return redirect("nagoyameshi:restaurant", pk)

review = ReviewView.as_view()


#飲食店のお気に入りを受けつけるビュー
class FavView(View):
    def post(self, request, pk, *args, **kwargs):

        copied = request.POST.copy()

        copied["restaurant"] = pk
        copied["user"] = request.user

        # FavFormを使ってバリデーション
        form = FavForm(copied)

        if form.is_valid():
            form.save()
        else:
            print("保存失敗")
            print(form.errors)
    
        # 飲食店の詳細ページへリダイレクト
        return redirect("nagoyameshi:restaurant", pk)

# urls.pyから呼び出せるようにする。
fav = FavView.as_view()

# マイページを表示するビュー
class MypageView(View):
    def get(salf, request, *args, **kwargs):

        # 予約の一覧、お気に入りの一覧、レビュー一覧がそれぞれ見れるようにする
        context = {}

        # 自分のお気に入り登録をすべて取り出す。
        # 自分のユーザーid は request.user から確認できる。
        context["favs"] = Fav.objects.filter(user=request.user)


        # 自分が投稿したレビューも取り出せる。
        

        return render(request, "nagoyameshi/mypage.html", context)

# urls.pyから呼び出せるようにする。
mypage = MypageView.as_view()