"""
views.py — View HTML di BiblioLab.

Le View ricevono la richiesta HTTP, interrogano i Model e restituiscono
la risposta HTML generata dai Template.

Questo file usa sia CBV (Class-Based Views) per le operazioni CRUD standard,
sia FBV (Function-Based Views) per logica piu articolata come autori e registrazione.

Struttura:
  - LibroListView, LibroDetailView, LibroCreateView*, LibroUpdateView*, LibroDeleteView
  - lista_autori, dettaglio_autore (FBV)
  - libri_per_categoria (FBV)
  - crea_libro*, modifica_libro* (FBV con LibroForm — sostituiscono le CBV Create/Update)
  - registrazione (FBV)

  * = protetta con login obbligatorio
"""

from django.db import models as db_models   # per models.Count nelle annotazioni
from django.shortcuts import render, get_object_or_404, redirect  # scorciatoie comuni
from django.views.generic import ListView, DetailView              # CBV per lista e dettaglio
from django.views.generic.edit import DeleteView                   # CBV per cancellazione
from django.contrib.auth.mixins import LoginRequiredMixin          # Mixin: richiede login per CBV
from django.contrib.auth.decorators import login_required          # decoratore: richiede login per FBV
from django.contrib.auth import login as auth_login                # funzione per autenticare l utente
from django.contrib import messages                                # messaggi flash
from django.urls import reverse_lazy                               # calcola URL in modo lazy (per attributi di classe)

from .models import Libro, Autore, Categoria  # i nostri Model
from .forms import LibroForm, RegistrazioneForm  # i nostri Form


# ══════════════════════════════════════════════════════════════
# LIBRI
# ══════════════════════════════════════════════════════════════

class LibroListView(ListView):
    """
    Mostra la lista di tutti i libri con ricerca e paginazione.
    Eredita da ListView: gestisce automaticamente la QuerySet e il passaggio al Template.
    """

    # model: il Model da usare. ListView esegue Model.objects.all() di default.
    model = Libro

    # template_name: percorso del template da usare.
    # Il percorso e relativo alle cartelle templates/ configurate in settings.
    template_name = 'catalogo/libro_list.html'

    # context_object_name: nome della variabile nel template (default: 'object_list').
    # Con 'libri' possiamo scrivere {% for libro in libri %} invece di {% for libro in object_list %}.
    context_object_name = 'libri'

    # paginate_by: numero di oggetti per pagina. ListView gestisce la paginazione automaticamente.
    # Il parametro ?page=2 nell URL seleziona la pagina.
    paginate_by = 12

    def get_queryset(self):
        """
        Sovrascrive la QuerySet default (objects.all()) per aggiungere ricerca e filtri.
        Questo metodo viene chiamato da ListView prima di passare i dati al template.
        """
        # Partiamo dalla QuerySet base con ottimizzazioni:
        # select_related('autore'): recupera autore e libro in una sola JOIN SQL
        #   evitando il problema N+1 (una query per ogni autore di ogni libro).
        # prefetch_related('categorie'): per ManyToMany, fa due query ottimizzate
        #   invece di N query (una per le categorie di ogni libro).
        qs = Libro.objects.select_related('autore').prefetch_related('categorie')

        # Legge il parametro di ricerca dall URL: /libri/?cerca=eco
        # .GET e un dizionario dei parametri GET della richiesta.
        # .get('cerca', '') restituisce '' se il parametro non e presente.
        q = self.request.GET.get('cerca', '')
        if q:
            # Filtra per titolo O per cognome autore (operatore | = OR tra QuerySet).
            # __icontains = contiene la stringa, case-insensitive (i = insensitive).
            qs = qs.filter(titolo__icontains=q) | qs.filter(autore__cognome__icontains=q)

        # Filtro per categoria: /libri/?categoria=3
        cat_pk = self.request.GET.get('categoria', '')
        if cat_pk:
            # Traversata di relazione: Libro -> categorie -> pk
            qs = qs.filter(categorie__pk=cat_pk)

        # .distinct() rimuove duplicati che possono emergere dal filtraggio su M2M.
        return qs.order_by('titolo').distinct()

    def get_context_data(self, **kwargs):
        """
        Aggiunge variabili extra al contesto del template.
        ListView gia aggiunge 'libri', 'page_obj', 'paginator', 'is_paginated'.
        Qui aggiungiamo le variabili per i filtri.
        """
        # super() chiama get_context_data() di ListView per ottenere il contesto base.
        ctx = super().get_context_data(**kwargs)

        # Aggiungiamo il termine di ricerca per pre-riempire il campo di ricerca nel template.
        ctx['query'] = self.request.GET.get('cerca', '')

        # Aggiungiamo tutte le categorie per il menu a tendina di filtro.
        ctx['categorie'] = Categoria.objects.all()

        # Aggiungiamo la categoria attiva per evidenziarla nel menu.
        ctx['cat_attiva'] = self.request.GET.get('categoria', '')

        return ctx


