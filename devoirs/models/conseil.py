# -*- coding: utf8 -*-
from django.db import models
from django.db.models import CASCADE, PROTECT, SET_NULL

from accueil.models import Eleve

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
    moyenne_auto = models.BooleanField(verbose_name="Calcul automatique de la moyenne")
    notes = models.ManyToManyField('DevoirNote')
    colles = models.ManyToManyField('accueil.Note')
    debut = models.DateField()
    fin = models.DateField()
    class Meta:
        unique_together = ('conseil', 'professeur', 'matiere')

    def __init__(self, *args, **kwargs):
        pass

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

    def save(self, *args, **kwargs):
        super(Conseil, self).save(*args, **kwargs)
        self.cree_bulletins()

    def cree_bulletins(self):
        eleves = Eleve.objects.filter(classe=self.classe)
        for eleve in eleves:
            try:
                b = Bulletin(conseil=self, eleve=eleve)
                b.save()
            except: #TODO IntegrityError
                pass

    def cree_appreciation_template(self, prof):
        profs = accueil.Prof.filter(classe=self.classe)
        for prof in profs:
            appr = AppreciationTemplate(conseil=self, professeur=prof,
                    matiere=prof.matiere, moyenne_auto=True,
                    debut=self.periode.debut, fin=self.periode.fin)
            appr.save()

    def cree_appreciations_prof(self, prof):
        bulletins = Bulletin.objects.filter(conseil=self)
        tpl = AppreciationTemplate.objects.filter(professeur=prof, conseil=self)
        for bulletin in bulletins:
            appr = Appreciation()
            bulletin.appreciations.add(appr)
