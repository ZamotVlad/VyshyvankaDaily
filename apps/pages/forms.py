from django import forms

from .models import ContactMessage


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "subject", "message", "honeypot"]
        widgets = {
            "honeypot": forms.TextInput(
                attrs={"style": "display:none;", "tabindex": "-1", "autocomplete": "off"}
            ),
        }
