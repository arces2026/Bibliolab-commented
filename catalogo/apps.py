"""
apps.py — configurazione dell app catalogo.

Django usa questo file per registrare l app nel progetto.
AppConfig contiene metadati dell app: nome, etichetta, campo pk default...
"""

from django.apps import AppConfig  # classe base per la configurazione di un app


class CatalogoConfig(AppConfig):
    # default_auto_field: tipo di chiave primaria usata per i Model di questa app
    # quando non specificano esplicitamente un campo id.
    # BigAutoField = intero a 64 bit (evita overflow su grandi quantita di dati).
    default_auto_field = 'django.db.models.BigAutoField'

    # name: nome Python dell app — deve corrispondere al nome della cartella.
    name = 'catalogo'

    # verbose_name: nome leggibile mostrato nel pannello Admin.
    verbose_name = 'Catalogo BiblioLab'
