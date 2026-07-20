"""
api_views.py — View API REST di BiblioLab.

Questo file contiene le View che restituiscono JSON invece di HTML.
E separato da views.py per chiarezza: View HTML da una parte, View API dall altra.

Struttura:
  - api_libri, api_libro_dettaglio: View semplici con JsonResponse (senza DRF)
  - LibroListAPIView, LibroDetailAPIView: View con DRF APIView (GET, POST, PATCH, DELETE)
  - LibroViewSet: ViewSet DRF che genera tutto il CRUD automaticamente
"""

from django.http import JsonResponse  # restituisce dati JSON come HttpResponse
from rest_framework.views import APIView  # classe base per View API DRF
from rest_framework.response import (
    Response,
)  # risposta DRF con serializzazione automatica
from rest_framework import status  # costanti per i codici HTTP (200, 201, 404...)
from rest_framework import viewsets  # ViewSet: CRUD completo in una classe
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly,
)  # permessi: lettura libera, scrittura con login
from django.shortcuts import get_object_or_404  # 404 se il record non esiste

from .models import Libro, Autore, Categoria  # il nostro Model
from .serializers import (
    LibroSerializer,
    AutoreSerializer,
    CategoriaSerializer,
)  # il nostro Serializer DRF
from django.db.models import Q

# ══════════════════════════════════════════════════════════════
# API SEMPLICI CON JsonResponse (senza DRF)
# ══════════════════════════════════════════════════════════════


def api_libri(request):
    """
    GET /api/libri/ — restituisce la lista di tutti i libri in formato JSON.
    Implementazione manuale senza DRF: utile per capire come funziona internamente.
    """
    # QuerySet ottimizzata: evita query N+1 per autore e categorie.
    libri = Libro.objects.select_related("autore").prefetch_related("categorie")

    # Filtro opzionale: /api/libri/?disponibile=true
    disp = request.GET.get("disponibile")
    if disp == "true":
        libri = libri.filter(disponibile=True)
    elif disp == "false":
        libri = libri.filter(disponibile=False)

    # Serializzazione manuale: convertiamo ogni oggetto Python in un dizionario Python.
    # La list comprehension crea la lista di dizionari.
    data = [
        {
            "id": libro.pk,  # pk e sempre presente (chiave primaria)
            "titolo": libro.titolo,
            "autore": {  # oggetto annidato per l autore
                "id": libro.autore.pk,
                "nome": libro.autore.nome,
                "cognome": libro.autore.cognome,
            },
            "categorie": [c.nome for c in libro.categorie.all()],  # lista di nomi
            "anno_pubblicazione": libro.anno_pubblicazione,
            "isbn": libro.isbn,
            "disponibile": libro.disponibile,
            "descrizione": libro.descrizione,
            "cover_url": libro.cover_url,
        }
        for libro in libri  # itera su tutta la QuerySet
    ]

    # JsonResponse converte automaticamente il dizionario in JSON
    # e imposta Content-Type: application/json nell header della risposta.
    # safe=False e necessario per serializzare una lista invece di un dizionario.
    return JsonResponse({"count": len(data), "results": data})


def api_libro_dettaglio(request, pk):
    """GET /api/libri/<pk>/ — restituisce il dettaglio di un singolo libro."""
    libro = get_object_or_404(Libro, pk=pk)

    data = {
        "id": libro.pk,
        "titolo": libro.titolo,
        "autore": str(libro.autore),  # usa __str__ di Autore
        "categorie": [c.nome for c in libro.categorie.all()],
        "anno_pubblicazione": libro.anno_pubblicazione,
        "isbn": libro.isbn,
        "descrizione": libro.descrizione,
        "disponibile": libro.disponibile,
        # .isoformat() converte datetime in stringa ISO 8601: "2024-01-10T09:00:00+00:00"
        # JSON non ha un tipo nativo per le date — si usa sempre una stringa.
        "data_aggiunta": libro.data_aggiunta.isoformat(),
    }

    return JsonResponse(data)


# ══════════════════════════════════════════════════════════════
# API CON DJANGO REST FRAMEWORK (APIView) - usati per il frontend Vue
# ══════════════════════════════════════════════════════════════


