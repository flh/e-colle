#-*- coding: utf-8 -*-
from django.conf.urls import url
from . import views

urlpatterns = [
url(r'^periodes/?$', views.periodes, name="periodes"),
url(r'^periodes/modifier/(?P<pk>\d+)$', views.periode_modif, name="modif_periode"),
url(r'^periodes/supprimer/(?P<pk>\d+)$', views.periode_suppr, name="suppr_periode"),
url(r'^conseils/?$', views.conseil_liste, name="conseil_liste"),
url(r'^conseils/modifier/(?P<pk>\d+)$', views.conseil_modif, name="modif_conseil"),
url(r'^conseils/supprimer/(?P<pk>\d+)$', views.conseil_suppr, name="suppr_conseil"),
url(r'^conseils/bulletins/(?P<pk>\d+)$', views.conseil_bulletin, name="conseil_bulletin"),
url(r'^conseils_prof/?$', views.prof_conseil_liste, name="prof_conseil_liste"),
url(r'^conseils_prof/(?P<pk>\d+)$', views.epreuves_conseil, name="epreuves_conseil"),
url(r'^conseils_prof/bulletins/(?P<pk>\d+)$', views.saisies_conseil, name="saisies_conseil"),
]