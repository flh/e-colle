# -*- coding:utf8 -*-

from django import forms

from devoirs.models import Periode, Conseil, Appreciation, Bulletin

class PeriodeForm(forms.ModelForm):
    class Meta:
        model = Periode
        fields=['nom', 'debut', 'fin']

class ConseilForm(forms.ModelForm):
    class Meta:
        model = Conseil
        fields=['classe', 'periode', 'date', 'president',
                'limite_saisie']

class ConseilAppreciationForm(forms.ModelForm):
    class Meta:
        model = Appreciation
        fields = ['texte']

BulletinFormset = forms.inlineformset_factory(Bulletin, Appreciation,
        fields=('texte',), extra=0)
class BulletinForm(forms.ModelForm):
    class Meta:
        model = Bulletin
        fields = ['pied_bulletin']