class LibroListApiView(APIView):
    """
    GET /api/v1/libri/  — lista libri con serializzazione DRF
    POST /api/v1/libri/ — crea un nuovo libro (solo autenticati)

    APIView gestisce automaticamente:
    - il parsing del JSON in input (request.data invece di request.POST)
    - la serializzazione della risposta
    - la Browsable API (interfaccia HTML per testare dal browser)
    """

    # permission_classes: chi puo usare questo endpoint.
    # IsAuthenticatedOrReadOnly = GET libero, POST/PUT/PATCH/DELETE richiedono login.
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Gestisce le richieste GET — restituisce la lista dei libri."""
        qs = Libro.objects.select_related("autore").prefetch_related("categorie")

        # Filtro opzionale per disponibilita.
        if request.GET.get("disponibile") == "true":
            qs = qs.filter(disponibile=True)

        # many=True: serializza una lista di oggetti invece di uno solo.
        serializer = LibroSerializer(qs, many=True)

        # Response di DRF: sceglie automaticamente il formato (JSON, HTML)
        # in base all header Accept della richiesta.
        return Response({"count": qs.count(), "results": serializer.data})
    
    def post(self, request):
        """Gestisce le richieste POST — crea un nuovo libro."""

        # request.data contiene i dati JSON parsati automaticamente da DRF.
        serializer = LibroSerializer(data=request.data)

        if serializer.is_valid():
            # save() crea il nuovo record nel database.
            serializer.save()
            # HTTP 201 Created: codice corretto per la creazione di una risorsa.
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # HTTP 400 Bad Request: i dati inviati non sono validi.
        # serializer.errors contiene i messaggi di errore per ogni campo.
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LibroDetailApiView(APIView):
    """
    GET /api/v1/libri/<pk>/    — dettaglio singolo libro
    PATCH /api/v1/libri/<pk>/  — aggiornamento parziale
    DELETE /api/v1/libri/<pk>/ — eliminazione
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        """Recupera il libro per pk o restituisce 404. Metodo helper riutilizzato dai metodi HTTP."""
        return get_object_or_404(Libro, pk=pk)

    def get(self, request, pk):
        """GET: restituisce il dettaglio del libro."""
        # Serializziamo un singolo oggetto (many=False, default).
        serializer = LibroSerializer(self.get_object(pk))
        return Response(serializer.data)  # HTTP 200 OK (default)

    def patch(self, request, pk):
        """PATCH: aggiornamento parziale — solo i campi inviati vengono aggiornati."""
        # instance=: il serializer sa che stiamo aggiornando un record esistente.
        # partial=True: non richiede tutti i campi obbligatori (solo quelli inviati).
        serializer = LibroSerializer(
            self.get_object(pk),
            data=request.data,
            partial=True,  # aggiornamento parziale: solo i campi presenti vengono modificati
        )
        if serializer.is_valid():
            serializer.save()  # esegue UPDATE nel database
            return Response(serializer.data)  # HTTP 200 con il libro aggiornato
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """DELETE: elimina il libro. Non restituisce body (204 No Content)."""
        self.get_object(pk).delete()  # esegue DELETE nel database
        # HTTP 204 No Content: operazione riuscita, nessun dato da restituire.
        return Response(status=status.HTTP_204_NO_CONTENT)


