# -*- coding:utf8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory

import datetime

from devoirs.models import Periode, Conseil, Appreciation, Bulletin
from devoirs.forms import PeriodeForm, ConseilForm, BulletinFormset, BulletinForm
from administrateur.views import ip_filter

@ip_filter
def periodes(request):
    """Affiche la liste des périodes pour les conseils de classe"""
    if request.method == "POST":
        form = PeriodeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('periodes')
    else:
        form = PeriodeForm()

    return render(request, "administrateur/periodes.html", {
        'periodes': Periode.objects.all(),
        'form': form,
        })

@ip_filter
def periode_modif(request, pk):
    periode = get_object_or_404(Periode, pk=pk)
    if request.method == "POST":
        form = PeriodeForm(request.POST, instance=periode)
        if form.is_valid():
            form.save()
            return redirect('periodes')
    else:
        form = PeriodeForm(instance=periode)
    return render(request, "administrateur/periode_modif.html", {'form': form,})

@ip_filter
def periode_suppr(request, pk):
    try:
        get_object_or_404(Periode, pk=pk).delete()
    except Exception:
        messages.error(request, "Impossible d'effacer la période")
    return redirect("periodes")

@ip_filter
def conseil_liste(request):
    if request.method == "POST":
        form = ConseilForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('conseil_liste')
    else:
        form = ConseilForm()

    limite = datetime.date.today() - datetime.timedelta(days=10)
    prochains = Conseil.objects.filter(date__gte=limite)
    anciens = Conseil.objects.filter(date__lt=limite)

    return render(request, 'administrateur/conseil_liste.html', {
        'prochains_conseils': prochains,
        'anciens_conseils': anciens,
        'form' : form,
        })

@ip_filter
def conseil_modif(request, pk):
    conseil = get_object_or_404(Conseil, pk=pk)
    if request.method == "POST":
        form = ConseilForm(request.POST, instance=conseil)
        if form.is_valid():
            form.save()
            return redirect('conseil_liste')
    else:
        form = ConseilForm(instance=conseil)
    return render(request, "administrateur/conseil_modif.html", {'form': form,})

@ip_filter
def conseil_suppr(request, pk):
    try:
        get_object_or_404(Conseil, pk=pk).delete()
    except Exception:
        messages.error(request, "Impossible d'effacer ce conseil de classe")
    return redirect("conseil_liste")

@ip_filter
def conseil_bulletin(request, pk):
    bulletin = get_object_or_404(Bulletin, pk=pk)
    bulletin_qs = Appreciation.objects.filter(bulletin=bulletin)
    if request.method == "POST":
        bulletin_formset = BulletinFormset(request.POST, prefix='apprs',
                queryset=bulletin_qs)
        form = BulletinForm(request.POST, instance=bulletin, prefix='bulletin')
        if form.is_valid() and bulletin_formset.is_valid():
            form.save()
            bulletin_formset.save()
            return redirect('conseil_bulletin', pk)
    else:
        bulletin_formset = BulletinFormset(prefix='apprs',
                queryset=bulletin_qs)
        form = BulletinForm(instance=bulletin, prefix='bulletin')
    return render(request, "administrateur/bulletin.html", {
        'appreciations': bulletin_formset,
        'form' : form,
        })