"""
forms.py — definizione dei Form di BiblioLab.

I Form Django automatizzano:
  - il rendering HTML dei campi con widget appropriati
  - la validazione dei dati inviati dall utente
  - la restituzione di messaggi di errore precisi per ogni campo
  - il salvataggio nel database (ModelForm)

Questo file contiene due Form:
  1. LibroForm — per creare e modificare libri (ModelForm)
  2. RegistrazioneForm — per registrare nuovi utenti (estende UserCreationForm)
"""

from django import forms                               # base per tutti i Form Django
from django.contrib.auth.forms import UserCreationForm # form di registrazione built-in di Django
from django.contrib.auth.models import User            # Model utente built-in di Django
from .models import Libro                              # il nostro Model Libro


# ── HELPER PER I WIDGET ───────────────────────────────────────────────────────
# I widget determinano quale elemento HTML viene generato per ogni campo.
# Questi helper evitano di ripetere attrs={'class': 'form-control'} ovunque.

def w_text(placeholder=''):
    """Widget TextInput con classe Bootstrap form-control."""
    return forms.TextInput(attrs={'class': 'form-control', 'placeholder': placeholder})

def w_number(**extra):
    """Widget NumberInput con classe Bootstrap form-control."""
    return forms.NumberInput(attrs={'class': 'form-control', **extra})

def w_textarea(rows=4):
    """Widget Textarea con classe Bootstrap form-control."""
    return forms.Textarea(attrs={'class': 'form-control', 'rows': rows})

def w_email():
    """Widget EmailInput con classe Bootstrap form-control."""
    return forms.EmailInput(attrs={'class': 'form-control'})

# Select (menu a tendina) con classe Bootstrap form-select.
W_SELECT = forms.Select(attrs={'class': 'form-select'})


class LibroForm(forms.ModelForm):
    """
    Form per creare e modificare un Libro.
    ModelForm genera automaticamente i campi dal Model Libro,
    poi personalizziamo widget, label e help_text nella classe Meta.
    """

    class Meta:
        # model: il Model da cui generare i campi.
        model = Libro

        # fields: lista dei campi da includere nel form.
        # L ordine qui e l ordine in cui appariranno nel template.
        # 'data_aggiunta' e escluso perche e auto_now_add (non modificabile).
        fields = [
            'titolo', 'autore', 'categorie',
            'anno_pubblicazione', 'isbn', 'descrizione', 'disponibile'
        ]

        # widgets: sovrascrive il widget default di Django per ogni campo.
        # Senza questa sezione Django userebbe widget senza classi CSS Bootstrap.
        widgets = {
            'titolo':             w_text(),                # <input type="text" class="form-control">
            'autore':             W_SELECT,                # <select class="form-select">
            'categorie':          forms.CheckboxSelectMultiple(),  # checkbox invece di select multiplo
            'anno_pubblicazione': w_number(min=1000, max=2099),    # input numerico con limiti HTML
            'isbn':               w_text('978...'),        # con placeholder suggerito
            'descrizione':        w_textarea(),            # area di testo multiriga
            # 'disponibile' usa il default CheckboxInput — va bene cosi
        }

        # labels: sovrascrive le etichette dei campi (default = nome campo capitalizzato).
        labels = {
            'anno_pubblicazione': 'Anno di pubblicazione',
            'disponibile':        'Disponibile per il prestito',
        }

        # help_texts: testo di aiuto mostrato sotto il campo nel form.
        help_texts = {
            'isbn': 'Codice ISBN a 13 cifre (opzionale)',
        }

    def clean_isbn(self):
        """
        Validazione personalizzata per il campo isbn.
        Questo metodo viene chiamato automaticamente da Django durante is_valid().
        Controlla che l ISBN non sia gia usato da un altro libro nel database.
        """
        # self.cleaned_data contiene i dati gia validati dai controlli base del campo.
        # .get() con default '' evita KeyError se il campo non e presente.
        isbn = self.cleaned_data.get('isbn', '')

        # Se l ISBN e vuoto (campo opzionale) non serve fare ulteriori controlli.
        if not isbn:
            return isbn  # restituiamo il valore pulito (stringa vuota)

        # Cerca libri con questo ISBN nel database.
        qs = Libro.objects.filter(isbn=isbn)

        # Se stiamo MODIFICANDO un libro esistente (self.instance.pk esiste),
        # dobbiamo escludere il libro stesso dalla ricerca di duplicati.
        # Senza questa esclusione, la modifica fallirebbe sempre perche
        # l ISBN corrente verrebbe trovato come "duplicato".
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        # Se esiste un altro libro con lo stesso ISBN, rifiutiamo il form.
        if qs.exists():
            # ValidationError interrompe la validazione e aggiunge l errore al campo.
            raise forms.ValidationError(
                f"Il libro con ISBN {isbn} e gia presente nel catalogo."
            )

        # Se tutto e ok, DOBBIAMO restituire il valore pulito — Django lo usa per cleaned_data.
        return isbn


class RegistrazioneForm(UserCreationForm):
    """
    Form di registrazione per nuovi utenti.
    Estende UserCreationForm (gia include username, password1, password2 con validazione)
    aggiungendo email obbligatoria e nome/cognome opzionali.
    """

    # Aggiungiamo email come campo obbligatorio (UserCreationForm non la include).
    email = forms.EmailField(
        required=True,           # obbligatorio
        label='Email',
        widget=w_email()
    )

    # Campi opzionali per nome e cognome.
    first_name = forms.CharField(
        max_length=100,
        required=False,          # opzionale
        label='Nome',
        widget=w_text()
    )

    last_name = forms.CharField(
        max_length=100,
        required=False,
        label='Cognome',
        widget=w_text()
    )

    class Meta(UserCreationForm.Meta):
        # Ereditiamo Meta da UserCreationForm (che imposta model=User)
        # e aggiungiamo i campi extra all ordine.
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        """Verifica che l email non sia gia registrata da un altro utente."""
        email = self.cleaned_data.get('email')

        # filter().exists() e piu efficiente di filter().count() > 0:
        # si ferma al primo record trovato invece di contarli tutti.
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Questa email e gia registrata.')

        return email  # restituire sempre il valore pulito

    def save(self, commit=True):
        """
        Sovrascrive save() per salvare anche i campi aggiuntivi (email, nome, cognome).
        UserCreationForm.save() salva solo username e password.
        commit=False crea l oggetto in memoria senza salvarlo nel DB,
        utile se vogliamo fare altre operazioni prima del salvataggio definitivo.
        """
        # Chiama il save() del genitore con commit=False: crea l oggetto User
        # con username e password (hashata) ma NON lo salva ancora nel database.
        user = super().save(commit=False)

        # Impostiamo manualmente i campi aggiuntivi sull oggetto User in memoria.
        user.email      = self.cleaned_data['email']
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')

        # Se commit=True (default), salviamo nel database.
        if commit:
            user.save()

        return user  # restituiamo l oggetto User (salvato o no)
