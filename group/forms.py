
from django import forms
from .models import Group

class CreateGroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'slug', 'description', 'icon'] 
        widgets = {
            'description': forms.Textarea(attrs={'rows':3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.FileInput(attrs={'class': 'form-control'}),
        }

class GroupUpdateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'icon'] 
        widgets = {
            'description': forms.Textarea(attrs={'rows':3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.FileInput(attrs={'class': 'form-control'}),
        }