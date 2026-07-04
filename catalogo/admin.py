"""
admin.py — configurazione del pannello di amministrazione di BiblioLab.

Django genera automaticamente un interfaccia CRUD per ogni Model registrato qui.
ModelAdmin permette di personalizzare: colonne visibili, filtri, ricerca, form di modifica.
"""

from django.contrib import admin   # importa il modulo admin di Django
from .models import Autore, Categoria, Libro  # importa i nostri Model (. = stessa cartella)


# Il decoratore @admin.register(Model) registra la classe come configurazione Admin
# per quel Model. E equivalente a admin.site.register(Autore, AutoreAdmin).
@admin.register(Autore)
class AutoreAdmin(admin.ModelAdmin):
    """Configurazione dell interfaccia Admin per il Model Autore."""

    # list_display: colonne mostrate nella pagina lista degli autori.
    # Ogni stringa deve essere il nome di un campo del Model o un metodo callable.
    list_display = ('cognome', 'nome', 'data_nascita')

    # search_fields: campi in cui Django cerca quando si usa la barra di ricerca.
    # Django usa LIKE '%termine%' su tutti i campi specificati.
    search_fields = ('cognome', 'nome')

    # ordering: ordine default nella lista (sovrascrive il Meta.ordering del Model).
    ordering = ('cognome',)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Configurazione Admin per il Model Categoria."""

    list_display  = ('nome',)        # mostra solo il nome nella lista
    search_fields = ('nome',)        # ricerca per nome


@admin.register(Libro)
class LibroAdmin(admin.ModelAdmin):
    """Configurazione Admin per il Model Libro — la piu ricca."""

    # Colonne nella lista: titolo, autore (usa __str__ di Autore), anno, disponibile, data.
    list_display = ('titolo', 'autore', 'anno_pubblicazione', 'disponibile', 'data_aggiunta')

    # list_filter: aggiunge un pannello filtri laterale con checkbox.
    # Django crea automaticamente i valori unici per ogni campo specificato.
    list_filter = ('disponibile', 'categorie', 'anno_pubblicazione')

    # search_fields con traversata di relazioni: autore__cognome cerca nel campo
    # cognome del Model Autore collegato tramite la ForeignKey autore.
    search_fields = ('titolo', 'autore__cognome', 'isbn')

    # list_editable: campi modificabili DIRETTAMENTE nella lista senza aprire il record.
    # Attenzione: il campo deve essere anche in list_display.
    list_editable = ('disponibile',)

    # date_hierarchy: aggiunge una barra di navigazione temporale sopra la lista.
    # Permette di filtrare per anno, mese, giorno.
    date_hierarchy = 'data_aggiunta'

    # filter_horizontal: widget a doppio pannello per ManyToMany.
    # Molto piu comodo del select multiplo standard per gestire le categorie.
    filter_horizontal = ('categorie',)

    # fieldsets: raggruppa i campi del form di modifica in sezioni con titolo.
    # Ogni sezione e una tupla (titolo, opzioni).
    fieldsets = (
        # Prima sezione: dati principali del libro (sempre visibile).
        ('Informazioni principali', {
            'fields': ('titolo', 'autore', 'anno_pubblicazione', 'isbn')
        }),
        # Seconda sezione: dettagli aggiuntivi (collassabile grazie a 'collapse').
        ('Dettagli', {
            'fields': ('categorie', 'descrizione', 'disponibile'),
            'classes': ('collapse',),  # sezione inizialmente chiusa, espandibile con click
        }),
    )
