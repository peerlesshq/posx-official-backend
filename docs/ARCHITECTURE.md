# POSX Framework - Architecture Overview

**Version**: v1.0.0  
**Updated**: 2025-11-07  
**For**: AI Assistants & Developers

---

## 🎯 System Overview

POSX is a **multi-site token presale platform** with strict data isolation using PostgreSQL Row Level Security (RLS).

### Key Characteristics
- **Multi-tenant**: Site-based isolation (NA, ASIA, etc.)
- **Production-ready**: Full security hardening (RLS, CSP, CSRF)
- **Financial precision**: Decimal arithmetic throughout
- **Async-capable**: Celery for background tasks
- **API-first**: RESTful with DRF

---

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────────────┐
│           Frontend (Next.js)                │
│  - Buyer UI                                 │
│  - Agent Dashboard                          │
└─────────────────┬───────────────────────────┘
                  │ HTTPS + JWT
┌─────────────────▼───────────────────────────┐
│       Django REST API (Backend)             │
│  - Authentication (Auth0)                   │
│  - Business Logic                           │
│  - RLS Context Management                   │
└─────────────────┬───────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼──────┐   ┌────────▼─────────┐
│  PostgreSQL  │   │  Redis + Celery  │
│  (with RLS)  │   │  (Async Tasks)   │
└──────────────┘   └──────────────────┘
```

---

## 📊 Data Model

### Core Entities

```
Sites (站点)
  ├── Tiers (档位)
  ├── Orders (订单)
  │   ├── Allocations (代币分配)
  │   └── Commissions (佣金)
  └── Commission Configs (佣金配置)

Users (用户)
  ├── Wallets (钱包)
  └── Referral Tree (推荐树)
```

### RLS Coverage

**Protected Tables** (7 tables):
- `orders` - Direct site_id
- `tiers` - Direct site_id
- `commissions` - Via orders JOIN
- `commission_configs` - Direct site_id
- `commission_levels` - Via configs JOIN
- `agent_commission_configs` - Via configs JOIN
- `allocations` - Via orders JOIN

**Unprotected Tables**:
- `users` - Global (shared across sites)
- `wallets` - Global (user-scoped)
- `sites` - Meta table

---

## 🔒 Security Architecture

### 1. Row Level Security (RLS)

**Policy Pattern**:
```sql
CREATE POLICY rls_<table>_site_isolation ON <table>
    FOR ALL
    USING (site_id = current_setting('app.current_site_id', true)::uuid)
    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
