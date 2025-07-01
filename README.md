# 🤖 Text-to-SQL Chatbot

An intelligent chatbot for converting natural language to SQL queries with the ability to execute them and visualize results.

## 📋 Project Description

Text-to-SQL Chatbot is a web application that allows users to ask questions in natural language and receive corresponding SQL queries that are automatically executed in the database. Results are displayed in a convenient tabular format with the ability to create charts.

### 🎯 Key Features

- **SQL Generation from Natural Language**: Uses OpenAI API to convert questions in Russian/English to SQL queries
- **SQL Query Execution**: Automatic execution of generated queries in PostgreSQL
- **Data Visualization**: Display results in tables and charts (line and bar charts)    

### 🏗️ Architecture

The project consists of three main components:

1. **Backend (FastAPI)** - API server for SQL generation and execution
2. **Frontend (Streamlit)** - Web interface for user interaction
3. **Database (PostgreSQL)** - Database with demo data

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   FastAPI       │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
│   (Port 8501)   │    │   (Port 8000)   │    │   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                |
                       ┌─────────────────┐
                       │     OpenAI      │
                       │      API        │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### 1. Clone the repository

```bash
git clone <repository-url>
cd text-to-sql-chatbot
```

### 2. Configure environment variables

Copy the environment variables example file:

```bash
cp env.example .env
```

Edit the `.env` file and add your OpenAI API key:

```env
# Database Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=5432
POSTGRES_DB=text_to_sql_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4-turbo
```

### 3. Start the application

Start all services using Docker Compose:

```bash
docker-compose up --build
```

### 4. Access the application

After successful startup, the application will be available at the following addresses:

- **Streamlit Frontend**: http://localhost:8501
- **FastAPI Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📊 Demo Data

To fill the database with demo data, go to your Postgres database using any IDE (for example, DataGrip) 
and run SQL from the **db_init.sql** file.

The demo data contains:

- **customers** - customer information (10 records)
- **products** - product catalog (15 records)
- **sales** - sales history (200 records)

### Example questions for testing

```
Basic and general questions
- What is the total revenue from all sales for all time?
- How many unique buyers made at least one purchase?

Questions for ranking (Top-N)
- Show the top 5 best-selling products by total revenue.
- Which buyer from the city 'Moscow' spent the most money?

Questions for analysis by time
- What is the sales dynamics by month for 2024? Show the total revenue for each month.
- How many new customers were registered in the second half of 2023?

Questions for analysis by categories and products
- Which product category is the most profitable?
- What products were most often purchased together with 'Notebook "ProBook 15"'?

Questions about customer behavior
- What is the average check (average amount of one sale)?
- Show a list of buyers who did not make any purchases in 2024.
```
