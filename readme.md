# One Piece Card Database

![One Piece Card Game](https://img.shields.io/badge/One%20Piece-Card%20Database-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Powered-blue?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.7+-blue?logo=python&logoColor=white)

A modern, Docker-based solution for managing and analyzing One Piece Card Game data using PostgreSQL and Python.

## 📋 Features

- **Docker-powered**: Spin up the entire database environment with a single command
- **PostgreSQL Database**: Reliable and powerful database for card data storage
- **pgAdmin Included**: Web-based PostgreSQL administration tool
- **Automated Data Import**: Python script to import and clean CSV data
- **Price Tracking**: Support for TCG marketplace prices and trends

## Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.7+ (for running the import script)

### Setting Up the Database

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/one-piece-card-database.git
   cd one-piece-card-database
   ```

2. Start the PostgreSQL database and pgAdmin:
   ```bash
   docker-compose up -d
   ```

3. The services will be available at:
   - PostgreSQL: `localhost:5432`
   - pgAdmin: `http://localhost:5050`

### Importing Card Data

1. Install the required Python packages:
   ```bash
   pip install pandas psycopg2-binary sqlalchemy
   ```

2. Place your One Piece card CSV file (named `all_opc.csv`) in the project directory

3. Run the import script:
   ```bash
   python import_cards.py
   ```

## Docker Compose Configuration

The `docker-compose.yml` file sets up:

- A PostgreSQL 15 database server
- pgAdmin for web-based database management

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    container_name: postgres_db
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: card_database
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      
  pgadmin:
    image: dpage/pgadmin4
    container_name: pgadmin
    restart: always
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  postgres_data:
```

## Database Schema

The import script creates a table with the following structure:

| Column | Type | Description |
|--------|------|-------------|
| Card Name | text | Name of the card |
| Set Code | text | Card set identifier |
| TCG Market Price | float | Current price on TCG marketplace |
| TCG Direct Low | float | Lowest direct seller price |
| TCG Low Price With Shipping | float | Lowest price including shipping |
| TCG Low Price | float | Absolute lowest price |
| Total Quantity | integer | Total quantity in collection |
| Add to Quantity | integer | Quantity to be added |
| ... | ... | Additional card attributes |

## Python Import Script

The included Python script (`import_cards.py`) handles:

- CSV data import
- Data cleaning and preprocessing
- Type conversion for price and quantity fields
- Database table creation and data insertion
- Verification of imported records

## pgAdmin Access

1. Open your browser and navigate to `http://localhost:5050`
2. Login with:
   - Email: `admin@example.com`
   - Password: `admin`
3. Add a new server with these details:
   - Name: `One Piece Cards`
   - Host: `postgres`
   - Port: `5432`
   - Username: `postgres`
   - Password: `postgres`

