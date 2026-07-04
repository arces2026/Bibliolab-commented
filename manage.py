#!/usr/bin/env python
# manage.py — punto di ingresso per tutti i comandi amministrativi di Django.
# Questo file viene creato automaticamente da django-admin startproject.
# Non va mai modificato manualmente.

import os   # modulo della libreria standard Python per interagire con il sistema operativo
import sys  # modulo per accedere agli argomenti della riga di comando (sys.argv)


def main():
    # Imposta la variabile d'ambiente che dice a Django quale file settings usare.
    # os.environ.setdefault imposta la variabile SOLO se non è già impostata —
    # questo permette di sovrascriverla dall'esterno (es. in produzione con settings_prod).
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliolab.settings')

    try:
        # Importa la funzione che legge sys.argv e lancia il comando corretto.
        # L'import è dentro il try perché se Django non è installato vogliamo
        # un messaggio di errore utile invece del generico ImportError.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Se Django non è installato (o il virtualenv non è attivato) diamo
        # un messaggio chiaro invece del traceback generico di Python.
        raise ImportError(
            "Impossibile importare Django. Assicuratevi che sia installato e "
            "che il virtualenv sia attivato."
        ) from exc

    # Passa sys.argv (es. ['manage.py', 'runserver']) alla funzione di gestione.
    # Django legge il primo argomento (es. 'runserver') e lancia il comando corrispondente.
    execute_from_command_line(sys.argv)


# Esegue main() solo se questo file è eseguito direttamente (python manage.py ...)
# e non quando viene importato da un altro modulo.
if __name__ == '__main__':
    main()
