# Credit Card Statement Analyzer

A self-hosted full-stack web application for analyzing credit card PDF statements, automatically categorizing transactions, and visualizing spending patterns with interactive charts and time-based reports.

## Features

- **PDF Upload & Parsing**: Upload credit card statements as PDFs and automatically extract transaction data
- **Intelligent Categorization**: Automatic transaction categorization using merchant rules and keyword matching
- **Multi-Card Support**: Manage multiple credit cards and statements in one place
- **Interactive Dashboard**: View spending summaries with pie charts, bar charts, and time-series graphs
- **Transaction Management**: Filter, search, edit, and bulk-update transactions
- **Time-Based Reports**: Analyze spending by day, week, or month with exportable CSV reports
- **Merchant Rules**: Create custom rules to auto-categorize future transactions
- **User Authentication**: Secure JWT-based authentication with email/password

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **PDF Parsing**: pdfplumber
- **Authentication**: JWT with bcrypt password hashing
- **ORM**: SQLAlchemy

### Frontend
- **Framework**: React
- **UI Library**: Material UI
- **Charts**: Chart.js with react-chartjs-2
- **Routing**: React Router
- **HTTP Client**: Axios
- **Date Handling**: date-fns

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Database**: PostgreSQL 15

## Project Structure

```
expenditure-dashboard/
├── backend/
│   ├── app/
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── parsers/             # PDF parsing (pluggable)
│   │   ├── utils/               # Utilities (auth, schemas)
│   │   ├── database.py          # Database configuration
│   │   └── main.py              # FastAPI application
│   ├── tests/                   # Backend tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API services
│   │   ├── contexts/            # React contexts
│   │   ├── App.js
│   │   └── index.js
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── infra/
│   └── nginx.conf               # Reverse proxy configuration
├── docker-compose.yml
├── .env.example
└── README.md
```

## Quick Start

### Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd expenditure-dashboard
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Update environment variables** (optional but recommended for production)
   ```bash
   # Edit .env file
   SECRET_KEY=your-random-secret-key-here
   POSTGRES_PASSWORD=your-secure-password
   ```

4. **Build and start services**
   ```bash
   docker-compose up -d
   ```

5. **Wait for services to be ready** (first run takes longer)
   ```bash
   docker-compose logs -f
   # Wait until you see "Application startup complete"
   ```

6. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost/api
   - API Documentation: http://localhost/api/docs

### Default Ports

- Nginx Reverse Proxy: `80`
- Frontend (internal): `3000`
- Backend (internal): `8000`
- PostgreSQL: `5432`

## Usage Guide

### 1. Register an Account

1. Navigate to http://localhost
2. Click "Sign Up"
3. Enter your email, password, and full name
4. Click "Sign Up"

### 2. Upload a Statement

1. Go to the "Statements" page
2. Click "Upload Statement"
3. Select your PDF statement file
4. (Optional) Enter card name and last 4 digits
5. Select bank type (Generic works for most statements)
6. Click "Upload"

The system will automatically:
- Parse the PDF and extract transactions
- Categorize transactions based on merchant rules
- Make transactions available for viewing and analysis

### 3. View Dashboard

The dashboard shows:
- **Summary Cards**: Total spending, transaction count, top category
- **Category Chart**: Pie or bar chart of spending by category
- **Time Series Chart**: Spending trends (daily/weekly/monthly)
- **Date Range Filters**: Customize the analysis period

### 4. Manage Transactions

On the Transactions page, you can:
- **Filter**: By date, category, type, amount, or search text
- **Edit**: Click "Edit" to change transaction category
- **Create Rules**: When editing, check "Create rule for this merchant" to auto-categorize future transactions
- **Bulk Update**: Select multiple transactions and set category for all at once

### 5. Generate Reports

The Reports page allows:
- **Time-Based Analysis**: View spending by day, week, or month
- **Category Breakdown**: Toggle category breakdown for each period
- **Chart Types**: Switch between line and bar charts
- **CSV Export**: Export transaction data to CSV

## PDF Parsing

### How It Works

The application uses a pluggable parser system:

1. **Base Parser** (`base_parser.py`): Provides common parsing utilities
2. **Generic Parser** (`generic_parser.py`): Works with most standard statements
3. **Bank-Specific Parsers**: Can be added for better accuracy

### Supported Statement Formats

The generic parser works best with:
- Text-based PDFs (not scanned images)
- Tabular transaction listings
- Common date formats (MM/DD/YYYY, etc.)
- Standard merchant names and amounts

### Adding a New Bank Parser

To add support for a specific bank:

1. **Create a new parser** in `backend/app/parsers/`:

```python
from .base_parser import BaseParser, ParsedTransaction

class ChaseParser(BaseParser):
    def parse(self):
        # Extract text from PDF
        text = self.extract_text_from_pdf()

        # Parse Chase-specific format
        # ... your parsing logic ...

        return self.transactions
```

2. **Register the parser** in `parser_factory.py`:

```python
from .chase_parser import ChaseParser

ParserFactory.register("chase", ChaseParser)
```

3. Users can now select "Chase" as the bank type when uploading

## Categorization System

### Default Categories