class LibroDetailView(DetailView):
    """
    Mostra il dettaglio di un singolo libro.
    DetailView cerca automaticamente il libro per pk nell URL e restituisce 404 se non esiste.
    """

    model               = Libro
    template_name       = 'catalogo/libro_detail.html'
    context_object_name = 'libro'

    def get_context_data(self, **kwargs):
        """Aggiunge al contesto altri libri dello stesso autore (per la sidebar)."""
        ctx = super().get_context_data(**kwargs)

        # self.object e il libro corrente recuperato da DetailView.
        # Cerchiamo altri libri dello stesso autore, escludendo il libro corrente.
        # [:4] limita a 4 risultati (slicing Python sul QuerySet).
        ctx['altri_libri'] = (
            Libro.objects
            .filter(autore=self.object.autore)   # stesso autore
            .exclude(pk=self.object.pk)           # escludi il libro corrente
            .order_by('titolo')[:4]               # max 4, in ordine alfabetico
        )
        return ctx


class LibroDeleteView(LoginRequiredMixin, DeleteView):
    """
    Mostra una pagina di conferma e cancella il libro se confermato.
    LoginRequiredMixin: redirige al login se l utente non e autenticato (deve stare PRIMA di DeleteView).
    DeleteView gestisce GET (mostra conferma) e POST (esegue la cancellazione).
    """

    model         = Libro
    template_name = 'catalogo/libro_confirm_delete.html'

    # reverse_lazy calcola l URL al momento dell uso, non quando la classe viene definita.
    # Necessario perche quando Python carica la classe gli URL potrebbero non essere ancora configurati.
    success_url = reverse_lazy('catalogo:lista_libri')

    def form_valid(self, form):
        """
        Aggiunge un messaggio flash prima di cancellare.
        form_valid() viene chiamato da DeleteView quando l utente conferma con POST.
        self.object e il libro che sta per essere cancellato.
        """
        # Salviamo il titolo prima che l oggetto venga cancellato (dopo non esiste piu).
        messages.warning(self.request, f'Libro "{self.object.titolo}" eliminato.')
        # super().form_valid() esegue la cancellazione effettiva.
        return super().form_valid(form)


# ── LIBRI: Form personalizzato (FBV) ─────────────────────────────────────────

@login_required  # decoratore: se l utente non e loggato, redirect a LOGIN_URL con ?next=/url/
def crea_libro(request):
    """
    Gestisce la creazione di un nuovo libro con LibroForm.
    Usa il pattern GET/POST:
    - GET: mostra il form vuoto
    - POST: valida i dati e salva, oppure mostra gli errori
    """
    # request.POST or None e un modo conciso per:
    #   - passare request.POST al form se la richiesta e POST
    #   - passare None se la richiesta e GET (crea un form non legato, vuoto)
    form = LibroForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # form.is_valid() esegue tutta la validazione (inclusi i metodi clean_*).
        # Se tutti i campi sono validi, restituisce True e popola form.cleaned_data.

        # form.save() crea un nuovo record Libro nel database e lo restituisce.
        libro = form.save()

        # Aggiunge un messaggio flash di successo — verra mostrato nel prossimo template.
        messages.success(request, f'"{libro.titolo}" aggiunto con successo!')

        # Pattern PRG (Post-Redirect-Get): dopo un POST riuscito si fa sempre redirect.
        # Evita che il browser reinvii il form se l utente ricarica la pagina.
        return redirect('catalogo:dettaglio_libro', pk=libro.pk)

    # Sia per GET (form vuoto) che per POST non valido (form con errori):
    # passa il form al template — se POST non valido, il form contiene gia gli errori.
    return render(request, 'catalogo/libro_form.html', {
        'form':          form,
        'titolo_pagina': 'Aggiungi libro',   # usato nel template per il titolo e il breadcrumb
        'testo_bottone': 'Salva libro',      # testo del pulsante submit
    })


