# AI Context - Quick Reference

**For**: Cursor AI & AI Assistants  
**Purpose**: Fast context loading for code generation

---

## 🎯 Project Identity

- **Name**: POSX Framework
- **Version**: v1.0.0
- **Type**: Multi-site token presale platform
- **Status**: Production ready
- **Tech**: Django + PostgreSQL RLS + DRF

---

## 🔑 Critical Facts (Never Forget)

### 1. Security ⭐⭐⭐
- **RLS is mandatory** for all tenant data
- **FORCE RLS** - even superuser restricted
- **No unsafe-inline** in production CSP
- **UUID casting required** in RLS policies: `::uuid`
- **site_id is immutable** - database triggers enforce this

### 2. Money ⭐⭐⭐
- **ALWAYS use Decimal** - never float
- **Stripe amounts** = `Decimal * 100` → `int` (cents)
- **DB type** = `NUMERIC(18, 6)`

### 3. Multi-Site ⭐⭐⭐
- **Site isolation** via RLS
- **7 protected tables**: orders, tiers, commissions, etc.
- **GUC variable**: `app.current_site_id`
- **Admin queries**: use separate `posx_admin` connection

---

## 📁 Critical Files (Locations)

```
⭐ RLS Migrations:
  backend/apps/core/migrations/0003_create_rls_indexes.py
  backend/apps/core/migrations/0004_enable_rls_policies.py

⭐ Security Config:
  backend/config/settings/production.py
  backend/config/middleware/csrf_exempt.py

⭐ Health Checks:
  backend/apps/core/views/health.py

⭐ Runtime:
  backend/config/wsgi.py
  backend/config/celery.py
  backend/config/__init__.py
```

---

## 🚫 Never Do This

```python
# ❌ Float for money
amount = 10.10 * 100  # Precision loss!

# ❌ String in RLS policy
USING (site_id = current_setting('app.current_site_id'))  # Wrong type!

# ❌ unsafe-inline in production
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Security risk!

# ❌ Forget site_id
Order.objects.create(amount=100)  # RLS will block!

# ❌ Return 500 on error in health check
return JsonResponse({...}, status=500)  # Should be 503!
```

---

## ✅ Always Do This

```python
# ✅ Decimal for money
from decimal import Decimal
amount = Decimal('10.10')
stripe_cents = int(amount * 100)

# ✅ UUID casting in RLS
USING (site_id = current_setting('app.current_site_id', true)::uuid)

# ✅ Strict CSP in production
CSP_SCRIPT_SRC = ("'self'", "https://js.stripe.com")

# ✅ Include site_id (or let middleware set it)
Order.objects.create(
    site_id=request.site_id,
    amount=Decimal('100.00')
)

# ✅ Return 503 on health check error
return JsonResponse({...}, status=503)
```

---

## 🔄 Common Patterns

### Django Model
```python
class YourModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    site = models.ForeignKey('sites.Site', on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'your_table'
        indexes = [
            models.Index(fields=['site', 'created_at']),
        ]
```

### RLS Policy
```sql
ALTER TABLE your_table ENABLE ROW LEVEL SECURITY;
ALTER TABLE your_table FORCE ROW LEVEL SECURITY;  -- ⭐ FORCE

CREATE POLICY rls_your_table_site_isolation ON your_table
    FOR ALL
    USING (site_id = current_setting('app.current_site_id', true)::uuid)  -- ⭐ ::uuid
    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
```

### API View
```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def your_view(request):
    """
    Your endpoint
    
    ⭐ Security:
    - CSRF exempt (middleware)
    - JWT auth required
    - RLS enforces site isolation
    """
    # Validate
    serializer = YourSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    # Use Decimal
    amount = Decimal(str(request.data['amount']))
    
    # Create with site context
    obj = YourModel.objects.create(
        site_id=request.site_id,
        amount=amount
    )
    
    return Response({'id': str(obj.id)})
```

---

## 🧪 Testing Pattern

```python
@pytest.mark.django_db
def test_your_feature(api_client, site, user):
    """Test your feature"""
    api_client.force_authenticate(user=user)
    
    # Set site context
    with site_context(site.id):
        response = api_client.post('/api/v1/endpoint/', {...})
    
    assert response.status_code == 201
```

---

## 📊 Data Flow

```
Request → Middleware (set site_id) → View → ORM → RLS → Response
```

---

## 🔍 Quick Checks

### Is RLS enabled?
```sql
SELECT tablename, rowsecurity FROM pg_tables 
WHERE tablename = 'your_table';
```

### What's current site?
```sql
SELECT current_setting('app.current_site_id', true);
```

### Check CSP
```bash
grep "unsafe-inline" backend/config/settings/production.py
# Should return empty
```

---

## 📚 Documentation Hierarchy

1. **.cursorrules** ← Start here for rules
2. **ARCHITECTURE.md** ← System design
3. **DEVELOPMENT.md** ← How to develop
4. **README.md** ← Getting started
5. **System Specs** ← Detailed specs

---

## 💡 Tips for AI

1. **Always check RLS** when creating models
2. **Always use Decimal** for money
3. **Always check production.py** for CSP
4. **Always include docstrings** with ⭐ for security notes
5. **Always write tests** for new features

---

## 🎓 Learning Curve

**Must Know**:
- Django basics
- PostgreSQL RLS concept
- Why Decimal > float

**Should Know**:
- DRF serializers
- JWT authentication
- Docker basics

**Nice to Know**:
- Celery tasks
- Stripe API
- CSP headers

---

## 🚀 Quick Commands

```bash
make up           # Start everything
make migrate      # Run migrations
make check-rls    # Verify RLS
make health       # Health check
make shell        # Django shell
make test         # Run tests
```

---

**Remember**: Security first, Decimal for money, RLS for everything.

**When in doubt**: Check .cursorrules and ARCHITECTURE.md
