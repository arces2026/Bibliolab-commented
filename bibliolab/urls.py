"""
urls.py (progetto) — rubrica principale degli URL di BiblioLab.

Ogni richiesta HTTP arriva qui. Django confronta l URL con i pattern
in ordine e delega alla funzione o all app corrispondente.
"""

from django.contrib import admin          # View e URL del pannello admin
from django.urls import path, include     # path() crea un pattern URL; include() delega a un altro urls.py
from django.conf import settings          # accesso alle impostazioni (DEBUG, MEDIA_ROOT...)
from django.conf.urls.static import static # aggiunge URL per i file media in sviluppo

urlpatterns = [
    # /admin/ → pannello di amministrazione automatico di Django.
    # admin.site.urls e un insieme di URL pattern gia pronti, non una singola View.
    path('admin/', admin.site.urls),

    # /accounts/ → URL di autenticazione integrati di Django.
    # include('django.contrib.auth.urls') aggiunge automaticamente:
    # /accounts/login/, /accounts/logout/, /accounts/password_change/, /accounts/password_reset/...
    path('accounts/', include('django.contrib.auth.urls')),

    # / (radice) → delega TUTTI gli altri URL al file catalogo/urls.py.
    # include('catalogo.urls') carica dinamicamente i pattern dell app.
    # Il prefisso '' significa che gli URL dell app iniziano dalla radice del sito.
    path('', include('catalogo.urls')),
]

# In sviluppo (DEBUG=True), Django serve i file media caricati dagli utenti.
# In produzione i file media vengono serviti da nginx o da uno storage esterno (S3).
# static() aggiunge un pattern URL come /media/foto.jpg → MEDIA_ROOT/foto.jpg.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
