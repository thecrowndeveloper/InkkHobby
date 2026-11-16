from django.urls import path

from . import views

app_name = "books"

urlpatterns = [
    path("", views.home, name="home"),
    path("browse/", views.browse, name="browse"),
    path("search/", views.browse, name="search"),
    path("genres/<slug:genre_slug>/", views.browse, name="genre"),
    path("library/", views.my_library, name="library"),
    path("writers/<int:pk>/", views.writer, name="writer"),
    path("writers/<int:pk>/follow/", views.follow_toggle, name="follow"),
    path("book/<slug:slug>/", views.book_detail, name="detail"),
    path("book/<slug:slug>/library/", views.library_toggle, name="library_toggle"),
    path("book/<slug:slug>/review/", views.review_submit, name="review"),
    path("book/<slug:slug>/read/<int:number>/", views.chapter_detail, name="chapter"),
    path("book/<slug:slug>/read/<int:number>/translate/", views.chapter_translate, name="translate"),
    path("book/<slug:slug>/read/<int:number>/comment/", views.comment_submit, name="comment"),
]
