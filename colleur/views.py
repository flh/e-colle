#-*- coding: utf-8 -*-
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from colleur.forms import ColleurConnexionForm, NoteForm, ProgrammeForm, GroupeForm, NoteGroupeForm, CreneauForm, SemaineForm, ColleForm, EleveForm
from accueil.models import Colleur, Matiere, Prof, Classe, Note, Eleve, Semaine, Programme, Groupe, Creneau, Colle, JourFerie
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.db.models import F, Count, Avg, Min, Max, StdDev
from datetime import date, timedelta
from django.http import Http404, HttpResponse, HttpResponseForbidden
from copy import copy
from pdf.pdf import Pdf
from reportlab.platypus import Table, TableStyle
import os
import json
import csv
from ecolle.settings import MEDIA_ROOT, MEDIA_URL, MATHJAX, IMAGEMAGICK

def is_colleur(user):
	"""Renvoie True si l'utilisateur est authentifié e est un colleur, False sinon"""
	if user.is_authenticated() and user.is_active:
		return bool(user.colleur)
	return False

def is_prof(user,matiere,classe):
	"""Renvoie True si l'utilisateur est un prof de la classe classe et dans la matière matière, False sinon"""
	if matiere==None:
		return Prof.objects.filter(classe=classe,colleur=user.colleur).exists()
	else:
		return Prof.objects.filter(classe=classe,matiere=matiere,colleur=user.colleur).exists()

def modifgroupe(colleur,classe):
	"""Renvoie True si colleur a les drois en modification des groupes dans la classe classe, False sinon"""
	return classe.profprincipal==colleur or (colleur in Colleur.objects.filter(colleurprof__classe=classe,colleurprof__modifgroupe=True))

def modifcolloscope(colleur,classe):
	"""Renvoie True si colleur a les drois en modification du colloscope dans la classe classe, False sinon"""
	return classe.profprincipal==colleur or (colleur in Colleur.objects.filter(colleurprof__classe=classe,colleurprof__modifcolloscope=True))

def is_profprincipal(user,classe=False):
	"""Renvoie True si user est professeur principal de la classe classe, False sinon"""
	if classe:
		return classe.profprincipal == user.colleur
	else:
		return bool(user.colleur.classeprofprincipal.all())

def connec(request, id_matiere):
	"""Renvoie la vue de la page de connexion des colleurs. Si le colleur est déjà connecté, redirige vers la page d'accueil des colleurs"""
	matiere=get_object_or_404(Matiere,pk=id_matiere)
	if is_colleur(request.user):
		return redirect('action_colleur')
	error = False
	form = ColleurConnexionForm(matiere,request.POST or None)
	if form.is_valid():
		username=form.cleaned_data['colleur'].user.username
		user = authenticate(username=username,password=form.cleaned_data['password'])
		if user is not None and user.is_active:
			login(request,user)
			request.session['matiere']=matiere.pk
			return redirect('action_colleur')
		else:
			error = True
	return render(request,'colleur/home.html',{'form':form, 'matiere':matiere,'error':error})

@user_passes_test(is_colleur, login_url='accueil')
def changemat(request,id_mat):
	"""La matière courante du colleur devient la matière dont l'id est id_mat, puis redirige vers la page d'accueil des colleurs"""
	matiere=get_object_or_404(Matiere,pk=id_mat,colleur=request.user.colleur)
	request.session['matiere']=matiere.pk
	return redirect('action_colleur')

@user_passes_test(is_colleur, login_url='accueil')
def action(request):
	"""Renvoie la vue de la page d'accueil des colleurs"""
	return render(request,"colleur/action.html")

@user_passes_test(is_colleur, login_url='accueil')
def note(request,id_classe):
	"""Renvoie la vue de la page de gestion des notes"""
	classe=get_object_or_404(Classe,pk=id_classe)
	colleur=request.user.colleur
	matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=request.user.colleur)
	if classe not in colleur.classes.all():
		raise Http404
	groupes = Groupe.objects.filter(classe=classe).values('nom','pk').annotate(nb=Count('groupeeleve'))
	nom_groupes = []
	eleves_groupes = list(Eleve.objects.filter(classe=classe,groupe__isnull=False).values('pk','user__first_name','user__last_name').order_by('groupe__nom','user__last_name','user__first_name'))
	for value in groupes:
		nom_groupes.append((value['nom'],value['pk'],value['nb'],[("{} {}".format(x['user__first_name'].title(),x['user__last_name'].upper()),x['pk']) for x in eleves_groupes[:value['nb']]]))
		del eleves_groupes[:value['nb']]
	eleves=Eleve.objects.filter(classe=classe,groupe__isnull=True).values('pk','user__first_name','user__last_name').order_by('user__last_name','user__first_name')
	modulo = eleves.count() % 3
	return render(request,"colleur/note.html",{'notes':Note.objects.listeNotes(classe,matiere,colleur),'classe':classe,'eleves':eleves,'groupes':nom_groupes,'modulo':modulo,'latex':MATHJAX})

