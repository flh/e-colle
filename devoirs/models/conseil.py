# -*- coding: utf8 -*-
from django.db import models
from django.db.models import CASCADE, PROTECT, SET_NULL

class Periode(models.Model):
    nom = models.CharField(max_length=30)
    debut = models.DateField()
    fin = models.DateField()
    class Meta:
        ordering = ['-fin', '-debut']
        unique_together = ('debut', 'fin')
        verbose_name = "période"
        verbose_name_plural = "périodes"

    def __str__(self):
        return self.nom


class AppreciationTemplate(models.Model):
    conseil = models.ForeignKey('Conseil', on_delete=CASCADE)
    professeur = models.ForeignKey('accueil.Prof', on_delete=CASCADE)
    matiere = models.ForeignKey('accueil.Matiere', on_delete=CASCADE)
    texte = models.TextField()
    moyenne = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.ManyToManyField('DevoirNote')
    colles = models.ManyToManyField('accueil.Note')

class Appreciation(models.Model):
    template = models.ForeignKey('AppreciationTemplate', null=True, on_delete=SET_NULL)
    bulletin = models.ForeignKey('Bulletin', on_delete=CASCADE)
    professeur = models.ForeignKey('accueil.Prof', on_delete=CASCADE)
    matiere = models.ForeignKey('accueil.Matiere', on_delete=CASCADE)
    texte = models.TextField()
    moyenne = models.DecimalField(max_digits=5, decimal_places=2)
    notes = models.ManyToManyField('DevoirNote')
    colles = models.ManyToManyField('accueil.Note')
    class Meta:
        unique_together = ('bulletin', 'matiere')
        verbose_name = "appréciation"
        verbose_name_plural = "appréciations"

class Bulletin(models.Model):
    conseil = models.ForeignKey('Conseil', on_delete=CASCADE)
    eleve = models.ForeignKey('accueil.Eleve', on_delete=CASCADE)
    appreciations = models.ManyToManyField('accueil.Matiere', through='Appreciation')
    pied_bulletin = models.TextField(verbose_name="Appréciation du conseil de classe")
    class Meta:
        unique_together = ('conseil', 'eleve')

class Conseil(models.Model):
    periode = models.ForeignKey('Periode', null=True, on_delete=PROTECT)
    date = models.DateField()
    limite_saisie = models.DateField()
    classe = models.ForeignKey('accueil.Classe', on_delete=CASCADE)
    description = models.TextField()
    president = models.ForeignKey('accueil.User', null=True, on_delete=SET_NULL)
    class Meta:
        unique_together = ('periode', 'classe')
        ordering = ['-date']
        verbose_name = "conseil de classe"
        verbose_name_plural = "conseils de classe"
