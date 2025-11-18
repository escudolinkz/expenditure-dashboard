# Quick Start Guide

Get your Credit Card Analyzer running in 5 minutes!

## Prerequisites

- Docker (20.10+)
- Docker Compose (2.0+)

## Installation Steps

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd expenditure-dashboard

# Create environment file
cp .env.example .env

# (Optional) Edit .env to change default passwords
nano .env
```

### 2. Start the Application

```bash
# Build and start all services
docker-compose up -d

# Watch the logs to see when it's ready
docker-compose logs -f
```

Wait for the message: **"Application startup complete"**

### 3. Access the Application

Open your browser and navigate to:
- **Application**: http://localhost
- **API Docs**: http://localhost/api/docs

### 4. Create Your Account

1. Click **"Sign Up"**
2. Enter your email and password
3. Click **"Create Account"**

### 5. Upload Your First Statement

1. Navigate to **"Statements"** page
2. Click **"Upload Statement"**
3. Select your PDF credit card statement
4. (Optional) Enter card details
5. Click **"Upload"**

The system will automatically parse and categorize your transactions!

### 6. Explore Your Data

- **Dashboard**: View spending summaries and charts
- **Transactions**: Filter, search, and edit transactions
- **Reports**: Generate time-based spending reports

## Common Commands

```bash
# View logs
docker-compose logs -f

# Stop the application
docker-compose down

# Restart after changes
docker-compose up -d --build

# Access database
docker-compose exec db psql -U postgres creditcard_analyzer

# Run backend tests
docker-compose exec backend pytest
```

## Troubleshooting

### Port 80 already in use?

Edit `docker-compose.yml` and change the nginx port:
```yaml
nginx:
  ports:
    - "8080:80"  # Change to port 8080
```

Then access at http://localhost:8080

### Database connection errors?

```bash
# Restart the database
docker-compose restart db

# Check database logs
docker-compose logs db
```

### PDF parsing failed?

- Ensure PDF is text-based (not scanned)
- Try "Generic" bank type
- Check logs: `docker-compose logs backend`

## Next Steps

- Read the [README.md](README.md) for detailed documentation
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- Review API docs at http://localhost/api/docs

## Getting Help

If you encounter issues:
1. Check the logs: `docker-compose logs`
2. Review the README troubleshooting section
3. Open an issue on GitHub

Enjoy analyzing your spending! 💳📊
