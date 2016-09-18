# -*- coding: utf8 -*-
from django.db import models
from django.db.models import CASCADE

class AbstractConcoursMatiere(models.Model):
    matiere = models.ForeignKey('accueil.Matiere', on_delete=CASCADE)
    coefficient = models.PositiveSmallIntegerField(default=1)
    option = models.BooleanField()
    ordre = models.PositiveSmallIntegerField(default=1)
    class Meta:
        abstract = True
        ordering = ['ordre']



class ConcoursTemplate(models.Model):
    nom = models.CharField(verbose_name="Nom", max_length=30, blank=False)
    matieres = models.ManyToManyField('accueil.Matiere', through='ConcoursTemplateMatiere')

class ConcoursTemplateMatiere(AbstractConcoursMatiere):
    concours = models.ForeignKey('ConcoursTemplate', on_delete=CASCADE)



class ConcoursBlanc(models.Model):
    classe = models.ForeignKey('accueil.Classe', on_delete=CASCADE)
    nom = models.CharField(verbose_name="Nom", max_length=30,
            blank=False)
    matieres = models.ManyToManyField('accueil.Matiere', through='ConcoursBlancMatiere')
    date = models.DateField()
    class Meta:
        ordering = ['-date']
        verbose_name = "concours blanc"
        verbose_name_plural = "concours blancs"

class ConcoursBlancMatiere(AbstractConcoursMatiere):
    concours_blanc = models.ForeignKey('ConcoursBlanc', on_delete=CASCADE)
    devoir = models.ForeignKey('Devoir', on_delete=CASCADE)
