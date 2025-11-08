# POSX Framework - Development Guide

**For**: Developers & AI Assistants  
**Version**: v1.0.0

---

## 🚀 Getting Started

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- Python 3.11+ (for local development)
- VS Code or Cursor AI (recommended)

### Initial Setup

```bash
# 1. Clone and navigate
cd posx-framework-v1.0

# 2. Configure environment
cp .env.example .env
# Edit .env with your keys

# 3. Start services
make up

# 4. Run migrations
make migrate

# 5. Create superuser
make createsuperuser

# 6. Verify
make health
```

---

## 🛠️ Development Workflow

### Daily Development

```bash
# Start all services
make up

# View logs
make logs

# Run Django shell
make shell

# Access database
make dbshell

# Run tests
make test
```

### Code Changes

```bash
# 1. Make changes to Python files
# Django dev server auto-reloads

# 2. Create migrations (if models changed)
make makemigrations

# 3. Apply migrations
make migrate

# 4. Format code
make format

# 5. Lint code
make lint

# 6. Run tests
make test
```

---

## 📝 Creating New Features

### 1. Creating a New Django App

```bash
# Inside backend/apps/
cd backend/apps
django-admin startapp your_app

# Update structure
your_app/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py       # ⭐ Add this
├── services.py          # ⭐ Add this
├── urls.py              # ⭐ Add this
├── views.py
├── migrations/
│   └── __init__.py
└── tests/               # ⭐ Add this
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

**Register in settings**:
```python
# config/settings/base.py
INSTALLED_APPS = [
    # ...
    'apps.your_app',
]
```

### 2. Creating Models

```python
# apps/your_app/models.py
import uuid
from django.db import models

class YourModel(models.Model):
    """
    Your model description
    
    ⭐ Security: This table is RLS-protected
    """
    # Primary key (UUID)
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Site isolation (if tenant-scoped)
    site = models.ForeignKey(
        'sites.Site',
        on_delete=models.PROTECT,
        related_name='your_models'
    )
    
    # Money fields (ALWAYS Decimal)
    amount = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="Amount in USD"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'your_table_name'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['site', 'created_at']),
        ]
        
    def __str__(self):
        return f"YourModel {self.id}"
```

**Create migration**:
```bash
python manage.py makemigrations your_app
python manage.py migrate
```

**Add RLS policy** (if tenant-scoped):
```python
# Create migration file
python manage.py makemigrations --empty your_app --name add_rls_policy

