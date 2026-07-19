from django.urls import path

from apps.pages import views

app_name = "pages"

urlpatterns = [
    path("faq/", views.faq_view, name="faq"),
    path("contacts/", views.contacts_view, name="contact"),
    path("about/", views.about_view, name="about"),
    path("terms-of-use/", views.terms_view, name="terms"),
    path("privacy-policy/", views.privacy_view, name="privacy"),
    path("<slug:slug>/", views.static_page_view, name="static_page"),
]
