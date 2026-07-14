"""
api_views.py — View API REST di BiblioLab.

Questo file contiene le View che restituiscono JSON invece di HTML.
E separato da views.py per chiarezza: View HTML da una parte, View API dall altra.

Struttura:
  - api_libri, api_libro_dettaglio: View semplici con JsonResponse (senza DRF)
  - LibroListAPIView, LibroDetailAPIView: View con DRF APIView (GET, POST, PATCH, DELETE)
  - LibroViewSet: ViewSet DRF che genera tutto il CRUD automaticamente
"""

from django.http import JsonResponse                       # restituisce dati JSON come HttpResponse
from rest_framework.views import APIView                   # classe base per View API DRF
from rest_framework.response import Response               # risposta DRF con serializzazione automatica
from rest_framework import status                          # costanti per i codici HTTP (200, 201, 404...)
from rest_framework import viewsets                        # ViewSet: CRUD completo in una classe
from rest_framework.permissions import IsAuthenticatedOrReadOnly  # permessi: lettura libera, scrittura con login
from django.shortcuts import get_object_or_404             # 404 se il record non esiste

from .models import Libro                                  # il nostro Model
from .serializers import LibroSerializer                   # il nostro Serializer DRF


# ══════════════════════════════════════════════════════════════
# API SEMPLICI CON JsonResponse (senza DRF)
# ══════════════════════════════════════════════════════════════

def api_libri(request):
    """
    GET /api/libri/ — restituisce la lista di tutti i libri in formato JSON.
    Implementazione manuale senza DRF: utile per capire come funziona internamente.
    """
    # QuerySet ottimizzata: evita query N+1 per autore e categorie.
    libri = Libro.objects.select_related('autore').prefetch_related('categorie')

    # Filtro opzionale: /api/libri/?disponibile=true
    disp = request.GET.get('disponibile')
    if disp == 'true':
        libri = libri.filter(disponibile=True)
    elif disp == 'false':
        libri = libri.filter(disponibile=False)

    # Serializzazione manuale: convertiamo ogni oggetto Python in un dizionario Python.
    # La list comprehension crea la lista di dizionari.
    data = [
        {
            'id':                  libro.pk,          # pk e sempre presente (chiave primaria)
            'titolo':              libro.titolo,
            'autore': {                               # oggetto annidato per l autore
                'id':      libro.autore.pk,
                'nome':    libro.autore.nome,
                'cognome': libro.autore.cognome,
            },
            'categorie':           [c.nome for c in libro.categorie.all()],  # lista di nomi
            'anno_pubblicazione':  libro.anno_pubblicazione,
            'isbn':                libro.isbn,
            'disponibile':         libro.disponibile,
            'descrizione':         libro.descrizione,
            'cover_url':           libro.cover_url,
        }
        for libro in libri  # itera su tutta la QuerySet
    ]

    # JsonResponse converte automaticamente il dizionario in JSON
    # e imposta Content-Type: application/json nell header della risposta.
    # safe=False e necessario per serializzare una lista invece di un dizionario.
    return JsonResponse({'count': len(data), 'results': data})


def api_libro_dettaglio(request, pk):
    """GET /api/libri/<pk>/ — restituisce il dettaglio di un singolo libro."""
    libro = get_object_or_404(Libro, pk=pk)

    data = {
        'id':                 libro.pk,
        'titolo':             libro.titolo,
        'autore':             str(libro.autore),           # usa __str__ di Autore
        'categorie':          [c.nome for c in libro.categorie.all()],
        'anno_pubblicazione': libro.anno_pubblicazione,
        'isbn':               libro.isbn,
        'descrizione':        libro.descrizione,
        'disponibile':        libro.disponibile,
        # .isoformat() converte datetime in stringa ISO 8601: "2024-01-10T09:00:00+00:00"
        # JSON non ha un tipo nativo per le date — si usa sempre una stringa.
        'data_aggiunta':      libro.data_aggiunta.isoformat(),
    }

    return JsonResponse(data)


# ══════════════════════════════════════════════════════════════
# API CON DJANGO REST FRAMEWORK (APIView)
# ══════════════════════════════════════════════════════════════

class LibroListAPIView(APIView):
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
        qs = Libro.objects.select_related('autore').prefetch_related('categorie')

        # Filtro opzionale per disponibilita.
        if request.GET.get('disponibile') == 'true':
            qs = qs.filter(disponibile=True)

        # many=True: serializza una lista di oggetti invece di uno solo.
        serializer = LibroSerializer(qs, many=True)

        # Response di DRF: sceglie automaticamente il formato (JSON, HTML)
        # in base all header Accept della richiesta.
        return Response({'count': qs.count(), 'results': serializer.data})

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


class LibroDetailAPIView(APIView):
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
            partial=True  # aggiornamento parziale: solo i campi presenti vengono modificati
        )
        if serializer.is_valid():
            serializer.save()   # esegue UPDATE nel database
            return Response(serializer.data)  # HTTP 200 con il libro aggiornato
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """DELETE: elimina il libro. Non restituisce body (204 No Content)."""
        self.get_object(pk).delete()  # esegue DELETE nel database
        # HTTP 204 No Content: operazione riuscita, nessun dato da restituire.
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    queryset = Libro.objects.select_related('autore').prefetch_related('categorie')

    # serializer_class: il Serializer usato per convertire i dati.
    serializer_class = LibroSerializer

    # permission_classes: stesse regole delle APIView — lettura libera, scrittura con login.
    permission_classes = [IsAuthenticatedOrReadOnly]
