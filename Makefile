# ============================================
# POSX Framework - Makefile
# ============================================

.PHONY: help
help:
	@echo "POSX Framework v1.0.0 - Available Commands:"
	@echo ""
	@echo "Development:"
	@echo "  make up              - Start all services (Docker)"
	@echo "  make down            - Stop all services"
	@echo "  make restart         - Restart all services"
	@echo "  make logs            - View logs"
	@echo "  make shell           - Django shell"
	@echo "  make bash            - Backend container bash"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         - Run migrations"
	@echo "  make makemigrations  - Create new migrations"
	@echo "  make dbshell         - PostgreSQL shell"
	@echo "  make dbreset         - Reset database (⚠️  DANGEROUS)"
	@echo ""
	@echo "Checks:"
	@echo "  make check           - Run Django checks"
	@echo "  make check-deploy    - Production deployment checks"
	@echo "  make check-rls       - Verify RLS status"
	@echo "  make health          - Health check"
	@echo ""
	@echo "Tests:"
	@echo "  make test            - Run tests"
	@echo "  make coverage        - Run tests with coverage"
	@echo ""
	@echo "Production:"
	@echo "  make prod-up         - Start production services"
	@echo "  make prod-down       - Stop production services"
	@echo "  make prod-logs       - View production logs"
	@echo "  make collectstatic   - Collect static files"

# ============================================
# Development Commands
# ============================================

.PHONY: up
up:
	docker-compose up -d

.PHONY: down
down:
	docker-compose down

.PHONY: restart
restart: down up

.PHONY: logs
logs:
	docker-compose logs -f

.PHONY: shell
shell:
	docker-compose exec backend python manage.py shell

.PHONY: bash
bash:
	docker-compose exec backend bash

# ============================================
# Database Commands
# ============================================

.PHONY: migrate
migrate:
	docker-compose exec backend python manage.py migrate

.PHONY: makemigrations
makemigrations:
	docker-compose exec backend python manage.py makemigrations

.PHONY: dbshell
dbshell:
	docker-compose exec postgres psql -U posx_app -d posx_local

.PHONY: dbreset
dbreset:
	@echo "⚠️  WARNING: This will DELETE all data!"
	@read -p "Are you sure? (type 'yes'): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		docker-compose down -v; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		docker-compose exec backend python manage.py migrate; \
		echo "✅ Database reset complete"; \
	else \
		echo "❌ Cancelled"; \
	fi

# ============================================
# Checks
# ============================================

.PHONY: check
check:
	docker-compose exec backend python manage.py check

.PHONY: check-deploy
check-deploy:
	docker-compose exec backend python manage.py check --deploy

.PHONY: check-rls
check-rls:
	@echo "Checking RLS status..."
	@docker-compose exec postgres psql -U posx_app -d posx_local -c \
		"SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public' AND tablename IN ('orders', 'tiers', 'commissions', 'allocations');"

.PHONY: health
health:
	@echo "Checking health endpoints..."
	@curl -s http://localhost:8000/health/ | jq .
	@echo ""
	@curl -s http://localhost:8000/ready/ | jq .

# ============================================
# Tests
# ============================================

.PHONY: test
test:
	docker-compose exec backend python manage.py test

.PHONY: coverage
coverage:
	docker-compose exec backend coverage run --source='.' manage.py test
	docker-compose exec backend coverage report
	docker-compose exec backend coverage html

# ============================================
# Production Commands
# ============================================

.PHONY: prod-up
prod-up:
	docker-compose -f docker-compose.prod.yml up -d

.PHONY: prod-down
prod-down:
	docker-compose -f docker-compose.prod.yml down

.PHONY: prod-logs
prod-logs:
	docker-compose -f docker-compose.prod.yml logs -f

.PHONY: collectstatic
collectstatic:
	docker-compose exec backend python manage.py collectstatic --noinput

# ============================================
# Utility Commands
# ============================================

.PHONY: createsuperuser
createsuperuser:
	docker-compose exec backend python manage.py createsuperuser

.PHONY: clean
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +

.PHONY: format
format:
	docker-compose exec backend black .
	docker-compose exec backend isort .

.PHONY: lint
lint:
	docker-compose exec backend flake8 .
	docker-compose exec backend black --check .
