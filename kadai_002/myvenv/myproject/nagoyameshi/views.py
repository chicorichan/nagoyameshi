from django.shortcuts import render, redirect
from django.views import View
from .models import Restaurant,Category,Review,Fav,Reservation

from .forms import RestaurantCategorySearchForm,ReviewForm,FavForm, ReservationForm


# ページネーション
from django.core.paginator import Paginator 
from django.db.models import Q

# ログイン必須とするために必要
from django.contrib.auth.mixins import LoginRequiredMixin

# DjangoMessageFramework
from django.contrib import messages

#予約時間のバリデーションのため
from django.utils import timezone

#Stripe
import stripe
from django.conf import settings
from django.urls import reverse_lazy

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

        # ユーザーがこの店舗をお気に入り登録しているかをチェックする。

        if request.user.is_authenticated:
            #                                                  ↓未ログイン状態で検索するとエラーになる。
            context["is_faved"]     = Fav.objects.filter(user=request.user,restaurant=context["restaurant"]).exists()
        else:
            context["is_faved"]     = False


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

            # messages を使って、投稿完了をフロントに表示させる。
            messages.success(request, "レビュー投稿が完了しました　")

        else:
            print("保存失敗")
            print(form.errors)
            messages.info(request, "レビュー投稿が失敗しました　")

       #投稿した後は、飲食店詳細ページにリダイレクトする。
        return redirect("nagoyameshi:restaurant", pk)

review = ReviewView.as_view()


#飲食店のお気に入りを受けつけるビュー
# お気に入り登録する店舗、すでに登録されていないか、チェックする。
class FavView(View):
    def post(self, request, pk, *args, **kwargs):

        copied = request.POST.copy()

        # 店舗(restaurant)、ユーザー(user)がFavの中にあるかは .exists() を使う
        fav = Fav.objects.filter(restaurant=pk, user=request.user)
        
        context = {}
        context["is_faved"] = Fav.objects.filter(user=request.user).exists()

        # お気に入り登録している場合は、削除をする。
        if fav:
            fav.delete()
            messages.success(request, "お気に入り登録解除しました　")
        # 登録していない場合は、作成する。
        else:
            copied["restaurant"] = pk
            copied["user"] = request.user
            # FavFormを使ってバリデーション
            form = FavForm(copied)

            if form.is_valid():
                form.save()
                messages.success(request, "お気に入り登録しました　")
            else:
                print("保存失敗")
                print(form.errors)
    
        # 飲食店の詳細ページへリダイレクト
        return redirect("nagoyameshi:restaurant", pk)

# urls.pyから呼び出せるようにする。
fav = FavView.as_view()

#予約受付のビュー
class ReservationView(LoginRequiredMixin, View):

    def get(self, request, pk, *args, **kwargs):

        # TODO:店舗情報も表示させる
        context = {}
        context["restaurant"]   = Restaurant.objects.filter(id=pk).first()

        # 日時の入力フォーム用
        context["deadline"]     = timezone.now() + timezone.timedelta(days=1)

        return render(request,"nagoyameshi/reservation.html", context)
    
    # pkを、Restaurantのpkとする。
    def post(self, request, pk, *args, **kwargs):
        # 予約を受け付ける
        """
        pk(予約したい店舗), request.user(予約する人)、
        
        ユーザー側から受け取る。
        date(予約日時), people(人数)
        """

        # date と peopleの2つに、 restaurant とuserを加える。
        copied  = request.POST.copy()

        copied["restaurant"] = pk
        copied["user"] = request.user

        form = ReservationForm(copied)

        if form.is_valid():
            form.save()
            messages.success(request, "予約が完了しました　")
        else:
            print(form.errors)
            messages.info(request, "予約ができませんでした　")
            values          = form.errors.get_json_data().values()

            for value in values:
                for v in value:
                    messages.error(request, v["message"])
                    
        return redirect("nagoyameshi:mypage")