# Edit the migration
class Migration(migrations.Migration):
    dependencies = [
        ('your_app', '0001_initial'),
    ]
    
    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE your_table_name ENABLE ROW LEVEL SECURITY;
                ALTER TABLE your_table_name FORCE ROW LEVEL SECURITY;
                
                CREATE POLICY rls_your_table_site_isolation ON your_table_name
                    FOR ALL
                    USING (site_id = current_setting('app.current_site_id', true)::uuid)
                    WITH CHECK (site_id = current_setting('app.current_site_id', true)::uuid);
            """,
            reverse_sql="""
                DROP POLICY IF EXISTS rls_your_table_site_isolation ON your_table_name;
                ALTER TABLE your_table_name DISABLE ROW LEVEL SECURITY;
            """
        ),
    ]
```

### 3. Creating Serializers

```python
# apps/your_app/serializers.py
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    """Serializer for YourModel"""
    
    # Custom fields
    amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = YourModel
        fields = [
            'id',
            'site',
            'amount',
            'amount_display',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_amount_display(self, obj):
        """Format amount for display"""
        return f"${obj.amount:.2f}"
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
```

### 4. Creating Views

```python
# apps/your_app/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import YourModel
from .serializers import YourModelSerializer

class YourModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for YourModel
    
    ⭐ Security:
    - Authentication required
    - RLS enforces site isolation
    - CSRF exempt (API)
    """
    queryset = YourModel.objects.all()
    serializer_class = YourModelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Filter queryset by current user
        RLS already filters by site
        """
        return super().get_queryset().filter(
            user=self.request.user
        )
    
    def perform_create(self, serializer):
        """
        Set site_id from request context
        """
        serializer.save(
            site_id=self.request.site_id,
            user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def custom_action(self, request, pk=None):
        """Custom action"""
        obj = self.get_object()
        # Your logic here
        return Response({'status': 'success'})
```

**Register URLs**:
```python
# apps/your_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r'your-models', YourModelViewSet, basename='yourmodel')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Add to main URLs**:
```python
# config/urls.py
urlpatterns = [
    # ...
    path('api/v1/your-app/', include('apps.your_app.urls')),
]
```

### 5. Writing Tests

```python
# apps/your_app/tests/test_views.py
import pytest
from decimal import Decimal
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestYourModelViewSet:
    """Test YourModel API"""
    
    def test_create_model(self, api_client, site, user):
        """Test creating a model"""
        api_client.force_authenticate(user=user)
        
        url = reverse('yourmodel-list')
        data = {
            'amount': '100.50',
        }
        
        response = api_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['amount'] == '100.500000'
    
    def test_list_models(self, api_client, user, your_model):
        """Test listing models"""
        api_client.force_authenticate(user=user)
        
        url = reverse('yourmodel-list')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_site_isolation(self, api_client, user, site_a, site_b):
        """Test RLS isolation"""
        # Create model in site A
        with site_context(site_a.id):
            model_a = YourModel.objects.create(
                site=site_a,
                amount=Decimal('100')
            )
        
        # Try to access from site B
        with site_context(site_b.id):
            assert not YourModel.objects.filter(id=model_a.id).exists()
```

---

## 🎨 Code Style Guide

### Python Style

**Follow PEP 8**:
- Line length: 88 characters (Black default)
- Indentation: 4 spaces
- Imports: isort with Django profile

**Type Hints**:
```python
from decimal import Decimal
from typing import Optional, List
from django.db.models import QuerySet

def calculate_commission(
    amount: Decimal,
    rate: Decimal
) -> Decimal:
    """Calculate commission amount"""
    return amount * rate / Decimal('100')

def get_active_orders(
    site_id: str,
    user_id: Optional[str] = None
) -> QuerySet:
    """Get active orders for site"""
    qs = Order.objects.filter(
        site_id=site_id,
        status='active'
    )
    if user_id:
        qs = qs.filter(user_id=user_id)
    return qs
```

**Docstrings**:
```python
def complex_function(param1: str, param2: int) -> dict:
    """
    Brief description of what function does
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Dictionary with results
    
    Raises:
        ValueError: If param2 is negative
    
    ⭐ Security: Note any security implications
    
    Example:
        >>> result = complex_function("test", 10)
        >>> print(result)
        {'status': 'success'}
    """
    pass
```

### Django Patterns

**Use Manager methods**:
```python
class YourModelManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)
    
    def for_site(self, site_id):
        """RLS will filter automatically"""
        return self.all()

class YourModel(models.Model):
    objects = YourModelManager()
```

**Use Services for complex logic**:
```python
# apps/your_app/services.py
class YourModelService:
    """Service for YourModel business logic"""
    
    @staticmethod
    def create_with_validation(data: dict) -> YourModel:
        """Create model with business validation"""
        # Complex validation
        # Business rules
        # Transaction handling
        return YourModel.objects.create(**data)
```

---

## 🔍 Debugging

### Django Debug Toolbar (Development)

Already configured in `settings/local.py`:
```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
```

Visit: `http://localhost:8000` (toolbar on right side)

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Usage
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message", exc_info=True)
```

**View logs**:
```bash
make logs
# or
docker-compose logs -f backend
```

### Database Queries

**Check RLS status**:
```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename, rowsecurity 
        FROM pg_tables 
        WHERE schemaname = 'public'
    """)
    for row in cursor.fetchall():
        print(row)
```

**Check current site**:
```python
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT current_setting('app.current_site_id', true)")
    site_id = cursor.fetchone()[0]
    print(f"Current site: {site_id}")
```

---

## 🧪 Testing Best Practices

### Fixtures

```python
# conftest.py
import pytest
from apps.sites.models import Site
from apps.users.models import User

@pytest.fixture
def site():
    """Create a test site"""
    return Site.objects.create(
        code='TEST',
        name='Test Site',
        is_active=True
    )

@pytest.fixture
def user(site):
    """Create a test user"""
    return User.objects.create_user(
        email='test@example.com',
        site=site
    )
```

### Site Context Helper

```python
from contextlib import contextmanager
from django.db import connection

@contextmanager
def site_context(site_id):
    """Set site context for testing"""
    with connection.cursor() as cursor:
        cursor.execute(
            "SET LOCAL app.current_site_id = %s",
            [str(site_id)]
        )
    try:
        yield
    finally:
        with connection.cursor() as cursor:
            cursor.execute("RESET app.current_site_id")
```

---

## 📊 Performance Tips

### Query Optimization

```python
# ❌ Bad: N+1 queries
orders = Order.objects.all()
for order in orders:
    print(order.tier.name)  # Query per order

# ✅ Good: Select related
orders = Order.objects.select_related('tier').all()
for order in orders:
    print(order.tier.name)  # No extra query
```

### Bulk Operations

```python
# ❌ Bad: Multiple queries
for data in items:
    YourModel.objects.create(**data)

# ✅ Good: Bulk create
YourModel.objects.bulk_create([
    YourModel(**data) for data in items
])
```

---

## 🔐 Security Checklist

When adding new features:

- [ ] RLS policy added (if tenant-scoped)
- [ ] UUID type casting in policies
- [ ] Input validation in serializers
- [ ] Authentication required
- [ ] CSRF exempt configured (if API)
- [ ] Decimal for money calculations
- [ ] Sensitive data logged appropriately
- [ ] Tests include security scenarios

---

## 📚 Additional Resources

- [Django Best Practices](https://docs.djangoproject.com/en/stable/topics/)
- [DRF Tutorial](https://www.django-rest-framework.org/tutorial/)
- [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Testing in Django](https://docs.djangoproject.com/en/stable/topics/testing/)

---

**Happy Coding!** 🚀

For questions, check the [ARCHITECTURE.md](ARCHITECTURE.md) or system specs.
