from django.contrib import admin

from .models import Book, Chapter, Comment, Follow, Genre, LibraryEntry, ReadingProgress, Review, TranslationCache


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order")
    prepopulated_fields = {"slug": ("name",)}


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ("number", "title", "coin_price", "is_published")
    show_change_link = True


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "kind", "status", "word_count", "views", "is_published")
    list_filter = ("kind", "status", "is_published", "genres")
    search_fields = ("title", "author__email", "author__profile__pen_name")
    filter_horizontal = ("genres",)
    inlines = [ChapterInline]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("book", "number", "title", "word_count", "coin_price", "is_published")
    list_filter = ("is_published",)
    search_fields = ("title", "book__title")


admin.site.register(Review)
admin.site.register(Comment)
admin.site.register(LibraryEntry)
admin.site.register(Follow)
admin.site.register(ReadingProgress)
admin.site.register(TranslationCache)
