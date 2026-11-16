from django.contrib import admin

from .models import AuthorEarning, ChapterUnlock, CoinTransaction


@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "balance_after", "kind", "note", "created_at")
    list_filter = ("kind",)
    search_fields = ("user__email", "note")
    readonly_fields = [f.name for f in CoinTransaction._meta.fields]


@admin.register(ChapterUnlock)
class ChapterUnlockAdmin(admin.ModelAdmin):
    list_display = ("user", "chapter", "coins_spent", "created_at")


@admin.register(AuthorEarning)
class AuthorEarningAdmin(admin.ModelAdmin):
    list_display = ("author", "book", "chapter", "coins_spent", "share_percent", "author_coins", "created_at")
    list_filter = ("book",)
