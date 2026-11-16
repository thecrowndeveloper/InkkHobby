from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from books.models import Book, Chapter
from careers.models import Contract

from . import services
from .models import AuthorEarning

User = get_user_model()


class WalletTests(TestCase):
    def setUp(self):
        self.reader = User.objects.create_user("reader", "reader@example.com", "pw")
        self.author = User.objects.create_user("author", "author@example.com", "pw")
        self.book = Book.objects.create(author=self.author, title="Test Tale", synopsis="x", is_published=True, free_chapters=1)
        self.free = Chapter.objects.create(book=self.book, number=1, title="One", body="a b c")
        self.locked = Chapter.objects.create(book=self.book, number=2, title="Two", body="d e f g")

    def test_daily_claim_once_per_day_and_streak(self):
        coins, streak = services.claim_daily(self.reader)
        self.assertEqual((coins, streak), (3, 1))
        self.assertIsNone(services.claim_daily(self.reader))
        profile = self.reader.profile
        profile.last_checkin = timezone.localdate() - timedelta(days=1)
        profile.save()
        coins, streak = services.claim_daily(self.reader)
        self.assertEqual((coins, streak), (4, 2))

    def test_streak_resets_after_a_missed_day(self):
        profile = self.reader.profile
        profile.last_checkin = timezone.localdate() - timedelta(days=3)
        profile.checkin_streak = 6
        profile.save()
        self.assertEqual(services.claim_daily(self.reader), (3, 1))

    def test_unlock_needs_coins_and_is_idempotent(self):
        with self.assertRaises(services.InsufficientCoins):
            services.unlock_chapter(self.reader, self.locked)
        services.credit(self.reader, 10, "bonus")
        self.assertTrue(services.unlock_chapter(self.reader, self.locked))
        self.assertFalse(services.unlock_chapter(self.reader, self.locked))
        self.reader.profile.refresh_from_db()
        self.assertEqual(self.reader.profile.coins, 5)

    def test_author_earns_only_under_active_contract(self):
        services.credit(self.reader, 20, "bonus")
        services.unlock_chapter(self.reader, self.locked)
        self.assertEqual(AuthorEarning.objects.count(), 0)

        Contract.objects.create(book=self.book, contract_type="exclusive", revenue_share_percent=70, status="active")
        later = Chapter.objects.create(book=self.book, number=3, title="Three", body="h i")
        services.unlock_chapter(self.reader, later)
        earning = AuthorEarning.objects.get()
        self.assertEqual(earning.author_coins, 3)  # 70% of 5 coins, rounded down

    def test_word_count_rolls_up_to_book(self):
        self.book.refresh_from_db()
        self.assertEqual(self.book.word_count, 7)
