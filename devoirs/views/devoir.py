# -*- coding:utf8 -*-

from django.shortcuts import render, redirect, get_object_or_404
from django.forms import formset_factory

from devoirs.models import Periode
from devoirs.forms import PeriodeForm
from administrateur.views import ip_filter

@ip_filter
def devoirs(request):
    """Affiche la liste des devoirs"""
    pass