@user_passes_test(is_colleur, login_url='accueil')
def noteEleve(request,id_eleve,id_classe):
	"""Renvoie la vue de la page de notation de l'élève dont l'id est id_eleve et dont la classe a pour id id_classe"""
	# on renseigne aussi la classe dans l'éventualité d'un élève fictif(None) qui n'a pas de classe
	try:
		eleve=Eleve.objects.get(pk=id_eleve)
	except Exception:
		eleve=None
	colleur=request.user.colleur
	if eleve is not None and eleve.classe not in colleur.classes.all():
		raise Http404
	try:
		classe=eleve.classe
	except Exception:
		classe=Classe.objects.get(pk=id_classe)
	colleur = request.user.colleur
	matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=colleur)
	note=Note(matiere=matiere,colleur=colleur,eleve=eleve,classe=classe)
	form=NoteForm(request.POST or None,instance=note)
	if form.is_valid():
		form.save()
		return redirect('note_colleur',classe.pk)
	return render(request,"colleur/noteEleve.html",{'eleve':eleve,'form':form,'classe':classe})

@user_passes_test(is_colleur, login_url='accueil')
def noteGroupe(request,id_groupe,colle=None):
	"""Renvoie la vue de la page de notation de du groupe dont l'id est id_groupe.
	Si colle est renseigné, les champs semaine/jour/heure sont préremplis avec ceux de la colle"""
	groupe=get_object_or_404(Groupe,pk=id_groupe)
	colleur=request.user.colleur
	if groupe.classe not in colleur.classes.all():
		raise Http404
	if colle:
		matiere=colle.matiere
		form=NoteGroupeForm(groupe,matiere,colleur,request.POST or None, initial={'semaine':colle.semaine,'jour':colle.creneau.jour,'heure':colle.creneau.heure})
	else:
		matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=colleur)
		form=NoteGroupeForm(groupe,matiere,colleur,request.POST or None)
	eleves=list(groupe.groupeeleve.all().select_related('user'))
	eleves+=[None]*(3-len(eleves))
	if form.is_valid():
		form.save()
		return redirect('note_colleur', groupe.classe.pk)
	return render(request,"colleur/noteGroupe.html",{'form':form,'groupe':groupe,'eleves':eleves,'matiere':matiere})

@user_passes_test(is_colleur, login_url='accueil')
def noteModif(request,id_note):
	"""Renvoie la vue de la page de modifcation de la note dont l'id est id_note"""
	note=get_object_or_404(Note,pk=id_note)
	colleur=request.user.colleur
	if note.colleur != colleur:
		messages.error(request,"Vous n'êtes pas le colleur de cette colle")
		return redirect('action_colleur')
	elif note.matiere.pk != request.session['matiere']:
		messages.error(request,"Ce n'est pas la bonne matière")
		return redirect('action_colleur')
	form = NoteForm(request.POST or None, instance=note)
	if form.is_valid():
		form.save()
		return redirect('note_colleur', note.classe.pk)
	return render(request,"colleur/noteEleve.html",{'eleve':note.eleve,'form':form,'classe':note.classe})

@user_passes_test(is_colleur, login_url='accueil')
def noteSuppr(request,id_note):
	"""Essaie de supprimer la note dont l'id est id_note puis redirige vers la page de gestion des notes"""
	note=get_object_or_404(Note,pk=id_note)
	if note.colleur != request.user.colleur:
		messages.error(request,"Vous n'êtes pas le colleur de cette colle")
		return redirect('action_colleur')
	elif note.matiere.pk != request.session['matiere']:
		messages.error(request,"Ce n'est pas la bonne matière")
		return redirect('action_colleur')
	note.delete()
	return redirect('note_colleur', note.classe.pk)

