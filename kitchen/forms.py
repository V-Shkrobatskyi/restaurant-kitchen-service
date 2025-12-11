from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django import forms
from django.forms import TextInput, Textarea, NumberInput, Select

from kitchen.models import Cook, Dish, RestaurantTable


class CookCreationForm(UserCreationForm):
    head_text = "Create Cook"

    class Meta(UserCreationForm.Meta):
        model = Cook
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "years_of_experience", "role",)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if not self.user or not self.user.is_staff:
            if 'role' in self.fields:
                del self.fields['role']

        for field_name in self.fields:
            field = self.fields[field_name]

            if field_name == 'role':
                field.widget.attrs.update({
                    "class": "form-select mb-3"
                })
            else:
                field.widget.attrs.update({
                    "class": "form-control mb-3"
                })

    def save(self, commit=True):
        cook = super().save(commit=False)

        if not self.user or not self.user.is_staff:
            cook.role = 'cook'

        if commit:
            cook.save()
        return cook

    def clean_years_of_experience(self):
        return validate_years_of_experience(self.cleaned_data["years_of_experience"])


def validate_years_of_experience(years_of_experience,):
    if len(str(years_of_experience)) > 2:
        raise ValidationError("Years of experience should be maximum 2 digits")

    return years_of_experience


class CookExperienceUpdateForm(forms.ModelForm):
    head_text = "Update Years of experience"
    years_of_experience = forms.CharField(
        required=True,
        validators=[validate_years_of_experience,]
    )

    class Meta:
        model = Cook
        fields = ("years_of_experience",)


class DishForm(forms.ModelForm):
    cooks = forms.ModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        widget=forms.CheckboxSelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget = TextInput(attrs={
            "class": "form-control mb-3"})
        self.fields["description"].widget = Textarea(attrs={
            "class": "form-control mb-3",
            "rows": "3",
        })
        self.fields["price"].widget = NumberInput(attrs={
            "class": "form-control mb-3"})

    class Meta:
        model = Dish
        fields = "__all__"


class CookSearchForm(forms.Form):
    username = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={"placeholder": "Search by Username"}
        )
    )


class DishSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={"placeholder": "Search by Name"}
        )
    )


class DishTypeSearchForm(forms.Form):
    name = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={"placeholder": "Search by Name"}
        )
    )

class RestaurantTableForm(forms.ModelForm):
    class Meta:
        model = RestaurantTable
        fields = ["number"]
        widgets = {
            "number": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter table number",
            })
        }
