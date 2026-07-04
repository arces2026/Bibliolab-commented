# BiblioLab

Applicazione web per la gestione di un catalogo libri, sviluppata con Django.
Progetto didattico per il corso **Full Stack Web Development** — ARCES Palermo, Modulo 4.

## Struttura del progetto

```
bibliolab/
├── Dockerfile                  # istruzioni per costruire l immagine Docker
├── docker-compose.yml          # orchestrazione Django + PostgreSQL
├── .env.example                # template per le variabili d ambiente
├── manage.py                   # punto di ingresso per i comandi Django
├── requirements.txt            # dipendenze Python
├── bibliolab/                  # pacchetto di configurazione del progetto
│   ├── settings.py             # tutte le impostazioni (database, app, template...)
│   ├── urls.py                 # URL principali (delega a catalogo/urls.py)
│   └── wsgi.py                 # punto di ingresso per Gunicorn in produzione
├── catalogo/                   # app principale
│   ├── models.py               # Autore, Categoria, Libro
│   ├── forms.py                # LibroForm, RegistrazioneForm
│   ├── views.py                # View HTML (CBV + FBV)
│   ├── api_views.py            # View API REST (JsonResponse + DRF)
│   ├── serializers.py          # Serializer DRF
│   ├── urls.py                 # URL patterns HTML + API
│   ├── admin.py                # configurazione pannello Admin
│   ├── apps.py                 # configurazione app
│   ├── fixtures/               # dati di esempio
│   ├── static/catalogo/css/    # CSS personalizzato
│   ├── migrations/             # storia delle modifiche al database
│   └── templates/catalogo/     # template HTML
└── templates/                  # template globali (base.html, login...)
```

## Avvio rapido (sviluppo locale)

```bash
# 1. Creare e attivare l ambiente virtuale
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
# source venv/bin/activate          # Linux / macOS

# 2. Installare le dipendenze
pip install -r requirements.txt

# 3. Applicare le migrazioni
python manage.py migrate

# 4. Caricare i dati di esempio
python manage.py loaddata catalogo/fixtures/dati_iniziali.json

# 5. Creare un superutente
python manage.py createsuperuser

# 6. Avviare il server
python manage.py runserver
```

Aprire il browser su: http://127.0.0.1:8000/

## Avvio con Docker (produzione)

```bash
# 1. Copiare il file delle variabili d ambiente
cp .env.example .env
# Modificare .env con SECRET_KEY e DB_PASSWORD reali

# 2. Costruire e avviare i container
docker-compose up --build

# 3. Creare il superutente nel container
docker-compose exec web python manage.py createsuperuser
```

## Endpoint API REST

| URL | Metodo | Descrizione |
|-----|--------|-------------|
| /api/libri/ | GET | Lista tutti i libri (JSON semplice) |
| /api/libri/<pk>/ | GET | Dettaglio libro (JSON semplice) |
| /api/v1/libri/ | GET, POST | Lista/crea libri (DRF APIView) |
| /api/v1/libri/<pk>/ | GET, PATCH, DELETE | Dettaglio/modifica/elimina (DRF APIView) |
| /api/v2/libri/ | GET, POST | Lista/crea libri (DRF ViewSet) |
| /api/v2/libri/<pk>/ | GET, PUT, PATCH, DELETE | CRUD completo (DRF ViewSet) |
