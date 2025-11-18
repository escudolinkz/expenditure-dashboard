# Architecture Overview

## System Design

The Credit Card Analyzer is a three-tier architecture application:

```
┌─────────────────────────────────────────────────────────────┐
│                         Nginx Proxy                          │
│                     (Port 80 - External)                     │
└─────────────────┬───────────────────────────┬───────────────┘
                  │                           │
         ┌────────▼────────┐         ┌────────▼────────┐
         │    Frontend      │         │    Backend      │
         │  (React + MUI)   │         │   (FastAPI)     │
         │  Port 3000       │         │   Port 8000     │
         └──────────────────┘         └────────┬────────┘
                                               │
                                      ┌────────▼────────┐
                                      │   PostgreSQL    │
                                      │   Port 5432     │
                                      └─────────────────┘
```

## Data Flow

### 1. PDF Upload and Processing

```
User uploads PDF
    ↓
Frontend sends file to /api/statements/upload
    ↓
Backend saves file and creates Statement record
    ↓
Background task triggers PDF parsing
    ↓
ParserFactory selects appropriate parser (Generic, Chase, etc.)
    ↓
Parser extracts transactions using pdfplumber
    ↓
TransactionCategorizer auto-categorizes each transaction
    ↓
Transactions saved to database
    ↓
Statement status updated to "completed"
```

### 2. Transaction Categorization Flow

```
New Transaction
    ↓
Check User Merchant Rules (priority order)
    ↓ (if no match)
Check Default Keyword Patterns
    ↓ (if no match)
Merchant Enrichment (stub for external API)
    ↓ (if no match)
Mark as "Uncategorized"
```

### 3. Analytics Generation

```
User requests analytics
    ↓
Frontend calls /api/analytics/* endpoints
    ↓
AnalyticsService queries database with aggregations
    ↓
SQL GROUP BY for time periods (day/week/month)
    ↓
Results formatted and cached
    ↓
JSON response sent to frontend
    ↓
Chart.js renders visualizations
```

## Database Schema

```sql
users
├── id (PK)
├── email (unique)
├── hashed_password
├── full_name
└── created_at

categories
├── id (PK)
├── name (unique)
├── parent_id (FK → categories.id)
├── color
└── icon

statements
├── id (PK)
├── user_id (FK → users.id)
├── filename
├── file_path
├── card_name
├── card_last4
├── period_start
├── period_end
├── bank_type
├── uploaded_at
├── parsed_at
├── parse_status
└── parse_error

transactions
├── id (PK)
├── statement_id (FK → statements.id)
├── category_id (FK → categories.id)
├── transaction_date
├── posting_date
├── merchant_name
├── description
├── amount
├── currency
├── transaction_type
├── raw_text
├── category_confidence
├── manually_categorized
└── created_at

merchant_rules
├── id (PK)
├── user_id (FK → users.id)
├── category_id (FK → categories.id)
├── pattern
├── pattern_type (exact, contains, regex)
├── is_case_sensitive
├── priority
├── confidence
└── is_global
```

## Key Components

### Backend Services

#### StatementService
- Handles PDF upload and storage
- Triggers parsing (sync or async)
- Manages statement lifecycle
- Re-parsing and recategorization

#### TransactionCategorizer
- Rule-based categorization engine
- Default keyword matching
- Extensible merchant enrichment
- Confidence scoring

#### AnalyticsService
- Time-based aggregations
- Category summaries
- Top merchants
- CSV export

#### PDF Parsers
- **BaseParser**: Abstract base with common utilities
- **GenericParser**: Works with most statements
- **Bank-specific parsers**: Pluggable via ParserFactory

### Frontend Components

#### Pages
- **Login/Register**: Authentication
- **Dashboard**: Summary cards + charts
- **Transactions**: Filterable table with editing
- **Statements**: Upload and management
- **Reports**: Time-based analysis

#### Services
- **api.js**: Centralized Axios client
- **AuthContext**: User state management

## Security Model

### Authentication
- JWT tokens (7-day expiry)
- Bcrypt password hashing
- HTTP-only bearer tokens

### Authorization
- All API endpoints require valid JWT
- User data isolation (user_id filtering)
- No cross-user data access

### Input Validation
- Pydantic schemas for all requests
- File type validation (PDF only)
- Size limits (50MB default)
- SQL injection prevention via ORM

### Network Security
- Nginx reverse proxy
- Rate limiting (10 req/s API, 2 req/m uploads)
- CORS configuration
- Security headers (X-Frame-Options, CSP, etc.)

## Extensibility Points

### 1. Adding a New Bank Parser

```python
# backend/app/parsers/chase_parser.py
from .base_parser import BaseParser, ParsedTransaction

class ChaseParser(BaseParser):
    def parse(self):
        # Implement Chase-specific logic
        pass

# backend/app/parsers/parser_factory.py
from .chase_parser import ChaseParser
ParserFactory.register("chase", ChaseParser)
```

### 2. Adding External Merchant Enrichment

```python
# backend/app/services/categorizer.py
async def _enrich_merchant(self, merchant_name: str):
    # Call external API
    response = await httpx.get(
        "https://api.merchant-lookup.com/categorize",
        params={"merchant": merchant_name}
    )
    data = response.json()

    # Map to category
    category = self.db.query(Category).filter(
        Category.name == data["category"]
    ).first()

    return category.id, data["confidence"]
```

### 3. Adding New Analytics Endpoints

```python
# backend/app/routes/analytics.py
@router.get("/spending/by-merchant")
def get_spending_by_merchant(...):
    # Implement new analytics view
    pass
```

## Performance Considerations

### Database Indexing
- Indexes on: user_id, transaction_date, category_id, merchant_name
- Composite indexes for common queries

### Caching Strategy
- Static assets cached (1 year)
- API responses can be cached (Redis integration point)

### Async Processing
- Background tasks for PDF parsing
- Prevents blocking on large files

### Pagination
- All list endpoints support pagination
- Default 50 items per page
- Prevents large result sets

## Deployment Architecture

### Production Setup

```
Internet
    ↓
Firewall (UFW - ports 80, 443)
    ↓
Nginx (SSL termination, reverse proxy)
    ↓
┌─────────────────────────────────┐
│      Docker Compose Network      │
│  ┌──────────┐  ┌──────────┐    │
│  │ Frontend │  │ Backend  │    │
│  │Container │  │Container │    │
│  └──────────┘  └────┬─────┘    │
│                     │           │
│               ┌─────▼─────┐    │
│               │PostgreSQL │    │
│               │ Container │    │
│               └───────────┘    │
└─────────────────────────────────┘
    ↓
Persistent Volumes (uploads, database)
```

## Monitoring and Logging

### Logs
- Nginx access/error logs
- FastAPI application logs
- Docker container logs

### Health Checks
- `/health` endpoint for backend
- PostgreSQL health check in docker-compose
- Can integrate with monitoring tools (Prometheus, Grafana)

## Future Enhancements

1. **OCR Support**: Add Tesseract for scanned PDFs
2. **ML Categorization**: Train model on user data
3. **Budget Tracking**: Set and monitor budgets
4. **Alerts**: Email/push notifications for overspending
5. **Multi-user**: Household/family accounts
6. **Mobile App**: React Native app
7. **Data Import**: Support for CSV, OFX, QFX formats
8. **Recurring Detection**: Identify subscription patterns
