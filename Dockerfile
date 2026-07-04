# Dockerfile — istruzioni per costruire l immagine Docker di BiblioLab.
#
# Ogni istruzione crea un layer (strato) dell immagine.
# Docker mette in cache i layer: se un layer non cambia, viene riusato nella build successiva.
# L ordine e progettato per massimizzare il riuso della cache.

# ── IMMAGINE BASE ─────────────────────────────────────────────────────────────
# FROM: specifica l immagine di partenza dal Docker Hub.
# python:3.11-slim = Python 3.11 su Debian "slim" (ridotto, senza pacchetti inutili).
# La versione esplicita (3.11) garantisce riproducibilita: non cambia mai.
FROM python:3.11-slim

# ── VARIABILI D AMBIENTE PYTHON ───────────────────────────────────────────────
# ENV: imposta variabili d ambiente disponibili per tutti i comandi successivi.
ENV PYTHONDONTWRITEBYTECODE=1
# PYTHONDONTWRITEBYTECODE=1: Python non crea file .pyc (bytecode compilato).
# In un container non servono — risparmia spazio e evita file inutili.

ENV PYTHONUNBUFFERED=1
# PYTHONUNBUFFERED=1: l output di print() e dei log viene inviato immediatamente a stdout.
# Senza questa variabile, Python bufferizza l output e i log potrebbero apparire in ritardo.
# Essenziale per vedere i log in tempo reale con docker-compose logs.

# ── CARTELLA DI LAVORO ────────────────────────────────────────────────────────
# WORKDIR: imposta la cartella di lavoro per tutti i comandi successivi.
# Se la cartella non esiste, viene creata automaticamente.
# /app e la convenzione standard per le applicazioni nei container.
WORKDIR /app

# ── INSTALLAZIONE DIPENDENZE ──────────────────────────────────────────────────
# COPIA requirements.txt PRIMA del codice sorgente.
# Questo e il trucco fondamentale per la cache Docker:
#   - Se solo il codice cambia, questo layer (pip install) viene recuperato dalla cache
#   - La reinstallazione avviene solo quando requirements.txt cambia
# Senza questo trucco, ogni modifica al codice richiederebbe reinstallare tutto.
COPY requirements.txt .

# RUN: esegue un comando durante la build dell immagine.
# --no-cache-dir: pip non salva i file scaricati (risparmia spazio nell immagine).
RUN pip install --no-cache-dir -r requirements.txt

# ── CODICE SORGENTE ───────────────────────────────────────────────────────────
# COPY . .: copia tutto il contenuto della cartella corrente del host
# nella cartella /app del container.
# I file in .dockerignore vengono esclusi (venv/, .git/, *.sqlite3...).
COPY . .

# ── FILE STATICI ──────────────────────────────────────────────────────────────
# Raccoglie tutti i file statici in STATIC_ROOT (staticfiles/).
# Va fatto durante la build perche in produzione DEBUG=False e Django
# non serve automaticamente i file statici — lo fa Whitenoise da staticfiles/.
# --noinput: non chiede conferma interattiva (il container non ha terminale).
RUN python manage.py collectstatic --noinput

# ── PORTA ─────────────────────────────────────────────────────────────────────
# EXPOSE: documenta quale porta espone il container (non la pubblica automaticamente).
# La pubblicazione avviene in docker-compose.yml con ports: ["8000:8000"].
EXPOSE 8000

# ── COMANDO DI AVVIO ──────────────────────────────────────────────────────────
# CMD: comando eseguito quando il container viene avviato.
# Usiamo Gunicorn invece di manage.py runserver:
#   - Gunicorn gestisce piu richieste in parallelo (3 worker)
#   - --bind 0.0.0.0:8000: accetta connessioni da qualsiasi IP sulla porta 8000
#   - --workers 3: 3 processi worker paralleli
#   - --access-logfile -: scrive i log di accesso su stdout (leggibili con docker logs)
CMD ["gunicorn", "bibliolab.wsgi:application","--bind", "0.0.0.0:8000","--workers", "3","--access-logfile", "-"]
