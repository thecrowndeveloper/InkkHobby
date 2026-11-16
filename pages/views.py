from django import forms
from django.conf import settings
from django.contrib import messages
from django.core.mail import mail_admins, send_mail
from django.shortcuts import redirect, render

from .models import ContactMessage

FAQS = [
    ("What is InkHobby?", "A home for web novels, fanfiction, manga and anime stories. Writers publish, readers discover, and editors, proofreaders and translators find work."),
    ("Is reading free?", "The opening chapters of every story are free. After that, chapters unlock with coins. You collect free coins every day with Daily Ink, and you can top up your well whenever you like."),
    ("What is Daily Ink?", "A small daily gift of coins. Collect it every day and your streak grows, and so does the reward. Miss a day and the streak starts again."),
    ("Do coins expire?", "Not at the moment. If that ever changes, we will tell you well in advance."),
    ("How do I become an author?", "Sign in, open For Authors, and send us a short application with a writing sample. Once approved you can publish your stories."),
    ("How do author contracts work?", "Authors can be offered exclusive or non-exclusive contracts. Exclusive stories live only on InkHobby and receive a higher revenue share and more promotion. Non-exclusive stories can be published elsewhere too. The terms are set out in your contract."),
    ("How are authors paid?", "When a reader unlocks a chapter of a story under contract, the author earns their contract share of the coins spent. Earnings are tracked chapter by chapter."),
    ("Can I read in my own language?", "Yes. Signed-in readers can translate a chapter from English into many languages from the reading page. Translations are machine-made, so nuance can be lost."),
    ("Can I find editing or proofreading work?", "Yes. The Jobs page lists open work for editors, proofreaders, translators and writers."),
    ("How do I share a chapter?", "Every book and chapter has share buttons for the major social networks, plus a button that copies a direct link."),
]


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message"]
        widgets = {"message": forms.Textarea(attrs={"rows": 6})}


def about(request):
    return render(request, "pages/about.html")


def faq(request):
    return render(request, "pages/faq.html", {"faqs": FAQS})


def terms(request):
    return render(request, "pages/terms.html")


def privacy(request):
    return render(request, "pages/privacy.html")


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            msg = form.save()
            try:
                mail_admins(f"[InkHobby contact] {msg.subject}", f"From: {msg.name} <{msg.email}>\n\n{msg.message}")
            except Exception:  # the message is already saved; email trouble shouldn't lose it
                pass
            messages.success(request, "Thank you. Your message is with us and we'll reply by email.")
            return redirect("pages:contact")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"name": request.user.profile.display_name, "email": request.user.email}
        form = ContactForm(initial=initial)
    return render(request, "pages/contact.html", {"form": form})
