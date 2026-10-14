from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import CropListing
User = get_user_model()

class CropListingForm(forms.ModelForm):
    class Meta:
        model = CropListing
        fields = ("name", "variety", "description", "image", "price_per_kg", "stock_kg", "district", "is_active")
        widgets = {"description":forms.Textarea(attrs={"rows":4}), "image":forms.ClearableFileInput(attrs={"accept":"image/jpeg,image/png,image/webp"}), "price_per_kg":forms.NumberInput(attrs={"min":"0.01", "step":"0.01"}), "stock_kg":forms.NumberInput(attrs={"min":"0.01", "step":"0.01"})}

    def clean_image(self):
        image = self.cleaned_data.get("image")
        if image and image.size > 5 * 1024 * 1024:
            raise ValidationError("Choose an image smaller than 5 MB.")
        return image

class StaffCropListingForm(CropListingForm):
    class Meta(CropListingForm.Meta):
        fields = ("farmer", "name", "variety", "description", "price_per_kg", "stock_kg", "district", "is_active")
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["farmer"].queryset = User.objects.filter(role=User.Role.FARMER)
