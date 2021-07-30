from django.forms import ModelForm
from django import forms

from .models import *

class SearchPlacesForm(forms.Form):
	location = forms.CharField(widget = forms.TextInput(attrs={
		'id':'floatingLocation','class':'form-control me-2','placeholder':'Enter city','type':'search','aria-label':'Search'}))