@user_passes_test(is_colleur, login_url='accueil')
def resultat(request,id_classe):
	"""Renvoie la vue de la page des résultats de la classe dont l'id est id_classe"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semaines=Semaine.objects.all()
	try:
		semin=semaines[0]
	except Exception:
		raise Http404
	try:
		semax=semaines[semaines.count()-1]
	except Exception:
		raise Http404
	return redirect('resultat2_colleur',id_classe,semin.pk,semax.pk)

@user_passes_test(is_colleur, login_url='accueil')
def resultat2(request,id_classe,id_semin,id_semax):
	"""Renvoie la vue de la page des résultats de la classe dont l'id est id_classe, entre les semaine dont l'id est id_semin et id_semax"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semin=get_object_or_404(Semaine,pk=id_semin)
	semax=get_object_or_404(Semaine,pk=id_semax)
	if classe not in request.user.colleur.classes.all():
		raise Http404
	form=SemaineForm(request.POST or None,initial={'semin':semin,'semax':semax})
	if form.is_valid():
		return redirect('resultat2_colleur',id_classe,form.cleaned_data['semin'].pk,form.cleaned_data['semax'].pk)
	matiere = get_object_or_404(Matiere,pk=request.session['matiere'])
	generateur = Note.objects.classe2resultat(matiere,classe,semin,semax)
	semaines = next(generateur)
	isprof = is_prof(request.user,matiere,classe)
	stat_colleurs = Note.objects.filter(classe=classe,matiere=matiere,semaine__lundi__range=(semin.lundi,semax.lundi)).exclude(note__gt=20).values('colleur__user__first_name','colleur__user__last_name').distinct().annotate(moy=Avg('note'),minimum=Min('note'),maximum=Max('note'),ecarttype=StdDev('note')) if isprof else False
	return render(request,"colleur/resultat.html",{'form':form,'classe':classe,'semaines':semaines,'notes':generateur,'isprof':isprof,'semin':semin,'semax':semax,'stats':stat_colleurs,'latex':MATHJAX})

@user_passes_test(is_colleur, login_url='accueil')
def resultatcsv(request,id_classe,id_semin,id_semax):
	"""Renvoie le fichier csv des résultats de la classe dont l'id est id_classe, entre les semaine dont l'id est id_semin et id_semax"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semin=get_object_or_404(Semaine,pk=id_semin)
	semax=get_object_or_404(Semaine,pk=id_semax)
	matiere = get_object_or_404(Matiere,pk=request.session['matiere'])
	generateur = Note.objects.classe2resultat(matiere,classe,semin,semax)
	semaines = next(generateur)
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="resultats_{}_{}_s{}-s{}.csv"'.format(classe.nom,matiere.nom,semin.numero,semax.numero)
	writer = csv.writer(response)
	writer.writerow(['Élève','rang','moyenne']+['S{}'.format(semaine.numero) for semaine in semaines])
	notation = {i:str(i) for i in range(21)}
	notation[21]="n.n."
	notation[22]="abs"
	for note in generateur:
		writer.writerow([note['eleve'],note['rang'],note['moyenne']]+["|".join([notation[note['note']] for note in value]) for value in note['semaine']])
	return response

@user_passes_test(is_colleur, login_url='accueil')
def programme(request,id_classe):
	"""Renvoie la vue de la page de gestion des programmes de la classe dont l'id est id_classe"""
	classe=get_object_or_404(Classe,pk=id_classe)
	colleur=request.user.colleur
	if classe not in request.user.colleur.classes.all():
		raise Http404
	matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=colleur)
	programmes=Programme.objects.filter(classe=classe,matiere=matiere).select_related('semaine').order_by('-semaine__lundi')
	isprof=False
	if is_prof(request.user,matiere,classe):
		isprof=True
		programme=Programme(matiere=matiere,classe=classe)
		form = ProgrammeForm(request.POST or None,request.FILES or None,instance=programme)
		if form.is_valid():
			form.save()
			return redirect('programme_colleur',classe.pk)
	else:
		form=False
	return render(request,"colleur/programme.html",{'programmes':programmes,'classe':classe,'form':form,'isprof':isprof,'latex':MATHJAX,'jpeg':IMAGEMAGICK})

@user_passes_test(is_colleur, login_url='accueil')
def programmeSuppr(request,id_programme):
	"""Essaie de supprimer le programme dont l'id est id_classe puis redirige vers la page de gestion des programmes"""
	programme=get_object_or_404(Programme,pk=id_programme)
	if not is_prof(request.user,programme.matiere,programme.classe):
		raise Http404
	programme.delete()
	return redirect('programme_colleur', programme.classe.pk)

@user_passes_test(is_colleur, login_url='accueil')
def programmeModif(request,id_programme):
	"""Renvoie la vue de la page de modification du programme dont l'id est id_programme"""
	programme=get_object_or_404(Programme,pk=id_programme)
	if not is_prof(request.user,programme.matiere,programme.classe):
		raise Http404
	form=ProgrammeForm(request.POST or None,request.FILES or None, instance=programme)
	oldfile=MEDIA_ROOT+programme.fichier.name if programme.fichier else False
	if form.is_valid():
		if request.FILES and oldfile:
			if os.path.isfile(oldfile):
				os.remove(oldfile)
			nomimage=oldfile.replace('programme','image').replace('pdf','jpg')
			if os.path.isfile(nomimage):
				os.remove(nomimage)
		form.save()
		return redirect('programme_colleur', programme.classe.pk)
	return render(request,"colleur/programmeModif.html",{'programme':programme,'form':form})

