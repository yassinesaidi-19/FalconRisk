# FalconRisk
**Real-Time Risk & Fraud Monitoring Platform for Digital Wallets**

FalconRisk is an end-to-end data engineering and analytics platform designed to simulate fraud detection and risk monitoring for a MENA-region digital wallet.

The project demonstrates a modern data stack including:

- **PostgreSQL** (Data Warehouse)
- **dbt** (Transformation & Testing)
- **Docker** (Containerized Infrastructure)
- **Streamlit** (Executive Dashboard)
- **Synthetic Transaction Generator**
- **Rule-Based Risk Scoring Engine**

---

## 🚀 Project Overview

FalconRisk simulates how a digital wallet platform can:

- Ingest raw transactional data
- Transform it into analytical models
- Generate fraud risk signals
- Score transactions by risk level
- Provide real-time executive monitoring
- Enable investigation & drill-down of suspicious activity

This project reflects a production-style architecture used in fintech and digital payment systems.

---

## 🏗 Architecture

### Data Flow:
```
Synthetic data generation → Parquet files
           ↓
Loader → Bronze schema (Postgres raw layer)
           ↓
dbt → Silver & Gold analytical models
           ↓
Risk engine → Signal detection + risk scoring
           ↓
Streamlit → Executive dashboard
```

### Technology Stack:
- **PostgreSQL 16**
- **dbt 1.8**
- **Docker Compose**
- **Streamlit**
- **Pandas**
- **Python**

---

## 📊 Dashboard Features

### Executive Overview
- Total Transactions
- Total Payment Volume
- Approval Rate
- High-Risk Transaction Ratio

### Real-Time Monitoring
- High-risk transactions in last X minutes
- Top customers by risk activity
- Top merchants by risk exposure

### Risk Classification
- Distribution by risk category (Low / Medium / High)

### Daily Trends
- Transactions & volume over time
- Approval rate trend
- Risk category evolution

### Investigation
- High-risk transactions with triggered rule explanations
- Drill-down into:
  - Transaction details
  - Triggered risk signals

---

## 🧠 Risk Engine Logic

The platform uses rule-based risk detection including:

- **Velocity rule** (multiple transactions in short time window)
- **High amount deviation** vs user baseline
- **New device + high transaction amount**

### Risk scoring logic:
- **1 rule → Low**
- **2 rules → Medium**
- **3+ rules → High**

---

## 🗂 Project Structure

```
mena-payments-analytics/
│
├── data/                      # Synthetic parquet data
├── docker/                    # Dockerfiles + init scripts
├── dbt/
│   └── mena_payments/
│       ├── models/
│       │   ├── silver/
│       │   ├── gold/
│       │   └── risk/
│       ├── dbt_project.yml
│       └── profiles.yml
│
├── streamlit_app/
│   └── app.py
│
├── src/
│   ├── generator/
│   └── loader/
│
├── docker-compose.yml
├── Makefile / run.ps1
└── README.md
```

---

## ⚙️ How to Run

### 1️⃣ Start services
```bash
docker compose up -d
```

### 2️⃣ Load data
```bash
docker compose run --rm loader
```

### 3️⃣ Build dbt models
```bash
docker compose run --rm dbt run --full-refresh
```

### 4️⃣ Run tests
```bash
docker compose run --rm dbt test
```

### 5️⃣ Open Dashboard
- **Streamlit Dashboard:** http://localhost:8501
- **Adminer (Database UI):** http://localhost:8081

---

## ✅ Data Quality

dbt tests implemented:

- `not_null`
- `unique`
- Model validation checks

Ensuring warehouse integrity and reliability.

---

## 🌍 Use Case

Designed for:

- Digital wallets
- Fintech platforms
- Regional payment systems (MENA context)
- Fraud & compliance monitoring teams

---

## 📈 Future Enhancements

- Real-time streaming ingestion (Kafka)
- Machine learning fraud scoring
- Alert notification system
- Airflow orchestration
- Multi-tenant support
- Cloud deployment (AWS/GCP/Azure)

---

## 👤 Author

Built as a portfolio project to demonstrate:

- Data engineering fundamentals
- Modern analytics stack
- Fraud risk modeling
- Containerized pipelines
- Executive-level dashboarding

---

## 🛡 License

Open-source for educational and portfolio use.


##DashBoard Screenshots:
<img width="1919" height="926" alt="image" src="https://github.com/user-attachments/assets/c626ef6f-7eae-41e0-8568-3dbdd31f0d8e" />
<img width="1455" height="669" alt="image" src="https://github.com/user-attachments/assets/3bb34768-881e-4ed9-b232-39e4bac887bf" />
<img width="1460" height="569" alt="image" src="https://github.com/user-attachments/assets/e5424a43-eca0-4020-8870-3dab4f3ba487" />
<img width="1466" height="592" alt="image" src="https://github.com/user-attachments/assets/9420423a-f2fd-4090-b83e-8256995a0a4e" />



