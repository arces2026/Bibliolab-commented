"""
models.py — definizione dei Model del catalogo di BiblioLab.

Un Model e una classe Python che corrisponde a una tabella del database.
Ogni attributo della classe e un campo (colonna) della tabella.
Django usa questi Model per:
  - creare le tabelle nel database (tramite migrations)
  - fornire la QuerySet API per leggere e scrivere dati
  - generare il pannello Admin automaticamente
"""

from django.db import models  # importa la base per tutti i Model e i tipi di campo


class Autore(models.Model):
    """
    Rappresenta un autore di libri nel catalogo.
    Tabella SQL generata: catalogo_autore
    """

    # CharField: colonna VARCHAR nel database. max_length e obbligatorio.
    # verbose_name e l etichetta mostrata nell Admin e nei form.
    nome = models.CharField(
        max_length=100,         # massimo 100 caratteri
        verbose_name='Nome'     # etichetta leggibile per Admin e form
    )

    # Un secondo CharField per il cognome — separato per poter ordinare per cognome.
    cognome = models.CharField(
        max_length=100,
        verbose_name='Cognome'
    )

    # DateField: colonna DATE nel database (solo anno-mese-giorno, senza ora).
    # null=True: il database puo contenere NULL (assenza di valore).
    # blank=True: il campo puo essere lasciato vuoto nei form (validazione Django).
    # Per DateField opzionale servono ENTRAMBI: null per il DB, blank per i form.
    data_nascita = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data di nascita'
    )

    # TextField: colonna TEXT nel database, senza limite di lunghezza.
    # blank=True (senza null=True): per i campi testo Django usa stringa vuota '' invece di NULL.
    biografia = models.TextField(
        blank=True,
        verbose_name='Biografia'
    )

    def __str__(self):
        # __str__ definisce come l oggetto viene rappresentato come stringa.
        # Usato dall Admin, dalla shell Django e ovunque si stampi un Autore.
        # f-string: restituisce es. "Eco, Umberto"
        return f"{self.cognome}, {self.nome}"

    class Meta:
        # Meta contiene configurazioni del Model che non sono campi del database.

        # ordering: ordine default di tutte le query su questo Model.
        # ['cognome', 'nome'] = ordine alfabetico per cognome, poi per nome a pari cognome.
        ordering = ['cognome', 'nome']

        # verbose_name e verbose_name_plural: nomi mostrati nell Admin.
        # Senza questi Django genererebbe 'Autores' (plurale inglese).
        verbose_name        = 'Autore'
        verbose_name_plural = 'Autori'


class Categoria(models.Model):
    """
    Rappresenta una categoria (genere letterario) per classificare i libri.
    Tabella SQL generata: catalogo_categoria
    """

    # unique=True: vincolo di unicita — non possono esistere due categorie con lo stesso nome.
    # Genera automaticamente un indice UNIQUE nel database.
    nome = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Nome'
    )

    descrizione = models.TextField(
        blank=True,
        verbose_name='Descrizione'
    )

    def __str__(self):
        # Restituisce semplicemente il nome della categoria (es. "Romanzo").
        return self.nome

    class Meta:
        ordering            = ['nome']        # ordine alfabetico
        verbose_name        = 'Categoria'
        verbose_name_plural = 'Categorie'     # Django non sa fare il plurale italiano


class Libro(models.Model):
    """
    Rappresenta un libro nel catalogo di BiblioLab.
    E il Model centrale dell applicazione — collegato ad Autore e Categoria.
    Tabella SQL generata: catalogo_libro
    """

    # CharField per il titolo — obbligatorio (nessun null o blank).
    titolo = models.CharField(max_length=200, verbose_name='Titolo')

    # ForeignKey: relazione molti-a-uno con Autore.
    # Molti libri possono avere lo stesso autore; ogni libro ha un solo autore.
    # Django crea una colonna autore_id (intero) nella tabella catalogo_libro.
    autore = models.ForeignKey(
        'Autore',                       # Model di destinazione (stringa per evitare import circolari)
        on_delete=models.PROTECT,       # impedisce di cancellare un autore che ha libri collegati
        related_name='libri',           # nome per la navigazione inversa: autore.libri.all()
        verbose_name='Autore'
    )

    # ManyToManyField: relazione molti-a-molti con Categoria.
    # Un libro puo avere piu categorie; una categoria puo contenere piu libri.
    # Django crea automaticamente una tabella intermedia catalogo_libro_categorie.
    # blank=True: un libro puo non avere categorie (la relazione e opzionale).
    categorie = models.ManyToManyField(
        'Categoria',
        blank=True,                     # opzionale: un libro puo non avere categorie
        related_name='libri',           # navigazione inversa: categoria.libri.all()
        verbose_name='Categorie'
    )

    # IntegerField: colonna INTEGER nel database. Obbligatorio (no null, no blank).
    anno_pubblicazione = models.IntegerField(verbose_name='Anno di pubblicazione')

    # CharField per ISBN con unique=True: ogni ISBN e univoco nel catalogo.
    # blank=True: l ISBN e opzionale (alcuni libri non ce l hanno).
    isbn = models.CharField(
        max_length=13,
        unique=False,
        blank=True,
        verbose_name='ISBN',
        help_text='Codice ISBN a 13 cifre (opzionale)'  # testo di aiuto nel form
    )

    # TextField per la descrizione — lunga e opzionale.
    descrizione = models.TextField(blank=True, verbose_name='Descrizione')

    # BooleanField: colonna BOOLEAN nel database (True/False).
    # default=True: i nuovi libri sono disponibili per default.
    disponibile = models.BooleanField(default=True, verbose_name='Disponibile')
    
    # Aggiungo field per le cover
    cover_url = models.URLField(max_length=300, default='immagini/libro_default.png')

    # DateTimeField con auto_now_add=True: viene impostato automaticamente
    # alla data e ora ATTUALI quando il record viene creato.
    # Non puo essere modificato dopo la creazione (read-only).
    data_aggiunta = models.DateTimeField(auto_now_add=True, verbose_name='Aggiunto il')

    def __str__(self):
        # Restituisce es. "Il nome della rosa (1980)".
        return f"{self.titolo} ({self.anno_pubblicazione})"

    class Meta:
        ordering            = ['titolo']      # ordine alfabetico per titolo
        verbose_name        = 'Libro'
        verbose_name_plural = 'Libri'
