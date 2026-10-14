from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
class SignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "phone", "district")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = [
            (User.Role.FARMER, "Farmer"),
            (User.Role.CUSTOMER, "Customer"),
        ]
    def clean_role(self):
        role = self.cleaned_data["role"]
        if role == User.Role.EXPERT:
            raise forms.ValidationError("Expert accounts are created by an administrator.")
        return role