class AutoreListApiView(APIView):
    """
    GET /api/v1/autori/ - lista autori
    POST /api/v1/autori/ - crea un nuovo autore (solo autenticati)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Gestisce le richieste GET — restituisce la lista degli autori.
        Supporta il filtro opzionale per ricerca.
        """

        # QuerySet base per tutti gli autori
        qs = Autore.objects.all()

        # Filtro opzionale per ricerca per nome o cognome
        search = request.GET.get("search")
        if search:
            qs = qs.filter(Q(nome__icontains=search) | Q(cognome__icontains=search))

        # Filtro per autore con libri disponibili
        solo_disponibili = request.GET.get("disponibili")
        if solo_disponibili == "true":
            qs = qs.filter(libri__disponibile=True).distinct()

        # Serializzazione
        serializer = AutoreSerializer(qs, many=True)

        return Response({"count": qs.count(), "results": serializer.data})

    def post(self, request):
        """
        Gestisce le richieste POST — crea un nuovo autore.
        """
        serializer = AutoreSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AutoreDetailApiView(APIView):
    """
    GET /api/v1/autori/<pk>/    — dettaglio di un autore
    PUT /api/v1/autori/<pk>/    — aggiornamento completo
    PATCH /api/v1/autori/<pk>/  — aggiornamento parziale
    DELETE /api/v1/autori/<pk>/ — eliminazione (solo se non ha libri)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        """Recupera l'autore per pk o restituisce 404."""
        return get_object_or_404(Autore, pk=pk)

    def get(self, request, pk):
        """GET: restituisce il dettaglio dell'autore con i suoi libri."""
        autore = self.get_object(pk)
        serializer = AutoreSerializer(autore)

        return Response(serializer.data)

    def put(self, request, pk):
        """PUT: aggiornamento completo dell'autore."""
        autore = self.get_object(pk)
        serializer = AutoreSerializer(autore, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """PATCH: aggiornamento parziale dell'autore."""
        autore = self.get_object(pk)
        serializer = AutoreSerializer(
            autore, data=request.data, partial=True  # Permette aggiornamento parziale
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        DELETE: elimina l'autore.
        Restituisce 400 se l'autore ha libri associati (PROTECT constraint).
        """
        autore = self.get_object(pk)

        # Verifica se l'autore ha libri associati
        if autore.libri.exists():  # related_name='libri'
            return Response(
                {
                    "error": "Impossibile eliminare l'autore perché ha libri associati. "
                    "Prima elimina o riassegna i suoi libri."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        autore.delete()
        return Response(
            {"message": "Autore eliminato con successo."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CategoriaListApiView(APIView):
    """
    GET /api/v1/categorie/ — lista di tutte le categorie
    POST /api/v1/categorie/ — crea una nuova categoria (solo autenticati)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        """
        Gestisce le richieste GET — restituisce la lista delle categorie.
        Supporta filtro opzionale per ricerca e conteggio libri.
        """
        # QuerySet base con tutte le categorie
        queryset = Categoria.objects.all()

        # Filtro opzionale per ricerca per nome
        search = request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(nome__icontains=search) | Q(descrizione__icontains=search)
            )

        # Filtro per categorie con almeno un libro
        con_libri = request.GET.get("con_libri")
        if con_libri == "true":
            queryset = queryset.filter(libri__isnull=False).distinct()

        # Filtro per categorie con libri disponibili
        con_libri_disponibili = request.GET.get("con_libri_disponibili")
        if con_libri_disponibili == "true":
            queryset = queryset.filter(libri__disponibile=True).distinct()

        # Serializzazione
        serializer = CategoriaSerializer(queryset, many=True)

        # Opzionale: includere conteggio libri per categoria
        include_count = request.GET.get("include_count")
        if include_count == "true":
            data = serializer.data
            for item in data:
                categoria = Categoria.objects.get(pk=item["id"])
                item["libri_count"] = categoria.libri.count()  # related_name='libri'
            return Response({"count": queryset.count(), "results": data})

        return Response({"count": queryset.count(), "results": serializer.data})

    def post(self, request):
        """
        Gestisce le richieste POST — crea una nuova categoria.
        """
        serializer = CategoriaSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoriaDetailApiView(APIView):
    """
    GET /api/v1/categorie/<pk>/    — dettaglio di una categoria
    PUT /api/v1/categorie/<pk>/    — aggiornamento completo
    PATCH /api/v1/categorie/<pk>/  — aggiornamento parziale
    DELETE /api/v1/categorie/<pk>/ — eliminazione (solo se non ha libri)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_object(self, pk):
        """Recupera la categoria per pk o restituisce 404."""
        return get_object_or_404(Categoria, pk=pk)

    def get(self, request, pk):
        """
        GET: restituisce il dettaglio della categoria con i suoi libri.
        """
        categoria = self.get_object(pk)
        serializer = CategoriaSerializer(categoria)

        return Response(serializer.data)

    def put(self, request, pk):
        """PUT: aggiornamento completo della categoria."""
        categoria = self.get_object(pk)
        serializer = CategoriaSerializer(categoria, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """PATCH: aggiornamento parziale della categoria."""
        categoria = self.get_object(pk)
        serializer = CategoriaSerializer(
            categoria,
            data=request.data,
            partial=True,  # Permette aggiornamento parziale
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        DELETE: elimina la categoria.
        Restituisce 400 se la categoria ha libri associati.
        """
        categoria = self.get_object(pk)

        # Verifica se la categoria ha libri associati
        if categoria.libri.exists():  # related_name='libri'
            return Response(
                {
                    "error": "Impossibile eliminare la categoria perché ha libri associati. "
                    "Prima rimuovi i libri da questa categoria."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        categoria.delete()
        return Response(
            {"message": "Categoria eliminata con successo."},
            status=status.HTTP_204_NO_CONTENT,
        )


# ══════════════════════════════════════════════════════════════
# API CON VIEWSET (CRUD COMPLETO IN UNA CLASSE)
# ══════════════════════════════════════════════════════════════


class LibroViewSet(viewsets.ModelViewSet):
    """
    ViewSet per il Model Libro — equivalente a 5 View separate (list, detail, create, update, delete).
    Usato con DefaultRouter in urls.py che genera automaticamente tutti gli URL.

    ModelViewSet include: list, create, retrieve, update, partial_update, destroy.
    """

    # queryset: la QuerySet base usata da tutte le azioni del ViewSet.
    # Ottimizzata con select_related e prefetch_related.
    queryset = Libro.objects.select_related("autore").prefetch_related("categorie")

    # serializer_class: il Serializer usato per convertire i dati.
    serializer_class = LibroSerializer

    # permission_classes: stesse regole delle APIView — lettura libera, scrittura con login.
    permission_classes = [IsAuthenticatedOrReadOnly]
