from django import forms

from .models import GuestPostSubmission


class GuestPostSubmissionForm(forms.ModelForm):
    class Meta:
        model = GuestPostSubmission
        fields = [
            "contact_name",
            "email",
            "brand_name",
            "proposed_topic",
            "proposal_description",
            "honeypot",
        ]
        widgets = {
            "honeypot": forms.TextInput(
                attrs={"style": "display:none;", "tabindex": "-1", "autocomplete": "off"}
            ),
        }
