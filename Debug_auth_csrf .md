# Debug Log: Pinia authStore + Django CSRF Login

## Problem

Login wasn't working between the Vue (Pinia) frontend and the Django backend. The `authStore.js` was calling JSON API endpoints for CSRF/login/logout/me that didn't actually exist on the backend yet.

---

## Bugs found in `authStore.js`

1. **`csrftoken` used before it was defined**
   ```javascript
   console.log({csrftoken: csrftoken})   // ReferenceError — runs before destructuring
   const {csrftoken} = await csrfRes.json()
   ```
   This threw immediately and was silently swallowed by the `catch` block, masking the real problem.

2. **`throw err('Error logging', err)`**
   `err` is an `Error` object, not a function. Calling it throws a `TypeError`, which is what actually surfaced in the console instead of the real login error. Fixed to `throw err`.

3. **Inconsistent CSRF strategy**
   `login()` read the CSRF token from the JSON response body; `logout()` read it from the cookie via `getCsrf()`. Standardized on `getCsrf()` (cookie-based) everywhere, matching the standard Django pattern.

4. **Inconsistent / non-existent endpoint paths**
   Store called `/accounts/api/auth/csrf/`, `accounts/login/` (relative, no leading slash), `/api/auth/logout/`, `/api/auth/me/` — three different base paths, none of which matched real backend routes.

---

## Root cause: no JSON auth API existed

`django.contrib.auth.urls` (mounted at `/accounts/`) only provides **HTML form + redirect** views (`LoginView`, `LogoutView`, password reset, etc.) — confirmed by inspecting `views.py`, which turned out to be Django's own built-in source, not custom project code. These views:

- expect `application/x-www-form-urlencoded` data, not JSON
- return redirects (302), not JSON bodies
- have no `csrf/` or `me/` endpoints

Additionally, the Vite dev server (`vite.config.js`) only proxies `/api` and `/media` to Django (`localhost:8000`). Any request to `/accounts/...` from the Vue app (port 5173) never reached Django at all.

**Conclusion:** the frontend needed a real JSON auth API, under a path Vite actually proxies (`/api/...`).

---

## Fix: dedicated `accounts` Django app

Created a new app to own the JSON auth API, kept separate from `catalogo` (content app) and from Django's built-in `django.contrib.auth.urls` (kept as-is for `/admin/` HTML login).

```
python manage.py startapp accounts
```

```
accounts/
├── serializers.py   # UserSerializer (id, username, email, isStaff)
├── views.py          # csrf, login_view, logout_view, me — all DRF @api_view
└── urls.py           # csrf/, login/, logout/, me/
```

### `accounts/serializers.py`
```python
from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    isStaff = serializers.BooleanField(source='is_staff', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'isStaff']
```

### `accounts/views.py`
```python
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import UserSerializer


@api_view(["GET"])
@permission_classes([AllowAny])
def csrf(request):
    token = get_token(request)
    return Response({"csrftoken": token})


@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    user = authenticate(
        request,
        username=request.data.get("username"),
        password=request.data.get("password"),
    )
    if user is None:
        return Response({"detail": "Invalid credentials"}, status=401)
    login(request, user)
    return Response(UserSerializer(user).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response(status=204)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)
```

### `accounts/urls.py`
```python
from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.csrf),
    path('login/', views.login_view),
    path('logout/', views.logout_view),
    path('me/', views.me),
]
```

### Project `urls.py`
```python
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),  # HTML views, kept for admin login
    path('api/vue/auth/', include('accounts.urls')),              # new JSON API
    path('', include('catalogo.urls')),
]
```

This produces the working, consistent endpoint set:
- `GET  /api/vue/auth/csrf/`
- `POST /api/vue/auth/login/`
- `POST /api/vue/auth/logout/`
- `GET  /api/vue/auth/me/`

All under `/api/`, which Vite already proxies to `localhost:8000`.

### `settings.py`
- Add `"accounts"` to `INSTALLED_APPS`.
- Add explicit CSRF trust for the dev frontend origin:
  ```python
  CSRF_TRUSTED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
  ```

---

## Final `authStore.js`

```javascript
import { defineStore } from "pinia";
import { ref, computed } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  const utente = ref(null) // {id, username, email, isStaff}
  const loading = ref(false)

  const isLogged = computed(() => utente.value !== null)
  const isStaff = computed(() => utente.value?.is_staff === true)

  async function login(username, password) {
    try {
      const csrfRes = await fetch('/api/vue/auth/csrf/', { credentials: 'include' })
      const { csrftoken } = await csrfRes.json()

      const res = await fetch('/api/vue/auth/login/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken,
        },
        body: JSON.stringify({ username, password })
      })

      if (!res.ok) throw new Error(`Credenziali non valide: ${res.status} ${res.statusText}`)
      utente.value = await res.json()
    } catch (err) {
      console.error('Error trying to login:', err)
      throw err
    }
  }

  async function logout() {
    await fetch('/api/vue/auth/logout/', {
      method: 'POST',
      credentials: 'include',
      headers: {
        'X-CSRFToken': getCsrf()
      }
    })
    utente.value = null
  }

  async function caricaUtente() {
    loading.value = true
    try {
      const res = await fetch('/api/vue/auth/me/', { credentials: 'include' })
      if (!res.ok) throw new Error(`Utente non loggato: ${res.status} ${res.statusText}`)
      utente.value = await res.json()
    } catch (err) {
      console.error('Errore caricando utente', err)
    } finally {
      loading.value = false
    }
  }

  function getCsrf() {
    return document.cookie.split(';')
      .find(c => c.trim().startsWith('csrftoken='))
      ?.split('=')[1] || ''
  }

  return { utente, loading, isLogged, isStaff, login, logout, caricaUtente }
})
```

> Note: also renamed `useAutStore` → `useAuthStore` (typo fix) — remember to update the import wherever the store is used.

---

## Remaining checks before calling this done

- [ ] Add `"accounts"` to `INSTALLED_APPS`
- [ ] Add `CSRF_TRUSTED_ORIGINS` to `settings.py`
- [ ] Confirm `catalogo/urls.py` doesn't already define a conflicting `/api/...` route
- [ ] Run migrations if the `accounts` app adds any models (not needed for this — no models were created)
- [ ] Update any component importing `useAutStore` to `useAuthStore`
- [ ] Test flow end-to-end: `GET /api/vue/auth/csrf/` → cookie set → `POST /api/vue/auth/login/` with `X-CSRFToken` header → `GET /api/vue/auth/me/` returns user