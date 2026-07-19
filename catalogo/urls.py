"""
urls.py (app catalogo) — rubrica degli URL dell app BiblioLab.

Ogni path() associa un URL a una View.
Il parametro name permette di riferirsi all URL per nome nel codice e nei template
(reverse('catalogo:lista_libri') o {% url 'catalogo:lista_libri' %})
invece di scrivere l URL direttamente — se l URL cambia, basta aggiornarlo qui.
"""

from django.urls import (
    path,
    include,
)  # path() crea pattern URL; include() delega ad altri urls.py
from . import views  # importa le View HTML (views.py nella stessa cartella)
from . import api_views  # importa le View API REST (api_views.py)
from rest_framework.routers import (
    DefaultRouter,
)  # Router DRF per generare URL automaticamente

# app_name definisce il namespace dell app.
# Permette nomi univoci anche se due app usano lo stesso nome:
# 'catalogo:lista_libri' vs 'altra_app:lista_libri' non vanno mai in conflitto.
app_name = "catalogo"

urlpatterns = [
    # ── LIBRI (HTML) ──────────────────────────────────────────────────────────
    # Radice del sito: lista di tutti i libri.
    # '' corrisponde a / (nessun prefisso aggiuntivo dopo quello in urls.py principale).
    path("", views.LibroListView.as_view(), name="lista_libri"),
    # .as_view() converte la classe CBV in una funzione callable richiesta da path().
    # ListView, DetailView ecc. sono classi, non funzioni — .as_view() crea la funzione.
    # /libri/<pk>/ — dettaglio di un singolo libro.
    # <int:pk> cattura un intero positivo dall URL e lo passa come argomento pk alla View.
    path("libri/<int:pk>/", views.LibroDetailView.as_view(), name="dettaglio_libro"),
    # /libri/nuovo/ — form per creare un nuovo libro (solo utenti loggati).
    # FBV: non serve .as_view() — views.crea_libro e gia una funzione.
    path("libri/nuovo/", views.crea_libro, name="crea_libro"),
    # /libri/42/modifica/ — form per modificare il libro con pk=42.
    path("libri/<int:pk>/modifica/", views.modifica_libro, name="modifica_libro"),
    # /libri/42/elimina/ — pagina di conferma cancellazione.
    path(
        "libri/<int:pk>/elimina/", views.LibroDeleteView.as_view(), name="elimina_libro"
    ),
    # ── AUTORI ────────────────────────────────────────────────────────────────
    path("autori/", views.lista_autori, name="lista_autori"),
    path("autori/<int:pk>/", views.dettaglio_autore, name="dettaglio_autore"),
    # ── CATEGORIE ─────────────────────────────────────────────────────────────
    path("categorie/<int:pk>/", views.libri_per_categoria, name="libri_per_categoria"),
    # ── AUTENTICAZIONE ────────────────────────────────────────────────────────
    # /registrazione/ — form di registrazione nuovo utente.
    path("registrazione/", views.registrazione, name="registrazione"),
    # ── API REST (versione manuale con JsonResponse) ───────────────────────────
    # Questi endpoint restituiscono JSON invece di HTML.
    path("api/libri/", api_views.api_libri, name="api_libri"),
    path(
        "api/libri/<int:pk>/", api_views.api_libro_dettaglio, name="api_libro_dettaglio"
    ),
    # ── API REST v1 (con DRF APIView) ──────────────────────────────────────────
    path("api/v1/libri/", api_views.LibroListAPIView.as_view(), name="api_v1_libri"),
    path(
        "api/v1/libri/<int:pk>/",
        api_views.LibroDetailAPIView.as_view(),
        name="api_v1_libro_dettaglio",
    ),
    path('api/v1/autori/', api_views.AutoreListApiView.as_view(), name='api_v1_autori'),
    path('api/v1/autori/<int:pk>', api_views.AutoreListApiView.as_view(), name='api_v1_autori_dettaglio'),
    path('api/v1/categorie/', api_views.CategoriaListApiView.as_view(), name='api_v1_categorie'),
    path('api/v1/categorie/<int:pk>', api_views.CategoriaListApiView.as_view(), name='api_v1_categorie_dettaglio'),
]

# ── API REST v2 (con Django REST Framework e Router) ──────────────────────────

# DefaultRouter genera automaticamente tutti gli URL CRUD per ogni ViewSet registrato:
# GET  /api/v2/libri/         → lista
# POST /api/v2/libri/         → crea
# GET  /api/v2/libri/{id}/    → dettaglio
# PUT  /api/v2/libri/{id}/    → aggiorna tutto
# PATCH /api/v2/libri/{id}/   → aggiorna parziale
# DELETE /api/v2/libri/{id}/  → elimina
router = DefaultRouter()

# router.register() collega un ViewSet a un prefisso URL.
# basename e usato per generare i nomi degli URL (basename-list, basename-detail...).
router.register("libri", api_views.LibroViewSet, basename="libro-v2")

# include(router.urls) aggiunge tutti gli URL generati dal Router.
# Il prefisso 'api/v2/' e aggiunto prima di tutti gli URL del router.
urlpatterns += [
    path("api/v2/", include(router.urls)),
]
