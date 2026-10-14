from django import forms
from django.core.validators import RegexValidator

class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=120, label="Full name", widget=forms.TextInput(attrs={"placeholder":"Name to receive the order", "autocomplete":"name"}))
    phone = forms.CharField(max_length=20, label="Phone number", widget=forms.TextInput(attrs={"placeholder":"Your contact number", "autocomplete":"tel", "inputmode":"tel"}))
    address = forms.CharField(max_length=500, label="House / street / landmark", widget=forms.Textarea(attrs={"rows":3, "placeholder":"House name or number, street, nearby landmark", "autocomplete":"street-address"}))
    city = forms.CharField(max_length=100, label="City / town", widget=forms.TextInput(attrs={"placeholder":"City or town", "autocomplete":"address-level2"}))
    district = forms.CharField(max_length=100, label="District", widget=forms.TextInput(attrs={"placeholder":"District", "autocomplete":"address-level1"}))
    postal_code = forms.CharField(max_length=6, label="PIN code", validators=[RegexValidator(r"^\d{6}$", "Enter a valid 6-digit PIN code.")], widget=forms.TextInput(attrs={"placeholder":"6-digit PIN", "inputmode":"numeric", "autocomplete":"postal-code", "maxlength":"6"}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["full_name"].initial = user.get_full_name()
            self.fields["phone"].initial = user.phone
            self.fields["district"].initial = user.district
            self.fields["address"].initial = user.delivery_address
            self.fields["city"].initial = user.delivery_city
            self.fields["postal_code"].initial = user.delivery_postal_code
