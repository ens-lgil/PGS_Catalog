"""
Django settings for pgs_web project.

Generated by 'django-admin startproject' using Django 3.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""


import os


if not os.getenv('GAE_APPLICATION', None):
    app_settings = os.path.join('./', 'app.yaml')
    if os.path.exists(app_settings):
        import yaml
        with open(app_settings) as secrets_file:
            secrets = yaml.load(secrets_file, Loader=yaml.FullLoader)
            for keyword in secrets['env_variables']:
                os.environ[keyword] = secrets['env_variables'][keyword]
    elif not os.environ['SECRET_KEY']:
        print("Error: missing secret key")
        exit(1)

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# Seehttps://docs.djangoproject.com/en/3.0//howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if os.environ['DEBUG'] == 'True':
    DEBUG = True

#ALLOWED_HOSTS = []
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

# Application definition

INSTALLED_APPS = [
	'catalog.apps.CatalogConfig',
    'rest_api.apps.RestApiConfig',
    #'release.apps.ReleaseConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_tables2',
    'django_extensions',
    'compressor',
    'rest_framework',
    'debug_toolbar' # Debug SQL queries
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware', # Debug SQL queries
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Debug SQL queries
INTERNAL_IPS = [
    '127.0.0.1',
]

ROOT_URLCONF = 'pgs_web.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalog.context_processors.pgs_urls',
                'catalog.context_processors.pgs_settings'
            ],
        },
    },
]

if DEBUG == False:
    TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR, 'templates')]
    TEMPLATES[0]['APP_DIRS'] = False
    TEMPLATES[0]['OPTIONS']['loaders'] = [
                                ('django.template.loaders.cached.Loader', [
                                 'django.template.loaders.filesystem.Loader',
                                 'django.template.loaders.app_directories.Loader'
                                ])
                            ]


USEFUL_URLS = {
    'BAKER_URL'         : 'https://baker.edu.au',
    'EBI_URL'           : 'https://www.ebi.ac.uk',
    'HDR_UK_CAM_URL'    : 'https://www.hdruk.ac.uk/about/structure/hdr-uk-cambridge/',
    'PGS_CONTACT'       : 'pgs-info@ebi.ac.uk',
    'PGS_FTP_ROOT'      : 'ftp://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_FTP_HTTP_ROOT' : 'http://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_TWITTER_URL'   : 'https://www.twitter.com/pgscatalog',
    'UOC_URL'           : 'https://www.phpc.cam.ac.uk/',
    'TEMPLATEGoogleDoc_URL' : 'https://docs.google.com/spreadsheets/d/1CGZUhxRraztW4k7p_6blfBmFndYTcmghn3iNnzJu1_0/edit?usp=sharing',
    'CATALOG_PUBLICATION_URL' : 'https://doi.org/10.1101/2020.05.20.20108217',
}
if os.getenv('GAE_APPLICATION', None):
    PGS_ON_GAE = 1
else:
    PGS_ON_GAE = 0

WSGI_APPLICATION = 'pgs_web.wsgi.application'

# Database
#https://docs.djangoproject.com/en/3.0//ref/settings/#databases

if os.getenv('GAE_APPLICATION', None):
    # Running on production App Engine, so connect to Google Cloud SQL using
    # the unix socket at /cloudsql/<your-cloudsql-connection string>
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': os.environ['DATABASE_HOST'],
            'PORT': os.environ['DATABASE_PORT']
        }
    }
else:
    # Running locally so connect to either a local MySQL instance or connect
    # to Cloud SQL via the proxy.  To start the proxy via command line:
    #    $ cloud_sql_proxy -instances=pgs-catalog:europe-west1:pgs-db-server-1=tcp:3306
    # See https://cloud.google.com/sql/docs/mysql-connect-proxy
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': os.environ['DATABASE_HOST'],
            'PORT': os.environ['DATABASE_PORT']
        }
    }


# Password validation
#https://docs.djangoproject.com/en/3.0//ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
#https://docs.djangoproject.com/en/3.0//topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
#https://docs.djangoproject.com/en/3.0//howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_FINDERS = [
	'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder'
]
if not os.getenv('GAE_APPLICATION', None):
    STATICFILES_FINDERS.append('compressor.finders.CompressorFinder')


COMPRESS_PRECOMPILERS = ''
COMPRESS_ROOT = os.path.join(BASE_DIR, "static/")

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)


#---------------------#
#  REST API Settings  #
#---------------------#

#REST_SAFELIST_IPS = [
#    '127.0.0.1'
#]
REST_BLACKLIST_IPS = [
    #'127.0.0.1'
]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_api.rest_permissions.BlacklistPermission', # see REST_BLACKLIST_IPS
        #'rest_api.rest_permissions.SafelistPermission', # see REST_SAFELIST_IPS
        #'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 50,
    'EXCEPTION_HANDLER': 'rest_api.views.custom_exception_handler',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES' : {
        'anon': '100/min',
        'user': '100/min'
    }
}
