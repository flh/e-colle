# -*- coding:utf8 -*-
# Django settings for e-colle project.

#---------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------ INFORMATIONS À REMPLIR----------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

DEFAULT_ADMIN_PASSWD = 'admin' # le mot de passe à la création de l'admin

DEFAULT_SECRETARIAT_PASSWD = 'secret' # le mot de passe à la création du compte secrétariat

EMAIL_ADMIN = '' # l'email de l'admin. Si vous ne voulez pas en mettre, laissez vide

EMAIL_SECRETARIAT = '' # l'email du secrétariat. Si vous ne voulez pas en mettre, laissez vide

IP_FILTRE_ADMIN = True # True si on veut restreindre la partie admin à certaines adresse IP (typiquement des adresse locales), False sinon

IP_FILTRE_ADRESSES = ('^127\.0\.0\.1$',) # la liste des adresses autorisées pour la partie admin si IP_FILTRE_ADMIN vaut True, à renseigner avec des REGEXP.

IMAGEMAGICK= True # True pour faire des images miniatures des pièces jointes de programmes de colle. False sinon.

ADMINS = ( # les couples nom/email du (des) administrateur(s) du site
     ('admin', 'admin@example.com'),
)

ALLOWED_HOSTS = [] # les nom de domaine autorisés pour accéder à e-colle, démarrer par un '.' pour les sous-domaines (par exemple '.e-colle.fr')

SECRET_KEY = 'cg(ip)m3z77z3v!5wo&cl8^4!rk9t0++5wld+@i(kifb!z-k0p' # une clé secrète de 50 caractères. À modifier à la configuration

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # le SGBD choisi: 'django.db.backends.mysql' si vous utilisez mysql, 'django.db.backends.postgresql' pour postgreSQL, etc ... 
        'NAME': 'e-colle',               # le nom de la base de données (le chemin vers le fichier + le nom du fichier.db pour sqlite)
        # La suite est à laisser vide si vous utilisez SQlite, puisqu'aucune authentification n'y est nécessaire
        'USER': 'e-colle',               # le nom de l'utilisateur ayant droits sur la base de données.
        'PASSWORD':'',       # le mot de passe de l'utilisateur
        'HOST': 'localhost',                  # l'adresse IP de la base de données. Mettre 'localhost' si elle se trouve directement sur le serveur de e-colle 
        'PORT': '',                           # vide par défaut. À renseigner si la BDD se trouve sur un port particulier.
    }
}


#---------------------------------------------------------------------------------------------------------------------------------------------------------------
#------------------------------------------------------------ FIN INFORMATIONS À REMPLIR------------------------------------------------------------------------
#---------------------------------------------------------------------------------------------------------------------------------------------------------------

from os import path

CHEMINVERSECOLLE = path.dirname(path.dirname(__file__))

BDD=DATABASES['default']['ENGINE'].split(".")[-1] # on récupère le nom du SGBD: mysql ou sqlite3 ou postgresql ou oracle.

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            path.join(CHEMINVERSECOLLE,'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


MEDIA_ROOT = path.join(CHEMINVERSECOLLE,'media')

RESOURCES_ROOT = path.join(CHEMINVERSECOLLE,'resources')

STATICFILES_DIRS = (
    path.join(CHEMINVERSECOLLE,'public'),
)


MEDIA_URL = '/media/'

STATIC_URL = '/static/'

DEBUG = False

APPEND_SLASH = False

MANAGERS = ADMINS

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accueil',
    'administrateur',
    'eleve',
    'colleur',
    'secretariat',
    'customfilter',
    'devoirs',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ecolle.urls'

WSGI_APPLICATION = 'ecolle.wsgi.application'

LANGUAGE_CODE = 'fr_FR'

USE_I18N = True

USE_TZ = True

AUTH_USER_MODEL = "accueil.User"
