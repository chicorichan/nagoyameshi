from django.shortcuts import render, redirect
from django.views import View
from .models import Restaurant,Category,Review,Fav,Reservation

from .forms import RestaurantCategorySearchForm,ReviewForm,FavForm, ReservationForm, ReviewEditForm



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

        # 有料会員状態をチェックして、その結果をcontextに入れる
        context["is_premium"]       = premium_check(request)

        return render(request, "nagoyameshi/restaurant.html", context)
    
restaurant  = RestaurantView.as_view()

#飲食店のレビューを受け付けるビュー
class ReviewView(View):
    def post(self, request, pk, *args, **kwargs):

        # 有料会員登録をチェックする
        if not premium_check(request):
            messages.info(request, "このサービスをご利用になるには画面右上から有料会員登録を行ってください　")
            return redirect("nagoyameshi:restaurant", pk)

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


# レビュー編集をするビュー
# pkはReviewのid
class ReviewEditView(LoginRequiredMixin,View):
    def get(self, request, pk, *args, **kwargs):
        # 編集したいレビューを表示
        # 自分が投稿したレビューではない場合は店舗検索画面へリダイレクト

        review = Review.objects.filter(id=pk, user=request.user).first()

        if not review:
            print("このレビューは存在しないか、自身で投稿したものではありません。")
            return redirect("nagoyameshi:index")
        context = {}
        context["review"]   = review
        return render(request, "nagoyameshi/review_edit.html", context)
        
    def post(self, request, pk, *args, **kwargs):

        # TODO: ここで編集処理を受け付ける。
        review = Review.objects.filter(id=pk, user=request.user).first()        
        if not review:
            print("このレビューは存在しないか、自分で投稿したものではありません。")
            return redirect("nagoyameshi:index")
        # request.POSTの中に、 stars と comment が入っている。
        # stars と commentをバリデーションする。

        # フォームクラス(データ) この場合、新規作成される。
        # フォームクラス(データ, instance=編集したいオブジェクト)
        form = ReviewEditForm(request.POST, instance=review)

        if form.is_valid():
            form.save()
            messages.success(request, "レビュー編集が完了しました　")
        else:
            print("編集失敗")
            print(form.errors)
            messages.info(request, "レビュー編集が失敗しました　")

        return redirect("nagoyameshi:mypage")

review_edit = ReviewEditView.as_view()

#review削除をするビュー
class ReviewDeleteView(LoginRequiredMixin,View):
    def post(self, request, pk, *args, **kwargs):

        review = Review.objects.filter(id=pk, user=request.user).first()        

        if not review:
            print("このレビューは存在しないか、自分で投稿したものではありません。")
            return redirect("nagoyameshi:index")
        # 削除する。
        review.delete()
        messages.info(request, "投稿レビューを削除しました　")

        return redirect("nagoyameshi:mypage")

review_delete = ReviewDeleteView.as_view()


#飲食店のお気に入りを受けつけるビュー
# お気に入り登録する店舗、すでに登録されていないか、チェックする。
class FavView(View):
    def post(self, request, pk, *args, **kwargs):

       # 有料会員登録をチェックする
        if not premium_check(request):
            messages.info(request, "このサービスをご利用になるには画面右上から有料会員登録を行ってください　")
            return redirect("nagoyameshi:restaurant", pk)

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

           # 有料会員登録をチェックする
        if not premium_check(request):
            messages.info(request, "このサービスをご利用になるには画面右上から有料会員登録を行ってください　")
            return redirect("nagoyameshi:restaurant", pk)

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

class ReservationCancelView(LoginRequiredMixin,View):

    # pk はキャンセルしたい予約(Reservation)のid
    def post(self, request, pk, *args, **kwargs):
        #pk を使って予約データを取り出す
        
        # Reservationモデルを使ってidがpkのデータを取り出す。
        Reservation.objects.filter(id=pk)

        # userでも絞り込みをすることで、 予約をしていない人が勝手に予約をキャンセルすることはできない。
        reservation = Reservation.objects.filter(id=pk, user=request.user).first()

        # datetime型なので、date型に直す deadline.date 
        deadline = reservation.date - timezone.timedelta(days=1)
        today = timezone.now()

        if today.date() <= deadline.date():
            print("キャンセルできる")
            messages.success(request, "予約を取り消しました　")

            # 予約の削除(キャンセル)
            reservation.delete()
        else:
            messages.error(request, "キャンセル可能期間が過ぎています　")

        return redirect("nagoyameshi:mypage")


reservation_cancel  = ReservationCancelView.as_view()


# マイページを表示するビュー
# マイページはログイン済みのユーザーのみ発動
class MypageView(LoginRequiredMixin,View):
    def get(salf, request, *args, **kwargs):

        # 予約の一覧、お気に入りの一覧、レビュー一覧をそれぞれ見られるようにする
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
        request.user.paid_member   = checkout_session["customer"]
        request.user.save()

        print("有料会員登録しました！")
        messages.success(request, "有料会員登録しました")

        return redirect("nagoyameshi:index")

success     = SuccessView.as_view()


# サブスクリプションの操作関係
class PortalView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):

        if not request.user.paid_member:
            print( "有料会員登録されていません")
            return redirect("nagoyameshi:index")

        # ユーザーモデルに記録しているカスタマーIDを使って、ポータルサイトへリダイレクト
        portalSession   = stripe.billing_portal.Session.create(
            customer    = request.user.paid_member,
            return_url  = request.build_absolute_uri(reverse_lazy("nagoyameshi:index")),
        )

        return redirect(portalSession.url)

portal      = PortalView.as_view()

class PremiumView(LoginRequiredMixin,View):
    def get(self, request, *args, **kwargs):
        
        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=request.user.paid_member)
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



        return redirect("nagoyameshi:index")

premium     = PremiumView.as_view()

# 有料会員かどうかをチェックして、ブーリアン値を返す関数をreview fav reserveition.view内に組み込む
def premium_check(request):

        # 有料会員登録をしていない場合は、 None 
        print(request.user.paid_member)

        is_premium = False

        # "" と None 両方が無料会員として扱われる。
        if not request.user.paid_member:
            print("まだ有料会員登録をしていません。")
            return is_premium

        # カスタマーIDを元にStripeに問い合わせ
        try:
            subscriptions = stripe.Subscription.list(customer=request.user.paid_member)
        except:
            print("このカスタマーIDは無効です。")
            request.user.paid_member = ""
            request.user.save()

            return is_premium
        
        # Noneの状態で↑の処理を実行すると、次のif文でサブスクリプションは有効と判断される。
        print(subscriptions)
        
        # ステータスがアクティブであるかチェック。
        for subscription in subscriptions.auto_paging_iter():
            if subscription.status == "active":
                print("サブスクリプションは有効です。")

                is_premium = True

        if not is_premium:
            request.user.paid_member = ""
            request.user.save()

        return is_premium
