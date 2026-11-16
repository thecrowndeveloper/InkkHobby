from django.urls import path

from . import views

app_name = "wallet"

urlpatterns = [
    path("", views.wallet_home, name="home"),
    path("daily/", views.daily_claim, name="daily"),
    path("unlock/<int:chapter_id>/", views.unlock, name="unlock"),
    path("buy/<slug:code>/", views.buy_pack, name="buy"),
]
