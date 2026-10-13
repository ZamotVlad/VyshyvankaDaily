from django import forms

from .models import GuestPostSubmission


class GuestPostSubmissionForm(forms.ModelForm):
    class Meta:
        model = GuestPostSubmission
        fields = [
            "contact_name",
            "email",
            "brand_name",
            "collaboration_type",
            "proposed_topic",
            "proposal_description",
            "honeypot",
        ]
        widgets = {
            "honeypot": forms.TextInput(
                attrs={"style": "display:none;", "tabindex": "-1", "autocomplete": "off"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collaboration_type"].required = False

    def clean_collaboration_type(self):
        return (
            self.cleaned_data.get("collaboration_type")
            or GuestPostSubmission.CollaborationType.GUEST
        )