@login_required
def modifica_libro(request, pk):
    """
    Gestisce la modifica di un libro esistente.
    Uguale a crea_libro ma: recupera il libro, precompila il form con instance=libro.
    """
    # get_object_or_404: cerca Libro con quel pk. Se non esiste restituisce HTTP 404.
    # Mai usare objects.get() direttamente nelle View: se il record manca si ottiene
    # un errore 500 invece del corretto 404.
    libro = get_object_or_404(Libro, pk=pk)

    # instance=libro: precompila il form con i dati del libro esistente.
    # Quando il form viene salvato, aggiorna il record esistente invece di crearne uno nuovo.
    form = LibroForm(request.POST or None, instance=libro)

    if request.method == 'POST' and form.is_valid():
        form.save()  # aggiorna il record esistente nel database
        messages.success(request, f'Modifiche a "{libro.titolo}" salvate.')
        return redirect('catalogo:dettaglio_libro', pk=libro.pk)

    return render(request, 'catalogo/libro_form.html', {
        'form':          form,
        'libro':         libro,                          # passato al template per il breadcrumb
        'titolo_pagina': f'Modifica: {libro.titolo}',
        'testo_bottone': 'Salva modifiche',
    })


# ══════════════════════════════════════════════════════════════
# AUTORI (FBV — logica piu articolata con annotate)
# ══════════════════════════════════════════════════════════════

def lista_autori(request):
    """
    Mostra la lista di tutti gli autori con il conteggio dei loro libri.
    Usa annotate() per aggiungere un campo calcolato (n_libri) a ogni autore.
    """
    # annotate() aggiunge un campo calcolato a ogni oggetto del QuerySet.
    # db_models.Count('libri') conta i libri collegati tramite related_name='libri'.
    # Il campo n_libri non esiste nel Model — viene calcolato dalla query SQL (COUNT).
    autori = (
        Autore.objects
        .annotate(n_libri=db_models.Count('libri'))
        .order_by('cognome', 'nome')
    )

    # render() carica il template, gli passa il dizionario contesto e restituisce HttpResponse.
    return render(request, 'catalogo/autore_list.html', {'autori': autori})


def dettaglio_autore(request, pk):
    """Mostra il dettaglio di un autore e la lista dei suoi libri."""
    autore = get_object_or_404(Autore, pk=pk)

    # Navigazione inversa tramite related_name='libri' definito nella ForeignKey.
    # autore.libri e il Manager inverso che restituisce i libri di quell autore.
    libri = autore.libri.order_by('anno_pubblicazione')

    return render(request, 'catalogo/autore_detail.html', {
        'autore': autore,
        'libri':  libri,
    })


# ══════════════════════════════════════════════════════════════
# CATEGORIE
# ══════════════════════════════════════════════════════════════

def libri_per_categoria(request, pk):
    """Mostra tutti i libri di una specifica categoria."""
    categoria = get_object_or_404(Categoria, pk=pk)

    # Navigazione inversa tramite related_name='libri' definito nella ManyToManyField.
    # select_related('autore') ottimizza l accesso al nome dell autore in ogni libro.
    libri = categoria.libri.select_related('autore').order_by('titolo')

    return render(request, 'catalogo/libri_per_categoria.html', {
        'categoria': categoria,
        'libri':     libri,
    })


# ══════════════════════════════════════════════════════════════
# AUTENTICAZIONE
# ══════════════════════════════════════════════════════════════

def registrazione(request):
    """
    Gestisce la registrazione di un nuovo utente.
    Dopo la registrazione riuscita, effettua il login automatico.
    """
    # Se l utente e gia autenticato non ha senso mostrargli la pagina di registrazione.
    if request.user.is_authenticated:
        return redirect('catalogo:lista_libri')

    form = RegistrazioneForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # form.save() chiama il nostro save() personalizzato in RegistrazioneForm,
        # che crea l utente con email, nome e cognome.
        user = form.save()

        # auth_login() crea la sessione: da questo momento request.user e autenticato.
        # Senza questa chiamata l utente dovrebbe fare login manualmente dopo la registrazione.
        auth_login(request, user)

        messages.success(request, f'Benvenuto, {user.username}! Account creato con successo.')
        return redirect('catalogo:lista_libri')

    return render(request, 'registration/registrazione.html', {'form': form})