reservation = ReservationView.as_view()


# マイページを表示するビュー
# マイページはログイン済みのユーザーのみ発動
class MypageView(View):
    def get(salf, request, *args, **kwargs):

        # 予約の一覧、お気に入りの一覧、レビュー一覧がそれぞれ見れるようにする
        context = {}

        # 自分が予約した情報を取り出す。
        context["reservations"] = Reservation.objects.filter(user=request.user)

        # 自分のお気に入り登録をすべて取り出す。
        # 自分のユーザーid は request.user から確認できる。
        context["favs"] = Fav.objects.filter(user=request.user)
        context["reviews"] = Review.objects.filter(user=request.user)

        # 自分が投稿したレビューも取り出せる。
        
        return render(request, "nagoyameshi/mypage.html", context)

# urls.pyから呼び出せるようにする。
mypage = MypageView.as_view()

#Stripe
stripe.api_key  = settings.STRIPE_API_KEY

""""
class IndexView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        return render(request, "nagoyameshi/index.html")

index   = IndexView.as_view()
"""

# 1: 決済の要求
class CheckoutView(LoginRequiredMixin,View):
    def post(self, request, *args, **kwargs):

        # セッションを作る
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': settings.STRIPE_PRICE_ID,
                    'quantity': 1,
                },
            ],
            payment_method_types=['card'],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse_lazy("nagoyameshi:success")) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse_lazy("nagoyameshi:index")),
        )

        # セッションid
        print( checkout_session["id"] )

        return redirect(checkout_session.url)

checkout    = CheckoutView.as_view()


# 顧客がカード情報を入力して決済を終えた後。本当に決済をしたのか調べる。
class SuccessView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):

        # パラメータにセッションIDがあるかチェック
        if "session_id" not in request.GET:
            print("セッションIDがありません。")
            return redirect("nagoyameshi:index")


        # そのセッションIDは有効であるかチェック。
        try:
            checkout_session_id = request.GET['session_id']
            checkout_session    = stripe.checkout.Session.retrieve(checkout_session_id)
        except:
            print( "このセッションIDは無効です。")
            return redirect("nagoyameshi:index")

        print(checkout_session)

        # statusをチェックする。未払であれば拒否する。(未払いのsession_idを入れられたときの対策)
        if checkout_session["payment_status"] != "paid":
            print("未払い")
            return redirect("nagoyameshi:index")

        print("支払い済み")


        # 有効であれば、セッションIDからカスタマーIDを取得。ユーザーモデルへカスタマーIDを記録する。
        request.user.customer   = checkout_session["customer"]
        request.user.save()

        print("有料会員登録しました！")
        messages.success(request, "有料会員登録しました")

        return redirect("nagoyameshi:index")

success     = SuccessView.as_view()


# サブスクリプションの操作関係
class PortalView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):

        if not request.user.customer:
            print( "有料会員登録されていません")
            return redirect("nagoyameshi:index")

        # ユーザーモデルに記録しているカスタマーIDを使って、ポータルサイトへリダイレクト
        portalSession   = stripe.billing_portal.Session.create(
            customer    = request.user.customer,
            return_url  = request.build_absolute_uri(reverse_lazy("nagoyameshi:index")),
        )

        return redirect(portalSession.url)

portal      = PortalView.as_view()

class PremiumView(View):
    def get(self, request, *args, **kwargs):
        
        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=request.user.customer)
        except:
            print("このカスタマーIDは無効です。")
            return redirect("nagoyameshi:index")
        
        # ステータスがアクティブであるかチェック。
        for subscription in subscriptions.auto_paging_iter():
            if subscription.status == "active":
                print("サブスクリプションは有効です。")

                return render(request, "nagoyameshi/premium.html")
            else:
                print("サブスクリプションが無効です。")

        #TODO: 予約・お気に入り登録



        return redirect("bbs:index")

premium     = PremiumView.as_view()
