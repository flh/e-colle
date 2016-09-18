# -*- coding: utf8 -*-
from django.db import models
from django.db.models import CASCADE, SET_NULL

class TypeDevoir(models.Model):
    nom = models.CharField(verbose_name="Nom",
            max_length=30, blank=False)
    description = models.CharField(verbose_name="Description",
            max_length=200, blank=True)
    coefficient = models.SmallIntegerField(verbose_name="Coefficient par défaut")
    class Meta:
        verbose_name = "type de devoir"
        verbose_name_plural = "types de devoir"

class Devoir(models.Model):
    type_devoir = models.ForeignKey(TypeDevoir, null=True, on_delete=SET_NULL)
    nom = models.CharField(verbose_name="Nom du devoir", max_length=30, blank=False)
    date = models.DateTimeField(auto_now_add=True)
    classe = models.ForeignKey('accueil.Classe', on_delete=CASCADE)
    professeur = models.ForeignKey('accueil.Prof', on_delete=CASCADE)
    matiere = models.ForeignKey('accueil.Matiere', on_delete=CASCADE)
    coefficient = models.PositiveSmallIntegerField(default=1)
    class Meta:
        ordering = ['-date']
        verbose_name = "devoir"
        verbose_name_plural = "devoirs"

class DevoirNote(models.Model):
    NOTE = 1
    ABSENT = 2
    ABSENT_EXCUSE = 3
    NON_NOTE = 4
    TYPE_NOTE = (
            (NOTE, "Noté"),
            (ABSENT, "Absent"),
            (ABSENT_EXCUSE, "Absent excusé"),
            (NON_NOTE, "Non noté"),
            )
    devoir = models.ForeignKey(Devoir, on_delete=CASCADE)
    eleve = models.ForeignKey('accueil.Eleve', on_delete=CASCADE)
    type_note = models.PositiveSmallIntegerField(choices=TYPE_NOTE)
    note = models.DecimalField(max_digits=5, decimal_places=2)
    class Meta:
        verbose_name = "note obtenue"
        verbose_name_plural = "notes obtenues"

