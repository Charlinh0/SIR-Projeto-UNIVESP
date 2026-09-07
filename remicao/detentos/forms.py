from django import forms
from .models import Documento

class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ['tipo_documento', 'arquivo']
        widgets = {
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'arquivo': forms.ClearableFileInput(attrs={'class': 'form-control w-100'}),
        }