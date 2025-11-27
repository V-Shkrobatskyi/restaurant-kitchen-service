from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django import forms
from django.forms import TextInput, Textarea, NumberInput

from kitchen.models import Cook, Dish, Table


class CookCreationForm(UserCreationForm):
    head_text = "Create Cook"

    class Meta(UserCreationForm.Meta):
        model = Cook
        fields = UserCreationForm.Meta.fields + ("first_name", "last_name", "years_of_experience", )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget = TextInput(attrs={
                "class": "form-control mb-3"})

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


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ("number", "description")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["number"].widget = NumberInput(attrs={
            "class": "form-control mb-3"})
        self.fields["description"].widget = TextInput(attrs={
            "class": "form-control mb-3"})


class TableSearchForm(forms.Form):
    number = forms.IntegerField(
        required=False,
        label="",
        widget=forms.NumberInput(
            attrs={"placeholder": "Search by Number"}
        )
    )