The system comes with 16 pre-configured categories:
- Groceries
- Dining
- Transport
- Shopping
- Utilities
- Entertainment
- Healthcare
- Subscriptions
- Travel
- Fitness
- Education
- Insurance
- Bills
- Personal Care
- Gifts
- Other

### Auto-Categorization

Transactions are automatically categorized using:

1. **User Merchant Rules**: Exact or pattern-based matching
2. **Default Keywords**: Built-in patterns for common merchants
3. **Manual Override**: User can manually categorize and create rules

### Creating Merchant Rules

**Via UI**:
1. Edit a transaction
2. Set the desired category
3. Check "Create rule for this merchant"
4. Save

**Via API**:
```bash
curl -X POST http://localhost/api/merchant-rules \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pattern": "AMAZON",
    "category_id": 4,
    "pattern_type": "contains"
  }'
```

### Merchant Enrichment (Extensible)

The categorizer includes a stub for external merchant lookup:

```python
# In backend/app/services/categorizer.py
def _enrich_merchant(self, merchant_name: str):
    # Add your external API integration here
    # Example: Call merchant categorization API
    # Return category_id and confidence score
    pass
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token

### Statements
- `GET /api/statements` - List all statements
- `POST /api/statements/upload` - Upload PDF statement
- `POST /api/statements/{id}/parse` - Parse or re-parse statement
- `POST /api/statements/{id}/recategorize` - Re-run categorization
- `DELETE /api/statements/{id}` - Delete statement

### Transactions
- `GET /api/transactions` - List transactions (with filters)
- `PATCH /api/transactions/{id}` - Update transaction
- `POST /api/transactions/bulk-update` - Bulk update categories

### Categories
- `GET /api/categories` - List all categories
- `POST /api/categories` - Create new category

### Analytics
- `GET /api/analytics/summary` - Get spending summary
- `GET /api/analytics/spending/by-category` - Spending by category
- `GET /api/analytics/spending/time-series` - Time-based spending data
- `GET /api/analytics/export/csv` - Export transactions to CSV

Full API documentation: http://localhost/api/docs

## Deployment

### Development Mode

```bash
# Start all services
docker-compose up

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose up --build
```

### Production Deployment on Ubuntu

1. **Install Docker**
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   ```

2. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

3. **Clone and Configure**
   ```bash
   git clone <repository-url>
   cd expenditure-dashboard
   cp .env.example .env

   # IMPORTANT: Edit .env with secure values
   nano .env
   ```

4. **Start Services**
   ```bash
   docker-compose up -d
   ```

5. **Set up Firewall**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp  # If using HTTPS
   sudo ufw enable
   ```

6. **Set up SSL (Optional but Recommended)**

   Install Certbot:
   ```bash
   sudo apt install certbot python3-certbot-nginx
   ```

   Get certificate:
   ```bash
   sudo certbot --nginx -d yourdomain.com
   ```

7. **Enable Auto-start**
   ```bash
   # Docker Compose services restart automatically with 'restart: unless-stopped'
   # To ensure Docker starts on boot:
   sudo systemctl enable docker
   ```

### Backup and Restore

**Backup Database**:
```bash
docker-compose exec db pg_dump -U postgres creditcard_analyzer > backup.sql
```

**Backup Uploads**:
```bash
docker cp creditcard_backend:/app/uploads ./uploads_backup
```

**Restore Database**:
```bash
docker-compose exec -T db psql -U postgres creditcard_analyzer < backup.sql
```

## Testing

### Backend Tests

```bash
# Run tests
cd backend
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app tests/
```

### Sample Test Files

Create test files in `backend/tests/`:

```python
# backend/tests/test_parser.py
from app.parsers import GenericParser

def test_generic_parser():
    parser = GenericParser("test_statement.pdf")
    transactions = parser.parse()
    assert len(transactions) > 0
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### PDF Parsing Failures

- Ensure PDF is text-based (not scanned image)
- Try "Generic" bank type first
- Check backend logs: `docker-compose logs backend`
- Consider creating a bank-specific parser

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up --build frontend
```

### Port Already in Use

```bash
# Find process using port 80
sudo lsof -i :80

# Change ports in docker-compose.yml if needed
# Example: Change "80:80" to "8080:80"
```

## Security Considerations

1. **Change Default Secrets**: Update `SECRET_KEY` in `.env`
2. **Use Strong Passwords**: For database and user accounts
3. **Enable HTTPS**: Use SSL certificates in production
4. **Limit File Uploads**: Max 50MB by default (configurable in nginx.conf)
5. **Rate Limiting**: Nginx includes rate limiting for API endpoints
6. **Input Validation**: All inputs are validated on backend
7. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
8. **XSS Protection**: React escapes content by default

## Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - feel free to use for personal or commercial projects.

## Support

For issues or questions:
- Check the [Issues](https://github.com/your-repo/issues) page
- Review the API documentation at `/api/docs`
- Check Docker logs for error messages

## Roadmap

Future enhancements:
- [ ] OCR support for scanned PDFs
- [ ] Machine learning-based categorization
- [ ] Budget tracking and alerts
- [ ] Mobile app (React Native)
- [ ] Multi-user households
- [ ] Recurring transaction detection
- [ ] Export to Mint/YNAB formats
- [ ] Email statement import
