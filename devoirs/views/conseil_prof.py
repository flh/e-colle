# -*- coding:utf8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F

import datetime

from devoirs.models import Periode, Conseil, Appreciation, Bulletin
from accueil.models import Classe
from devoirs.forms import BulletinFormset

from colleur.views import is_colleur

@user_passes_test(is_colleur, login_url='accueil')
def prof_conseil_liste(request):
    limite = datetime.date.today() - datetime.timedelta(days=10)
    prochains = Conseil.objects.filter(date__gte=limite,
            classe__classeprof__colleur=request.user.colleur)
    anciens = Conseil.objects.filter(date__lt=limite,
            classe__classeprof__colleur=request.user.colleur)
    return render(request, 'colleur/conseil_liste.html', {
        'prochains_conseils': prochains,
        'anciens_conseils': anciens,
        })

@user_passes_test(is_colleur, login_url='accueil')
def epreuves_conseil(request, pk):
    pass

@user_passes_test(is_colleur, login_url='accueil')
def saisies_conseil(request, pk):
    conseil = get_object_or_404(Conseil, pk=pk)
    appr_qs = Appreciation.objects.filter(bulletin__conseil=conseil,
            professeur__colleur=request.user.colleur)
            
    if request.method == 'POST':
        formset = BulletinFormset(request.POST, queryset=appr_qs)
        if formset.is_valid():
            formset.save()
    else:
        formset = BulletinFormset(queryset=appr_qs)

    return render(request, 'colleur/appreciations.html',
            {'formset': formset,})