```

**Key Points**:
- ⭐ **FORCE RLS**: Even superuser is restricted
- ⭐ **UUID casting**: `::uuid` for type safety
- ⭐ **Admin bypass**: Separate `posx_admin` role with read-only policies

### 2. Content Security Policy (CSP)

**Production** (strict):
```python
CSP_SCRIPT_SRC = ("'self'", "https://js.stripe.com")  # No unsafe-inline
CSP_STYLE_SRC = ("'self'",)  # No unsafe-inline
CSP_FRAME_ANCESTORS = ("'none'",)  # Prevent embedding
```

**Development** (relaxed):
```python
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
```

### 3. CSRF Protection

**Smart Exemption**:
- Middleware: `CSRFExemptMiddleware` (before `CsrfViewMiddleware`)
- Exempts: `/api/v1/*`, `/health/`, `/ready/`, `/webhooks/*`
- Traditional Django views: CSRF enabled

---

## 🔄 Request Flow

### 1. API Request

```
Client Request
  ↓
HTTPS (Nginx)
  ↓
Django Middleware Stack
  ├─ CORS
  ├─ CSRF Exempt (for API)
  ├─ Authentication (JWT)
  └─ Site Context (set app.current_site_id)
  ↓
View Function
  ↓
Django ORM Query
  ↓
PostgreSQL (RLS Applied)
  ↓
Response
```

### 2. Site Context Setting

```python
# Middleware sets GUC for session
def process_request(self, request):
    site_code = request.headers.get('X-Site-Code', 'NA')
    site = Site.objects.get(code=site_code)
    
    # Set for this connection
    with connection.cursor() as cursor:
        cursor.execute(
            "SET LOCAL app.current_site_id = %s",
            [str(site.site_id)]
        )
    
    request.site_id = site.site_id
```

### 3. Admin Queries (Cross-Site)

```python
# Use separate connection
with connections['admin'].cursor() as cursor:
    # Bypasses RLS (admin role)
    cursor.execute("SELECT * FROM orders")
```

---

## 💰 Financial Flow

### Order Creation

```
1. User selects tier + quantity
   ↓
2. Frontend calls POST /api/v1/orders/
   ↓
3. Backend validates + locks inventory (optimistic lock)
   ↓
4. Create Stripe Payment Intent
   ↓
5. Return order_id + client_secret
   ↓
6. Frontend completes payment
   ↓
7. Webhook: payment_intent.succeeded
   ↓
8. Update order status → paid
   ↓
9. Generate multi-level commissions (Celery)
   ↓
10. Create allocation record (status: pending)
```

### Commission Calculation

```
Order paid → Trigger Celery task
  ↓
Calculate commission tree:
  - Level 1 (direct referrer): 12%
  - Level 2 (referrer's referrer): 4%
  ↓
Create commission records (status: hold)
  ↓
After hold period (7 days):
  Status: hold → ready
  ↓
Admin settles:
  Status: ready → paid
  Transfer via Stripe Connect
```

### Token Allocation

```
Order paid → Create allocation (status: pending)
  ↓
Admin selects batch (max 100)
  ↓
Call Fireblocks API (batch transfer)
  ↓
Update status: pending → processing
  ↓
Fireblocks webhook: TRANSACTION_STATUS_UPDATED
  ↓
Update status: processing → completed
Record tx_hash + confirmed_at
```

---

## 🔧 Key Components

### 1. Middleware

**Site Context** (`apps.core.middleware.site_context`):
- Extracts site from header/subdomain
- Sets `app.current_site_id` GUC
- Attaches to `request.site_id`

**CSRF Exempt** (`config.middleware.csrf_exempt`):
- Exempts API endpoints
- Must be BEFORE `CsrfViewMiddleware`

**Request ID** (`apps.core.middleware.request_id`):
- Generates unique ID per request
- For tracing and logging

### 2. Authentication

**Auth0 JWT** (`apps.core.authentication`):
```python
class Auth0JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        token = extract_token(request)
        payload = verify_jwt(token)  # JWKS with cache
        user = get_or_create_user(payload)
        return (user, None)
```

### 3. Health Checks

**Endpoints**:
- `/health/` - Simple liveness (200 OK)
- `/ready/` - Detailed readiness (DB + Redis + Migrations + RLS)

**Implementation**:
```python
def ready(request):
    checks = {}
    all_healthy = True
    
    # Check DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {e}'
        all_healthy = False
    
    # ... more checks
    
    return JsonResponse(
        {'status': 'healthy' if all_healthy else 'unhealthy', 'checks': checks},
        status=200 if all_healthy else 503  # ⭐ 503 not 500
    )
```

---

## 📦 Deployment

### Docker Services

**Development** (`docker-compose.yml`):
- postgres (5432)
- redis (6379)
- backend (8000) - Django runserver
- celery_worker (optional)
- celery_beat (optional)

**Production** (`docker-compose.prod.yml`):
- postgres (internal)
- redis (internal)
- backend - Gunicorn (4 workers)
- celery_worker (2 instances)
- celery_beat (1 instance)
- nginx (80/443) - Reverse proxy + static files

### Environment Variables

**Critical**:
- `DJANGO_SETTINGS_MODULE` - config.settings.{local|production}
- `SECRET_KEY` - Django secret
- `DB_*` - Database config
- `STRIPE_SECRET_KEY` - sk_test_* (dev) / sk_live_* (prod)
- `AUTH0_DOMAIN` - Auth0 tenant

---

## 🧪 Testing Strategy

### Unit Tests
```python
# Test RLS isolation
def test_site_isolation():
    with site_context(site_a):
        order_a = create_order()
    
    with site_context(site_b):
        # Should not see order_a
        assert not Order.objects.filter(id=order_a.id).exists()
```

### API Tests
```python
# Test order creation
def test_create_order_api(api_client, tier):
    response = api_client.post('/api/v1/orders/', {
        'tier_id': str(tier.id),
        'quantity': 10
    })
    assert response.status_code == 201
```

### Integration Tests
- Stripe webhook handling
- Fireblocks callback processing
- Multi-level commission calculation

---

## 📈 Performance Considerations

### Database
- **Indexes**: All RLS policies have supporting indexes
- **Connection Pooling**: CONN_MAX_AGE = 600
- **Query Optimization**: Use `select_related` / `prefetch_related`

### Caching
- **Redis**: Session + general cache
- **JWKS Cache**: 1 hour TTL
- **Query Cache**: For static data (tiers, configs)

### Async Tasks
- **Celery**: Commission calculations, email sending
- **Worker Scaling**: Based on queue length

---

## 🔍 Debugging Tips

### RLS Issues

**Check policy status**:
```sql
SELECT tablename, rowsecurity FROM pg_tables 
WHERE tablename = 'orders';
```

**Check current setting**:
```sql
SELECT current_setting('app.current_site_id', true);
```

**Bypass for debugging** (dev only):
```python
# Use admin connection
with connections['admin'].cursor() as cursor:
    cursor.execute("SELECT * FROM orders")
```

### CSP Issues

**Check headers**:
```bash
curl -I https://yourdomain.com | grep -i content-security
```

**Temporarily disable** (dev only):
```python
# In settings/local.py
CSP_ENABLED = False
```

---

## 📚 Key Files Reference

| Path | Purpose |
|------|---------|
| `config/settings/base.py` | Shared settings |
| `config/settings/production.py` | Production config ⭐ |
| `config/middleware/csrf_exempt.py` | CSRF exemption ⭐ |
| `apps/core/migrations/0003_*` | RLS indexes ⭐ |
| `apps/core/migrations/0004_*` | RLS policies ⭐ |
| `apps/core/views/health.py` | Health checks ⭐ |
| `config/wsgi.py` | WSGI entry point |
| `config/celery.py` | Celery config |

---

## 🎓 Learning Resources

- **Django Docs**: https://docs.djangoproject.com/
- **DRF Docs**: https://www.django-rest-framework.org/
- **PostgreSQL RLS**: https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- **Stripe API**: https://stripe.com/docs/api
- **Auth0**: https://auth0.com/docs

---

**For AI Assistants**: This architecture prioritizes security and data isolation.
Always consider RLS implications when generating code.
