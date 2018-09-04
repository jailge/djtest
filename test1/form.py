from django import forms
from . import models


class SysConfigForm(forms.Form):
    pass
    # TasksList = forms.ChoiceField(choices=)


class AddForm(forms.Form):
    a = forms.IntegerField()
    b = forms.IntegerField()
    IntervalList = forms.ChoiceField(choices=[('seconds','Seconds'),('minutes','Minutes')])
    # forms.ModelChoiceField(label='队列', queryset=)


class IntervalForm(forms.Form):
    every = forms.IntegerField()

