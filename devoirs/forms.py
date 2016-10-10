# -*- coding:utf8 -*-

from django import forms

from devoirs.models import Periode, Conseil

class PeriodeForm(forms.ModelForm):
    class Meta:
        model = Periode
        fields=['nom', 'debut', 'fin']

class ConseilForm(forms.ModelForm):
    class Meta:
        model = Conseil
        fields=['classe', 'periode', 'date', 'president',
                'limite_saisie']
