from django import forms
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy

from .models import GuestPostSubmission

PROPOSAL_MAX_LENGTH = 500


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
        description = self.fields["proposal_description"]
        description.max_length = PROPOSAL_MAX_LENGTH
        description.validators.append(MaxLengthValidator(PROPOSAL_MAX_LENGTH))
        description.widget.attrs.update({"maxlength": PROPOSAL_MAX_LENGTH, "rows": 6})
        description.help_text = gettext_lazy("До %(n)s символів.") % {"n": PROPOSAL_MAX_LENGTH}

    def clean_collaboration_type(self):
        return (
            self.cleaned_data.get("collaboration_type")
            or GuestPostSubmission.CollaborationType.GUEST
        )
