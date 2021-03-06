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
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if os.environ['DEBUG'] == 'True':
    DEBUG = True

ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')


# Application definition

INSTALLED_APPS = [
	'catalog.apps.CatalogConfig',
    'rest_api.apps.RestApiConfig',
    'search.apps.SearchConfig',
    'release.apps.ReleaseConfig',
    'benchmark.apps.BenchmarkConfig',
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
    'debug_toolbar' # Debug SQL queries
]
#if os.environ['PGS_LIVE_SITE'] == False:
#    INSTALLED_APPS.append('release.apps.ReleaseConfig')

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
                    'catalog.context_processors.pgs_settings',
                    'catalog.context_processors.pgs_search_examples'
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
                    'catalog.context_processors.pgs_settings',
                    'catalog.context_processors.pgs_search_examples'
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
    'TEMPLATEGoogleDoc_URL' : 'https://docs.google.com/spreadsheets/d/1CGZUhxRraztW4k7p_6blfBmFndYTcmghn3iNnzJu1_0/edit?usp=sharing',
    'CurationGoogleDoc_URL' : 'https://drive.google.com/file/d/1iYoa0R3um7PtyfVO37itlGbK1emoZmD-/view',
    'CATALOG_PUBLICATION_URL' : 'https://doi.org/10.1101/2020.05.20.20108217'
}
if os.getenv('GAE_APPLICATION', None):
    PGS_ON_GAE = 1
else:
    PGS_ON_GAE = 0

PGS_ON_LIVE_SITE = os.environ['PGS_LIVE_SITE']

PGS_ON_CURATION_SITE = os.environ['PGS_CURATION_SITE']

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
            'PORT': os.environ['DATABASE_PORT']
        },
        'benchmark': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DATABASE_NAME_2'],
            'USER': os.environ['DATABASE_USER_2'],
            'PASSWORD': os.environ['DATABASE_PASSWORD_2'],
            'HOST': os.environ['DATABASE_HOST_2'],
            'PORT': os.environ['DATABASE_PORT_2']
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
            'PORT': os.environ['DATABASE_PORT']
        },
        'benchmark': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': os.environ['DATABASE_NAME_2'],
            'USER': os.environ['DATABASE_USER_2'],
            'PASSWORD': os.environ['DATABASE_PASSWORD_2'],
            'HOST': 'localhost',
            'PORT': os.environ['DATABASE_PORT_2']
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


FILE_UPLOAD_HANDLERS = [
    "django.core.files.uploadhandler.MemoryFileUploadHandler",
    "django.core.files.uploadhandler.TemporaryFileUploadHandler"
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(BASE_DIR, "static/")

STATICFILES_FINDERS = [
	'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder'
]
#if not os.getenv('GAE_APPLICATION', None):
#    STATICFILES_FINDERS.append('compressor.finders.CompressorFinder')

COMPRESS_PRECOMPILERS = ''
COMPRESS_ROOT = os.path.join(BASE_DIR, "static/")

COMPRESS_PRECOMPILERS = (
    ('text/x-scss', 'django_libsass.SassCompiler'),
)



#---------------------------------#
#  Google Cloud Storage Settings  #
#---------------------------------#

if os.getenv('GAE_APPLICATION'):
    from google.oauth2 import service_account
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        os.path.join(BASE_DIR, os.environ['GS_SERVICE_ACCOUNT_SETTINGS'])
    )
    DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
    GS_BUCKET_NAME = os.environ['GS_BUCKET_NAME']
    #GS_DEFAULT_ACL = 'publicRead'
    MEDIA_URL = 'https://storage.googleapis.com/'+os.environ['GS_BUCKET_NAME']+'/'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



#---------------------#
#  REST API Settings  #
#---------------------#

#REST_SAFELIST_IPS = [
#    '127.0.0.1'
#]
REST_BLACKLIST_IPS = [
    #'127.0.0.1'
]

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

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
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FileUploadParser'

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



#--------------------------#
#  Elasticsearch Settings  #
#--------------------------#

# Elasticsearch configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.environ['ELASTICSEARCH_URL_ROOT']
    }
}

# Name of the Elasticsearch index
ELASTICSEARCH_INDEX_NAMES = {
    'search.documents.efo_trait': 'efo_trait',
    'search.documents.publication': 'publication'
}
