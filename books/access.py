from wallet.models import ChapterUnlock


def is_owner(user, book):
    return user.is_authenticated and (user == book.author or user.is_staff)


def can_read(user, chapter):
    """Free chapters are open to everyone; locked ones need an unlock (or being the author/staff)."""
    if chapter.is_free:
        return True
    if not user.is_authenticated:
        return False
    if is_owner(user, chapter.book):
        return True
    return ChapterUnlock.objects.filter(user=user, chapter=chapter).exists()