@user_passes_test(is_colleur, login_url='accueil')
def groupe(request,id_classe):
	"""Renvoie la vue de la page de gestion des groupes de la classe dont l'id est id_classe"""
	classe=get_object_or_404(Classe,pk=id_classe)
	if not modifgroupe(request.user.colleur,classe):
		return HttpResponseForbidden("Accès non autorisé")
	groupes = Groupe.objects.filter(classe=classe).prefetch_related('groupeeleve__user')
	form = GroupeForm(classe,None,request.POST or None)
	if form.is_valid():
		form.save()
		return redirect('groupe_colleur', classe.pk)
	return render(request,"colleur/groupe.html",{'classe':classe,'groupes':groupes,'form':form})

@user_passes_test(is_colleur, login_url='accueil')
def groupeSuppr(request,id_groupe):
	"""Essaie de supprimer la groupe dont l'id est id_groupe, puis redirige vers la page de gestion des groupes"""
	groupe=get_object_or_404(Groupe,pk=id_groupe)
	colleur=request.user.colleur
	matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=colleur)
	if not modifgroupe(request.user.colleur,groupe.classe):
		return HttpResponseForbidden("Accès non autorisé")
	else:
		groupe.delete()
	return redirect('groupe_colleur',groupe.classe.pk)

@user_passes_test(is_colleur, login_url='accueil')
def groupeModif(request,id_groupe):
	"""Renvoie la vue de la page de modification du groupe dont l'id est id_groupe"""
	groupe=get_object_or_404(Groupe,pk=id_groupe)
	colleur=request.user.colleur
	matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=colleur)
	if not modifgroupe(request.user.colleur,groupe.classe):
		return HttpResponseForbidden("Accès non autorisé")
	initial = {"eleve{}".format(i):eleve for i,eleve in enumerate(groupe.groupeeleve.all())}
	initial['nom']=groupe.nom
	form = GroupeForm(groupe.classe,groupe,request.POST or None, initial=initial)
	if form.is_valid():
		form.save()
		return redirect('groupe_colleur', groupe.classe.pk)
	return render(request,'colleur/groupeModif.html',{'form':form,'groupe':groupe})

@user_passes_test(is_colleur, login_url='accueil')
def colloscope(request,id_classe):
	"""Renvoie la vue de la page de gestion du colloscope de la classe dont l'id est id_classe"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semaines=list(Semaine.objects.all())
	try:
		semin=semaines[0]
	except Exception:
		raise Http404
	try:
		semax=semaines[-1]
	except Exception:
		raise Http404
	return colloscope2(request,id_classe,semin.pk,semax.pk)

@user_passes_test(is_colleur, login_url='accueil')
def colloscope2(request,id_classe,id_semin,id_semax):
	"""Renvoie la vue de la page de gestion du colloscope de la classe dont l'id est id_classe,
	dont les semaines sont entre la semaine d'id id_semin et celle d'id id_semax"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semin=get_object_or_404(Semaine,pk=id_semin)
	semax=get_object_or_404(Semaine,pk=id_semax)
	if classe not in request.user.colleur.classes.all():
		raise Http404
	form=SemaineForm(request.POST or None,initial={'semin':semin,'semax':semax})
	if form.is_valid():
		return redirect('colloscope2_colleur',id_classe,form.cleaned_data['semin'].pk,form.cleaned_data['semax'].pk)
	groupes = Groupe.objects.filter(classe=classe).values('nom','pk').annotate(nb=Count('groupeeleve'))
	nom_groupes = []
	eleves_groupes = list(Eleve.objects.filter(classe=classe,groupe__isnull=False).values('pk','user__first_name','user__last_name').order_by('groupe__nom','user__last_name','user__first_name'))
	for value in groupes:
		nom_groupes.append((value['pk'],(value['nom'],"; ".join(["{} {}".format(x['user__first_name'].title(),x['user__last_name'].upper()) for x in eleves_groupes[:value['nb']]]))))
		del eleves_groupes[:value['nb']]
	listegroupes = dict(nom_groupes)
	jours,creneaux,colles,semaines=Colle.objects.classe2colloscope(classe,semin,semax)
	return render(request,'colleur/colloscope.html',
	{'semin':semin,'semax':semax,'form':form,'isprof':modifcolloscope(request.user.colleur,classe),'classe':classe,'jours':jours,'listegroupes':listegroupes,'creneaux':creneaux,'listejours':["lundi","mardi","mercredi","jeudi","vendredi","samedi"],'collesemaine':zip(semaines,colles)})

