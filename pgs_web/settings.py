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
    import yaml
    with open(os.path.join('./', 'app.yaml')) as secrets_file:
        secrets = yaml.load(secrets_file, Loader=yaml.FullLoader)
        for keyword in secrets['env_variables']:
            os.environ[keyword] = secrets['env_variables'][keyword]


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

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
    'release.apps.ReleaseConfig',
    'search.apps.SearchConfig',
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
    'django_elasticsearch_dsl',
    'django_elasticsearch_dsl_drf',
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

if os.getenv('GAE_APPLICATION', None) and DEBUG==False:
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [os.path.join(BASE_DIR, 'templates')],
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                    'django.contrib.auth.context_processors.auth',
                    'django.contrib.messages.context_processors.messages',
                    'catalog.context_processors.pgs_urls',
                    'catalog.context_processors.pgs_settings'
                ],
                'loaders': [
                    ('django.template.loaders.cached.Loader', [
                        'django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader'
                    ])
                ]
            },
        },
    ]
else:
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


USEFUL_URLS = {
    'BAKER_URL'         : 'https://baker.edu.au',
    'EBI_URL'           : 'https://www.ebi.ac.uk',
    'HDR_UK_CAM_URL'    : 'https://www.hdruk.ac.uk/about/structure/hdr-uk-cambridge/',
    'PGS_CONTACT'       : 'pgs-info@ebi.ac.uk',
    'PGS_FTP_ROOT'      : 'ftp://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_FTP_HTTP_ROOT' : 'http://ftp.ebi.ac.uk/pub/databases/spot/pgs',
    'PGS_TWITTER_URL'   : 'https://www.twitter.com/pgscatalog',
    'UOC_URL'           : 'https://www.phpc.cam.ac.uk/',
    'TEMPLATEGoogleDoc_URL' : 'https://docs.google.com/spreadsheets/d/1CGZUhxRraztW4k7p_6blfBmFndYTcmghn3iNnzJu1_0/edit?usp=sharing'
}
if os.getenv('GAE_APPLICATION', None):
    PGS_ON_GAE = 1
else:
    PGS_ON_GAE = 0

WSGI_APPLICATION = 'pgs_web.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# [START db_setup]
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
            'PORT': 5432
        }
    }
else:
    # Running locally so connect to either a local PostgreSQL instance or connect
    # to Cloud SQL via the proxy.  To start the proxy via command line:
    # $ cloud_sql_proxy -instances=pgs-catalog:europe-west2:pgs-*******=tcp:5430
    # See https://cloud.google.com/sql/docs/postgres/connect-admin-proxy
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DATABASE_NAME'],
            'USER': os.environ['DATABASE_USER'],
            'PASSWORD': os.environ['DATABASE_PASSWORD'],
            'HOST': 'localhost',
            'PORT': 5432
        }
    }
# [END db_setup]

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

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


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'ORDERING_PARAM': 'ordering',
}

# Elasticsearch configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'http://localhost:9200'
    },
}

# Name of the Elasticsearch index
ELASTICSEARCH_INDEX_NAMES = {
    'search.documents.score': 'score',
    'search.documents.efo_trait': 'efo_trait',
    'search.documents.publication': 'publication',
    #'search.documents.publisher': 'publisher',
}
