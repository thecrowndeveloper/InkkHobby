from django import forms

from .models import Comment, Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        choices=[(5, "5 — Superb"), (4, "4 — Very good"), (3, "3 — Good"), (2, "2 — Fair"), (1, "1 — Poor")],
        coerce=int,
    )

    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {"text": forms.Textarea(attrs={"rows": 4, "placeholder": "What did you taste? What stayed with you?"})}
        labels = {"text": "Your review"}


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Leave a thought for the author and other readers…"})}
        labels = {"body": ""}
