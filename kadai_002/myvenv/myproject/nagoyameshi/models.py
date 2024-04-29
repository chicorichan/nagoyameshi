from django.db import models
#最大値と最小値の制限を課せる
from django.core.validators import MinValueValidator,MaxValueValidator
from django.contrib.auth import get_user_model

#Djangoの中にあるユーザーモデルえお用意することができる
User = get_user_model()

#Create your models here.
#カテゴリモデル
class Category(models.Model):
    name = models.CharField(verbose_name="カテゴリ名",max_length=10)

    def __str__(self):
        return self.name

#飲食店モデル
class Restaurant(models.Model):
    name = models.CharField(verbose_name="店舗名",max_length=100)
  #カテゴリモデルと紐づくcategory/紐づくCategory-nameが削除されたとき、その飲食店は未分類で残る
    category = models.ForeignKey(Category, verbose_name="カテゴリ", on_delete=models.SET_NULL, null=True, blank=True)
  #画像と説明文
    img = models.ImageField(verbose_name="店舗画像", upload_to="nagoyameshi/restaurant/img")
    description = models.TextField(verbose_name="店舗説明文")
  #登録日と更新日
  #auto_now（_add）で自動的に日時を入力してくれる（修正はできない）
    created_date = models.DateTimeField(verbose_name="作成日",auto_now_add=True)
    update_date = models.DateTimeField(verbose_name="編集日",auto_now=True)
  #予算、受け入れ可能人数（0以上の整数）
    budget = models.PositiveIntegerField(verbose_name="予算")
    capacity = models.PositiveIntegerField(verbose_name="受け入れ可能人数")

  #営業時間
    start = models.TimeField(verbose_name="営業開始")
    end = models.TimeField(verbose_name="営業終了")


#予約モデル
class Reservation(models.Model):
    date = models.DateTimeField(verbose_name="予約日時")
    user = models.ForeignKey(User, verbose_name="予約者", on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, verbose_name="対象飲食店", on_delete=models.CASCADE)
    people = models.PositiveIntegerField(verbose_name="予約人数")

#レビューモデル
class Review(models.Model):
    created_date = models.DateTimeField(verbose_name="作成日時", auto_now_add=True)
    user = models.ForeignKey(User, verbose_name="レビューユーザー", on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, verbose_name="対象飲食店", on_delete=models.CASCADE)
    comment = models.TextField(verbose_name="コメント")
    stars = models.IntegerField(verbose_name="評価", validators=[MinValueValidator(1),MaxValueValidator(5)])

    def star_icon(self):
        dic                 = {}
        dic["true_star"]    = self.star * " "
        dic["false_star"]   = (5-self.star)* " "

        return dic


#お気に入り
class Fav(models.Model):
    created_date = models.DateTimeField(verbose_name="登録日",auto_now_add=True)
    user = models.ForeignKey(User, verbose_name="お気に入り登録ユーザー名", on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, verbose_name="対象飲食店", on_delete=models.CASCADE)

#会社情報
class Company(models.Model):
    name = models.CharField(verbose_name="会社名",max_length=20)
    address = models.CharField(verbose_name="所在地",max_length=100)
    phone = models.CharField(verbose_name="電話番号",max_length=15)
    history = models.DateField(verbose_name="設立日")
    terms = models.TextField(verbose_name="規約")

