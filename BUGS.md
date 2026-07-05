# BUGS

```bash
WARNINGS:
?: (staticfiles.W004) The directory 'C:\Git-repos\bibliolab_commented\static' in the STATICFILES_DIRS setting does not exist.
```

## Errore caricamento pagine da admin

Risolto con update to django>=5.0,6.0< (requirements.txt)

## 404 v1

Page not found (404)
Request Method:	GET
Request URL:	http://localhost:8000/api/v1/libri/

## Comments and extends in templates

The {% extends %} tag has to be the first in the template, even before the {% comment %} tag

## Dockerfile

Solved by eliminating New line error in the CMD list.

## Database manager connection in production (es. Dbeaver)

Not compatible with SCRAM-SHA-256 authentication