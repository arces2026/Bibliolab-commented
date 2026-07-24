"""
serializers.py — Serializer di Django REST Framework per BiblioLab.

Un Serializer in DRF e l equivalente di un Form/ModelForm per le API:
  - converte oggetti Python (istanze di Model) in dizionari Python -> JSON (serializzazione)
  - converte JSON in input -> dizionari -> oggetti Python con validazione (deserializzazione)
  - controlla quali campi includere nella risposta JSON
"""

from rest_framework import serializers  # base per tutti i Serializer DRF
from .models import Autore, Categoria, Libro  # i nostri Model


class AutoreSerializer(serializers.ModelSerializer):
    """
    Serializer per il Model Autore.
    ModelSerializer genera automaticamente i campi dal Model,
    come ModelForm fa per i Form.
    """
    libri_titles = serializers.StringRelatedField(many=True, source='libri')

    class Meta:
        model  = Autore  # Model di riferimento
        # fields: lista dei campi da includere nella rappresentazione JSON.
        # 'id' e il pk generato automaticamente da Django.
        fields = ['id', 'nome', 'cognome', 'data_nascita', 'biografia', 'libri_titles']


class CategoriaSerializer(serializers.ModelSerializer):
    """Serializer minimale per le categorie (usato come campo annidato in LibroSerializer)."""

    class Meta:
        model  = Categoria
        fields = ['id', 'nome']  # solo id e nome — la descrizione non serve nelle liste


class LibroSerializer(serializers.ModelSerializer):
    """
    Serializer per il Model Libro.
    Include campi annidati (categorie come oggetti) e campi calcolati (autore_nome).
    """

    # SerializerMethodField: campo calcolato che non corrisponde direttamente a un campo del Model.
    # Il valore viene calcolato dal metodo get_autore_nome (convenzione: get_<nome_campo>).
    autore_nome = serializers.SerializerMethodField()

    # Campo annidato: invece di restituire solo l id dell autore, restituisce l oggetto completo.
    # many=False (default): un solo autore per libro (ForeignKey).
    # read_only=True: questo campo viene usato solo in output (GET), non in input (POST/PUT).
    autore_oggetto = AutoreSerializer(source='autore', read_only=True)

    # Campo annidato per ManyToMany:
    # many=True: una lista di categorie per ogni libro.
    # read_only=True: gestire le categorie in POST/PATCH richiederebbe logica extra.
    categorie = CategoriaSerializer(many=True, read_only=True)

    class Meta:
        model  = Libro
        fields = [
            'id', 'titolo',
            'autore',         # id dell autore (scrivibile per POST/PATCH)
            'autore_nome',    # stringa calcolata "Eco, Umberto" (read-only)
            'autore_oggetto', # oggetto autore annidato (read-only)
            'categorie',      # lista di oggetti categoria (read-only)
            'anno_pubblicazione', 'isbn', 'disponibile', 'data_aggiunta', 'cover_url',
            'descrizione',
        ]
        # read_only_fields: campi che non possono essere impostati dall utente tramite API.
        # data_aggiunta e auto_now_add — non ha senso permettere di modificarlo.
        read_only_fields = ['data_aggiunta']

    def get_autore_nome(self, obj):
        """
        Calcola il valore del campo autore_nome.
        obj e l istanza del Model Libro corrente.
        str(obj.autore) chiama __str__ di Autore, che restituisce "Cognome, Nome".
        """
        return str(obj.autore)  # es: "Eco, Umberto"
