# Domande e dubbi

Indice
ul
- [settings.py](#-settings.py)
- [urls.py proj](#-urls.py-proj)

## settings.py
A cosa serve nel ns caso? 
```python
from pathlib import Path  # per costruire percorsi cross-platform (Windows/Linux/Mac)
```

## urls.py

```python
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

Come funziona nel dettaglio
Parametri della funzione static()
settings.MEDIA_URL - L'URL base per i file media (di solito /media/)

Definito in settings.py come MEDIA_URL = '/media/'

document_root=settings.MEDIA_ROOT - Il percorso fisico sul filesystem dove sono salvati i file

Definito in settings.py come MEDIA_ROOT = BASE_DIR / 'media'