@user_passes_test(is_colleur, login_url='accueil')
def colloscopeModif(request,id_classe,id_semin,id_semax,creneaumodif=None):
	"""Renvoie la vue de la page de modification du colloscope de la classe dont l'id est id_classe,
	dont les semaines sont entre la semaine d'id id_semin et celle d'id id_semax"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semin=get_object_or_404(Semaine,pk=id_semin)
	semax=get_object_or_404(Semaine,pk=id_semax)
	colleur=request.user.colleur
	matiere=get_object_or_404(Matiere,pk=request.session['matiere'],colleur=colleur)
	if not modifcolloscope(request.user.colleur,classe):
		return HttpResponseForbidden("Accès non autorisé")
	form1=SemaineForm(request.POST or None,initial={'semin':semin,'semax':semax})
	if form1.is_valid():
		return redirect('colloscopemodif_colleur',id_classe,form1.cleaned_data['semin'].pk,form1.cleaned_data['semax'].pk)
	form2=ColleForm(classe,None)
	jours,creneaux,colles,semaines = Colle.objects.classe2colloscope(classe,semin,semax,True)
	creneau=creneaumodif if creneaumodif else Creneau(classe=classe)
	form=CreneauForm(request.POST or None,instance=creneau)
	if form.is_valid():
		if creneaumodif:
			form.save()
		else:
			if Creneau.objects.filter(classe=classe,jour=form.cleaned_data['jour'],heure=form.cleaned_data['heure']).exists():
				messages.error(request,"Il y a déjà un créneau ce jour à cette heure, utiliser la fonction dupliquer")
			else:
				form.save()
		return redirect('colloscopemodif_colleur',classe.pk,semin.pk,semax.pk)
	matieres = list(classe.matieres.filter(colleur__classes=classe).values_list('pk','nom','couleur').annotate(nb=Count("colleur")))
	colleurs = list(Classe.objects.filter(pk=classe.pk,matieres__colleur__classes=classe).values_list('matieres__colleur__pk','matieres__colleur__user__username','matieres__colleur__user__first_name','matieres__colleur__user__last_name').order_by("matieres__nom","matieres__colleur__user__last_name","matieres__colleur__user__first_name"))
	listeColleurs = []
	for x in matieres:
		listeColleurs.append(colleurs[:x[3]])
		del colleurs[:x[3]]
	groupes = Groupe.objects.filter(classe=classe)
	largeur=str(500+42*creneaux.count())+'px'
	hauteur=str(27*(len(matieres)+groupes.count()+Colleur.objects.filter(classes=classe).count()))+'px'
	return render(request,'colleur/colloscopeModif.html',
	{'semin':semin,'semax':semax,'form1':form1,'form':form,'form2':form2,'largeur':largeur,'hauteur':hauteur,'groupes':groupes,'matieres':zip(matieres,listeColleurs),'creneau':creneaumodif,'classe':classe,'jours':jours,'creneaux':creneaux,'listejours':["lundi","mardi","mercredi","jeudi","vendredi","samedi"],'collesemaine':zip(semaines,colles)})

@user_passes_test(is_colleur, login_url='accueil')
def creneauSuppr(request,id_creneau,id_semin,id_semax):
	"""Essaie de supprimer le créneau dont l'id est id_creneau puis redirige vers la page de modification du colloscope
	dont les semaines sont entre la semaine d'id id_semin et celle d'id id_semax"""
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe):
		return HttpResponseForbidden("Accès non autorisé")
	try:
		creneau.delete()
	except Exception:
		messages.error(request,"Vous ne pouvez pas effacer un créneau qui contient des colles")
	return redirect('colloscopemodif_colleur',creneau.classe.pk,id_semin,id_semax)

@user_passes_test(is_colleur, login_url='accueil')
def creneauModif(request,id_creneau,id_semin,id_semax):
	"""Renvoie la vue de la page de modification du creneau dont l'id est id_creneau"""
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe):
		return HttpResponseForbidden("Accès non autorisé")
	return colloscopeModif(request,creneau.classe.pk,id_semin,id_semax,creneaumodif=creneau)

@user_passes_test(is_colleur, login_url='accueil')
def creneauDupli(request,id_creneau,id_semin,id_semax):
	"""Renvoie la vue de la page de duplication du creneau dont l'id est id_creneau"""
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe):
		return HttpResponseForbidden("Accès non autorisé")
	creneau.pk=None
	creneau.salle=None
	creneau.save()
	return redirect('colloscopemodif_colleur',creneau.classe.pk,id_semin,id_semax)

