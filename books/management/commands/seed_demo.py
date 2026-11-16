"""Fill a fresh database with original demo content so the site isn't empty while you build.

    python manage.py seed_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from books.models import Book, Chapter, Genre
from careers.models import Contract, Job

User = get_user_model()

GENRES = [
    ("Fantasy", "Magic, myth and other worlds"),
    ("Romance", "Slow burns and grand gestures"),
    ("Sci-Fi", "Futures worth worrying about"),
    ("Mystery", "Locked rooms and loose ends"),
    ("Action", "Fists, fire and fast pacing"),
    ("Slice of Life", "Quiet days, loud feelings"),
    ("Horror", "Best read with the lights on"),
    ("Historical", "Other centuries, same hearts"),
    ("Isekai", "Another world, another chance"),
    ("Xianxia", "Cultivation and heavenly trials"),
    ("Drama", "People at their limits"),
    ("Comedy", "Because we all need one"),
]

AUTHORS = [
    ("adaeze", "Adaeze Okoye"),
    ("tomi", "Tomi Balogun"),
    ("marguerite", "Marguerite Vale"),
]

BOOKS = [
    ("The Lantern Keeper of Ash Harbour", "adaeze", "webnovel", ["Fantasy", "Mystery"],
     "Every night Ilo lights the harbour lanterns, and every night one burns a colour it shouldn't. When the sea starts answering back, the keeper must decide who the light is really for.",
     "The harbour woke slowly, the way old things do. Ilo climbed the iron stairs with a taper in one hand and a thermos of bitter tea in the other.\n\nBelow, the water turned over in its sleep. Somewhere out past the breakwater a bell rang that no ship owned.\n\nShe counted the lanterns the way her grandmother had taught her: left to right, wish to warning. Forty-one burned gold. The forty-second burned a quiet, patient green."),
    ("Salt, Sugar and Second Chances", "tomi", "novel", ["Romance", "Slice of Life"],
     "A pastry chef who swore off love and a food critic who swore off bakeries share one tiny kitchen for one long winter.",
     "Folake kept two rules in her kitchen: never taste the batter twice, and never learn a customer's name.\n\nThe man at the corner table broke both before the morning rush had ended.\n\n\"The croissant,\" he said, as though announcing a verdict. \"It's unreasonable.\" She decided, against her better judgement, to find out what he meant."),
    ("Orbit of Small Hours", "marguerite", "webnovel", ["Sci-Fi", "Drama"],
     "On a station that never sleeps, the night-shift engineer discovers a message from a crew that hasn't been born yet.",
     "Night shift on Kestrel Station began, as it always did, with the sound of the recyclers clearing their throats.\n\nNaveen drifted along the spine corridor, a coffee bulb tucked against his chest, auditing a ship that had never once required an audit.\n\nThe message arrived at 03:12. It was addressed to him by name, and it was dated four years from now."),
    ("Ninth Gate, Fallen Sword", "adaeze", "anime", ["Action", "Xianxia"],
     "Disgraced and powerless, a sword disciple finds a rusted blade at the bottom of a sealed well, and it has opinions.",
     "Wen Rui had been expelled from the Azure Peak Sect for the third time, which she felt was starting to look like a pattern.\n\nThe well behind the old armoury had been sealed for three hundred years. She dropped a stone in anyway.\n\nIt did not land. Something at the bottom caught it, weighed it, and politely threw it back."),
    ("Letters to the Lighthouse Girl", "tomi", "fanfic", ["Drama", "Romance"],
     "An original-universe epistolary story: forty letters, two coasts, one very patient postman.",
     "Dear Mara,\n\nYou asked me to write about nothing in particular, so I'll begin with the weather, which has been dreadful and entirely my fault.\n\nI took your advice and left the window open. The sea came in. So, in a smaller way, did the idea that I might answer you honestly."),
    ("What the Moth Knew", "marguerite", "novel", ["Horror", "Mystery"],
     "The house on Calder Lane has never had a burglary, a fire or a visitor. The new tenant is beginning to understand why.",
     "The estate agent had a way of saying 'characterful' that made Bea check her pockets.\n\nThe house leaned slightly toward the road, like a stranger trying to overhear.\n\nOn the first night, a single pale moth settled on the bedroom ceiling. On the second night there were six, arranged in a line, pointing at the wardrobe."),
]

JOBS = [
    ("Fiction line editor, fantasy and webnovel", "editor", "₦30,000 per 50k words", "English"),
    ("Proofreader for weekly chapter releases", "proofreader", "₦12,000 per week", "English"),
    ("English to Yorùbá chapter translator", "translator", "Per project", "English → Yorùbá"),
    ("Ghostwriter for serial romance", "writer", "Revenue share", "English"),
]


class Command(BaseCommand):
    help = "Create demo genres, authors, books, chapters, contracts and jobs."

    def handle(self, *args, **options):
        genres = {}
        for i, (name, blurb) in enumerate(GENRES):
            genres[name], _ = Genre.objects.get_or_create(name=name, defaults={"blurb": blurb, "order": i})

        users = {}
        for username, pen in AUTHORS:
            user, created = User.objects.get_or_create(username=username, defaults={"email": f"{username}@example.com"})
            if created:
                user.set_unusable_password()
                user.save()
            profile = user.profile
            profile.pen_name, profile.is_author = pen, True
            profile.bio = profile.bio or f"{pen} writes stories for people who read past their bedtime."
            profile.save()
            users[username] = user

        for n, (title, author, kind, genre_names, synopsis, opening) in enumerate(BOOKS):
            book, created = Book.objects.get_or_create(
                title=title,
                defaults={"author": users[author], "kind": kind, "synopsis": synopsis, "is_published": True, "views": 40 * (len(BOOKS) - n)},
            )
            if not created:
                continue
            book.genres.set([genres[g] for g in genre_names])
            for number in range(1, 9):
                Chapter.objects.create(
                    book=book,
                    number=number,
                    title="The Opening" if number == 1 else f"Chapter {number}",
                    body=opening + (f"\n\nThe story carries on from here, and so will you. (Demo text for chapter {number}.)" if number > 1 else ""),
                )
            if n == 0:
                Contract.objects.create(book=book, contract_type="exclusive", revenue_share_percent=70, status="active")
            if n == 2:
                Contract.objects.create(book=book, contract_type="non_exclusive", revenue_share_percent=50, status="active")

        for title, category, pay, language in JOBS:
            Job.objects.get_or_create(
                title=title,
                defaults={"category": category, "pay": pay, "language": language,
                          "description": "We're looking for a careful, reliable professional to join our growing network. Tell us about your experience and share a sample of your work."},
            )
        self.stdout.write(self.style.SUCCESS("Demo content ready. Visit / to see it."))
