from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from wallet import services

from .models import Book, Chapter, ReadingProgress

User = get_user_model()


class ContinueReadingTests(TestCase):
    def setUp(self):
        self.reader = User.objects.create_user("reader", "r@example.com", "pw")
        author = User.objects.create_user("author", "a@example.com", "pw")
        self.book = Book.objects.create(author=author, title="Test Tale", synopsis="x", is_published=True, free_chapters=2)
        self.chapters = [Chapter.objects.create(book=self.book, number=n, title=f"C{n}", body="word " * 50) for n in (1, 2, 3)]

    def test_opening_a_free_chapter_records_progress(self):
        self.client.force_login(self.reader)
        self.client.get(self.chapters[1].get_absolute_url())
        self.assertEqual(ReadingProgress.objects.get(user=self.reader, book=self.book).chapter, self.chapters[1])

    def test_locked_chapter_without_unlock_does_not_record_progress(self):
        self.client.force_login(self.reader)
        self.client.get(self.chapters[2].get_absolute_url())
        self.assertFalse(ReadingProgress.objects.filter(user=self.reader).exists())

    def test_home_shows_continue_reading_for_signed_in_reader(self):
        self.client.force_login(self.reader)
        self.client.get(self.chapters[0].get_absolute_url())
        response = self.client.get(reverse("books:home"))
        self.assertContains(response, "Continue reading")
        self.assertContains(response, "Chapter 1 of 3")

    def test_book_page_offers_resume_button(self):
        self.client.force_login(self.reader)
        self.client.get(self.chapters[1].get_absolute_url())
        self.assertContains(self.client.get(self.book.get_absolute_url()), "Continue chapter 2")