@user_passes_test(is_colleur, login_url='accueil')
def ajaxcompat(request,id_classe):
	"""Renvoie ue chaîne de caractères récapitulant les incompatibilités du colloscope de la classe dont l'id est id_classe"""
	LISTE_JOURS=['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche']
	classe=get_object_or_404(Classe,pk=id_classe)
	colleurs = Colle.objects.filter(groupe__classe=classe).values('colleur__user__first_name','colleur__user__last_name','semaine__numero','creneau__jour','creneau__heure').annotate(nbcolles = Count('pk',distinct=True)).filter(nbcolles__gt=1).order_by('semaine__numero','creneau__jour','creneau__heure','colleur__user__last_name','colleur__user__first_name')
	colleurs="\n".join(["le colleur {} {} a {} colles en semaine {} le {} à {}h{}0".format(valeur['colleur__user__first_name'].title(),valeur['colleur__user__last_name'].upper(),valeur['nbcolles'],valeur['semaine__numero'],LISTE_JOURS[valeur['creneau__jour']],valeur['creneau__heure']//2,3*(valeur['creneau__heure']%2)) for valeur in colleurs])
	if colleurs:
		colleurs+="\n\n"
	eleves = Colle.objects.filter(groupe__classe=classe).values('groupe__nom','semaine__numero','creneau__jour','creneau__heure').annotate(nbcolles = Count('pk',distinct=True)).filter(nbcolles__gt=1).order_by('semaine__numero','creneau__jour','creneau__heure','groupe__nom')
	eleves="\n".join(["le groupe {} a {} colles en semaine {} le {} à {}h{}0".format(valeur['groupe__nom'].title(),valeur['nbcolles'],valeur['semaine__numero'],LISTE_JOURS[valeur['creneau__jour']],valeur['creneau__heure']//2,3*(valeur['creneau__heure']%2)) for valeur in eleves])
	if eleves:
		eleves+="\n\n"
	groupes=Colle.objects.filter(groupe__classe=classe).values('groupe__nom','matiere__nom','semaine__numero').annotate(nbcolles = Count('pk',distinct=True)).filter(nbcolles__gt=1).order_by('semaine__numero','matiere__nom','groupe__nom')
	groupes = "\n".join(["le groupe {} a {} colles de {} en semaine {}".format(valeur['groupe__nom'].title(),valeur['nbcolles'],valeur['matiere__nom'].title(),valeur['semaine__numero']) for valeur in groupes])
	reponse=colleurs+eleves+groupes
	print(reponse)
	if not reponse:
		reponse="aucune incompatibilité dans le colloscope"
	return HttpResponse(reponse)

@user_passes_test(is_colleur, login_url='accueil')
def ajaxmajcolleur(request, id_matiere, id_classe):
	"""Renvoie la liste des colleurs de la classe dont l'id est id_classe et de la matière dont l'id est id_matiere, au format json"""
	classe=get_object_or_404(Classe,pk=id_classe)
	matiere=get_object_or_404(Matiere,pk=id_matiere)
	if not modifcolloscope(request.user.colleur,classe):
		return HttpResponseForbidden("Accès non autorisé")
	colleurs=Colleur.objects.filter(matieres=matiere,classes=classe).values('id','user__first_name','user__last_name','user__username').order_by('user__first_name','user__last_name')
	colleurs=[{'nom': value['user__first_name'].title()+" "+value['user__last_name'].upper()+' ('+value['user__username']+')','id':value['id']} for value in colleurs]
	return HttpResponse(json.dumps(colleurs))

@user_passes_test(is_colleur, login_url='accueil')
def ajaxcolloscope(request, id_matiere, id_colleur, id_groupe, id_semaine, id_creneau):
	"""Ajoute la colle propre au quintuplet (matière,colleur,groupe,semaine,créneau) et renvoie le username du colleur
	en effaçant au préalable toute colle déjà existante sur ce couple créneau/semaine"""
	matiere=get_object_or_404(Matiere,pk=id_matiere)
	colleur=get_object_or_404(Colleur,pk=id_colleur)
	groupe=get_object_or_404(Groupe,pk=id_groupe)
	semaine=get_object_or_404(Semaine,pk=id_semaine)
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe):
		return HttpResponseForbidden("Accès non autorisé")
	Colle.objects.filter(semaine=semaine,creneau=creneau).delete()
	feries = [dic['date'] for dic in JourFerie.objects.all().values('date')]
	if semaine.lundi+timedelta(days=creneau.jour) in feries:
		return HttpResponse("jour férié")
	Colle(semaine=semaine,creneau=creneau,groupe=groupe,colleur=colleur,matiere=matiere).save()
	return HttpResponse(colleur.user.username)

@user_passes_test(is_colleur, login_url='accueil')
def ajaxcolloscopeeffacer(request,id_semaine, id_creneau):
	"""Efface la colle sur le créneau dont l'id est id_creneau et la semaine sont l'id est id_semaine
	puis renvoie la chaine de caractères "efface" """
	semaine=get_object_or_404(Semaine,pk=id_semaine)
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe):
		return HttpResponseForbidden("Accès non autorisé")
	Colle.objects.filter(semaine=semaine,creneau=creneau).delete()
	return HttpResponse("efface")

@user_passes_test(is_colleur, login_url='accueil')
def ajaxcolloscopemulti(request, id_matiere, id_colleur, id_groupe, id_semaine, id_creneau, duree, frequence, permutation):
	"""Compte le nombre de colles présente sur les couples créneau/semaine sur le créneau dont l'id est id_creneau
	et les semaines dont le numéro est compris entre celui de la semaine d'id id_semaine et ce dernier + duree
	et dont le numéro est congru à celui de la semaine d'id id_semaine modulo frequence
	S'il n'y en a aucune, ajoute les colles sur les couples créneau/semaine précédents, avec le colleur dont l'id est id_colleur
	le groupe démarre au groupe dont l'id est id_groupe puis va de permutation en permutation, et la matière dont l'id est id_matière"""
	matiere=get_object_or_404(Matiere,pk=id_matiere)
	colleur=get_object_or_404(Colleur,pk=id_colleur)
	groupe=get_object_or_404(Groupe,pk=id_groupe)
	semaine=get_object_or_404(Semaine,pk=id_semaine)
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe) or matiere not in colleur.matieres.all():
		return HttpResponseForbidden("Accès non autorisé")
	frequence = int(frequence)
	modulo = int(semaine.numero)%frequence
	ecrase = Colle.objects.filter(creneau = creneau,semaine__numero__range=(semaine.numero,semaine.numero+int(duree)-1)).annotate(semaine_mod = F('semaine__numero') % frequence).filter(semaine_mod=modulo).count()
	nbferies = JourFerie.objects.recupFerie(creneau.jour,semaine,duree,frequence,modulo)
	if not(ecrase and nbferies[0]):
		return HttpResponse("{}_{}".format(ecrase,nbferies[0]))
	else:
		return ajaxcolloscopemulticonfirm(request, id_matiere, id_colleur, id_groupe, id_semaine, id_creneau, duree, frequence, permutation)

@user_passes_test(is_colleur, login_url='accueil')
def ajaxcolloscopemulticonfirm(request, id_matiere, id_colleur, id_groupe, id_semaine, id_creneau, duree, frequence, permutation):
	"""ajoute les colles sur les couples créneau/semaine sur le créneau dont l'id est id_creneau
	et les semaines dont le numéro est compris entre celui de la semaine d'id id_semaine et ce dernier + duree
	et dont le numéro est congru à celui de la semaine d'id id_semaine modulo frequence, avec le colleur dont l'id est id_colleur
	le groupe démarre au groupe dont l'id est id_groupe puis va de permutation en permutation, et la matière dont l'id est id_matière"""
	matiere=get_object_or_404(Matiere,pk=id_matiere)
	colleur=get_object_or_404(Colleur,pk=id_colleur)
	groupe=get_object_or_404(Groupe,pk=id_groupe)
	semaine=get_object_or_404(Semaine,pk=id_semaine)
	creneau=get_object_or_404(Creneau,pk=id_creneau)
	if not modifcolloscope(request.user.colleur,creneau.classe) or matiere not in colleur.matieres.all():
		return HttpResponseForbidden("Accès non autorisé")
	numsemaine=semaine.numero
	groupes=list(Groupe.objects.filter(classe=creneau.classe).order_by('nom'))
	rang=groupes.index(groupe)
	i=0
	creneaux={'creneau':creneau.pk,'couleur':matiere.couleur,'colleur':colleur.user.username}
	creneaux['semgroupe']=[]
	feries = [dic['date'] for dic in JourFerie.objects.all().values('date')]
	for numero in range(numsemaine,numsemaine+int(duree),int(frequence)):
		try:
			semainecolle=Semaine.objects.get(numero=numero)
			if semainecolle.lundi + timedelta(days = creneau.jour) not in feries:
				Colle.objects.filter(creneau=creneau,semaine=semainecolle).delete()
				groupe=groupes[(rang+i*int(permutation))%len(groupes)]
				Colle(creneau=creneau,colleur=colleur,matiere=matiere,groupe=groupe,semaine=semainecolle).save()
				creneaux['semgroupe'].append({'semaine':semainecolle.pk,'groupe':groupe.nom})
		except Exception:
			pass
		i+=1
	return HttpResponse(json.dumps(creneaux))

@user_passes_test(is_colleur, login_url='accueil')
def agenda(request):
	"""Renvoie la vue de la page de l'agenda"""
	jour=date.today()
	semaine=jour+timedelta(days=-jour.weekday())
	semainemin=semaine+timedelta(days=-21)
	groupes,colles = Colle.objects.agenda(request.user.colleur,semainemin)
	return render(request,"colleur/agenda.html",{'colles':colles,'groupes':groupes,'media_url':MEDIA_URL,'jour':jour,'semaine':semaine,'latex':MATHJAX})

@user_passes_test(is_colleur, login_url='accueil')
def colleNote(request,id_colle):
	"""Récupère la colle dont l'id est id_colle puis redirige vers la page de notation des groupes sur la colle concernée"""
	colle=get_object_or_404(Colle,pk=id_colle,colleur=request.user.colleur)
	return noteGroupe(request,colle.groupe.pk,colle)

@user_passes_test(is_colleur, login_url='accueil')
def decompte(request):
	"""Renvoie la vue de la page du décompte des colles"""
	colleur=request.user.colleur
	matieres=colleur.matieres.all()
	classes=colleur.classes.all()
	listematieres=list()
	for matiere in matieres:
		listemois = Note.objects.filter(colleur=colleur,matiere=matiere).dates('date_colle','month').distinct()
		listeclasses=list()
		for classe in classes:
			nbcolles=list()
			for mois in listemois:
				finmois=date(mois.year + mois.month//12,mois.month%12+1,1)-timedelta(days=1)
				nbcolles.append(Note.objects.filter(colleur=colleur,matiere=matiere,classe=classe,date_colle__range=(mois,finmois)).aggregate(nb=Count('id',distinct=True)))
			total=Note.objects.filter(colleur=colleur,matiere=matiere,classe=classe).aggregate(nb=Count('id',distinct=True))
			listeclasses.append((classe,nbcolles,total))
		listematieres.append((matiere,listeclasses,listemois))
	return render(request,"colleur/decompte.html",{'listematieres':listematieres})

@user_passes_test(is_colleur, login_url='accueil')
def colloscopePdf(request,id_classe,id_semin,id_semax):
	"""Renvoie le fichier PDF du colloscope de la classe dont l'id est id_classe, entre les semaines d'id id_semin et id_semax"""
	classe=get_object_or_404(Classe,pk=id_classe)
	semin=get_object_or_404(Semaine,pk=id_semin)
	semax=get_object_or_404(Semaine,pk=id_semax)
	if classe not in request.user.colleur.classes.all():
		raise Http404
	return Pdf(classe,semin,semax)

@user_passes_test(is_colleur, login_url='accueil')
def eleves(request,id_classe):
	"""Renvoie la vue de la page de gestion des élèves"""
	classe = get_object_or_404(Classe,pk=id_classe)
	if not is_profprincipal(request.user,classe):
		return HttpResponseForbidden("Accès non autorisé")
	try:
		eleve = Eleve.objects.get(pk=request.session['eleve'])
	except Exception:
		eleve = None
	try:
		semin = Semaine.objects.get(pk=request.session['semin'])
		semax = Semaine.objects.get(pk=request.session['semax'])
	except Exception:
		try:
			semaines = list(Semaine.objects.all())
			semin,semax = semaines[0],semaines[-1]
		except Exception:
			semin=semax=None
	if request.method == 'POST':
		 if 'semaines' in request.POST:
		 	form2 = SemaineForm(request.POST)
		 	form = EleveForm(classe, initial = {"eleve":eleve})
		 	if form2.is_valid():
		 		request.session['semin'] = form2.cleaned_data['semin'].pk
		 		request.session['semax'] = form2.cleaned_data['semax'].pk
		 		return redirect('eleves_colleur',classe.pk)
		 elif 'eleveselect' in request.POST:
		 	form2 = SemaineForm(initial = {'semin':semin,'semax':semax})
		 	form = EleveForm(classe,request.POST) 
		 	if form.is_valid():
		 		request.session['eleve'] = form.cleaned_data['eleve'].pk
		 		return redirect('eleves_colleur',classe.pk)
	else:
		form = EleveForm(classe, initial = {"eleve":eleve})
		form2 = SemaineForm(initial = {'semin':semin,'semax':semax})
	if eleve and semin and semax:
		semaines = Note.objects.filter(eleve=eleve,semaine__lundi__range=(semin.lundi,semax.lundi)).values('semaine','semaine__numero').distinct().order_by('semaine__lundi')
		matieres = classe.matieres.all().order_by('nom')
		matierenote=[]
		for matiere in matieres:
			moyenne = Note.objects.filter(eleve=eleve,semaine__lundi__range=(semin.lundi,semax.lundi),matiere=matiere).exclude(note__gt=20).aggregate(moy=Avg('note'))
			if moyenne['moy']:
				rang=Note.objects.exclude(note__gt=20).filter(classe=classe,eleve__isnull=False,matiere=matiere,semaine__lundi__range=(semin.lundi,semax.lundi)).values('eleve').annotate(Avg('note')).filter(note__avg__gt=moyenne['moy']+0.001).count()+1
			else:
				rang=""
			notes = []
			for semaine in semaines:
				note = Note.objects.filter(eleve=eleve,matiere=matiere,semaine__pk=semaine['semaine']).select_related('colleur__user')
				notes.append(note)
			matierenote.append((matiere,moyenne,rang,notes))
	else:
		semaines = matierenote = None
	return render(request,'colleur/eleves.html',{'eleve':eleve,'semin':semin,'semax':semax,'form':form,'form2':form2,'matierenote':matierenote,'semaines':semaines})



