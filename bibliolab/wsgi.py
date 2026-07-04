"""
wsgi.py — punto di ingresso WSGI per il deployment in produzione.

WSGI (Web Server Gateway Interface) e lo standard Python che definisce
come un server web (es. Gunicorn) comunica con un applicazione Python.
Django espone una funzione 'application' che Gunicorn chiama per ogni richiesta.

Gunicorn la usa cosi:
    gunicorn bibliolab.wsgi:application --bind 0.0.0.0:8000
"""

import os  # per impostare la variabile d ambiente DJANGO_SETTINGS_MODULE

from django.core.wsgi import get_wsgi_application  # costruisce l oggetto application WSGI

# Imposta quale file settings usare. In produzione si puo sovrascrivere
# questa variabile prima di avviare Gunicorn.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliolab.settings')

# get_wsgi_application() inizializza Django e restituisce la funzione callable
# che Gunicorn chiamera per ogni richiesta HTTP in arrivo.
application = get_wsgi_application()
