from django import forms

from .models import AuthorApplication, JobApplication


class AuthorApplicationForm(forms.ModelForm):
    class Meta:
        model = AuthorApplication
        fields = ["pen_name", "bio", "sample"]
        labels = {"pen_name": "Pen name", "bio": "About you", "sample": "A sample of your writing"}
        widgets = {"bio": forms.Textarea(attrs={"rows": 3}), "sample": forms.Textarea(attrs={"rows": 7})}


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ["note", "portfolio_url"]
        labels = {"note": "Why you're a good fit", "portfolio_url": "Portfolio or sample link (optional)"}
        widgets = {"note": forms.Textarea(attrs={"rows": 5})}
