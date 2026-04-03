```md
# Khet2Mandi  
## AI-Powered Agricultural Profit Intelligence  

> **"Indian farmers do not fail because they cannot grow crops. They fail because markets stay unpredictable."**

Khet2Mandi is an AI-driven agricultural profit intelligence platform designed to help farmers maximize income by answering three critical questions:

- **When to Sell**
- **Where to Sell**
- **Whether to Wait**

Unlike traditional mandi price apps, Khet2Mandi combines **price forecasting, arrival trends, weather intelligence, and logistics cost** to deliver **profit-based actionable recommendations**.

---

# Problem Statement

Indian farmers often lose profit not because of poor crop production, but because of missing market intelligence.

## Major Challenges

- Delayed mandi price information (24–48 hour lag)
- Distress selling under urgent cash pressure
- Dependence on a single local mandi
- No forecasting system for future prices
- No transport-cost aware selling decisions

## Current Impact

- ₹1.5 lakh crore annual farmer income loss  
- 58% farmers lack reliable price access  
- Up to 3× price gap between farm-gate and mandi prices  

---

# Solution

Khet2Mandi transforms fragmented agricultural data into **AI-powered profit intelligence**.

## Core Pipeline

Raw Data → AI Prediction → Profit Decision

### Input Data Sources

- Mandi price records  
- Commodity arrivals  
- Weather data  
- Logistics cost  
- Historical market trends  

### Output for Farmers

- **Sell Now**
- **Wait**
- **Shift to Another Mandi**

---

# Key Features

## 1. 8-Week Price Forecasting
Predicts commodity prices up to 8 weeks ahead using machine learning models.

## 2. Sell Timing Optimizer
Suggests the ideal selling window based on predicted price peaks.

## 3. Demand Index
Uses arrival data to detect oversupply and early price pressure.

## 4. Profit Optimizer
Calculates actual net profit after transport cost.

## 5. Price Crash Alerts
Warns farmers when price drop probability becomes high.

## 6. Mandi Comparison Engine
Compares nearby mandis based on net profitability.

## 7. Weather Sensitivity Modeling
Maps rainfall and temperature impact on commodity prices.

## 8. Community Trust Layer
Supports farmer-reported price verification.

---

#  System Architecture

## Data Sources
- Agmarknet mandi APIs  
- Historical price dataset (2021–2025)  
- Weather APIs  
- Arrival records  
- Logistics data  

## Processing Layer
- Data cleaning  
- Normalization  
- Feature engineering  
- Lag features  
- Rolling averages  

## AI Prediction Core
- Time-series forecasting  
- XGBoost models  
- Seasonality detection  
- Arrival-price correlation  
- Weather sensitivity modeling  

## Decision Engine
- Net profit optimizer  
- Crash alert logic  
- Confidence scoring  
- Multi-mandi recommendation engine  

## Delivery Layer
- Mobile-first frontend  
- REST API backend  
- Local language support  

---

#  AI Model Inputs

- Historical mandi prices (t-1 to t-52)  
- Arrival volume  
- Rainfall and temperature  
- Seasonal indicators  
- Transport distance  
- MSP support price  

## Model Output

- Predicted price  
- Confidence score  
- Recommended action  

---

# 📱 Farmer User Journey

## Step 1
Select crop  

## Step 2
Select mandi / auto-detect location  

## Step 3
AI analyzes:
- Price  
- Arrivals  
- Weather  

## Step 4
View net profit across mandis  

## Step 5
Take action:
- SELL NOW  
- WAIT  
- SHIFT MANDI  

---

# 🛠 Tech Stack

## Frontend
- React JS  
- Mobile-first PWA  
- Local language UI  

## Backend
- FastAPI / Node.js  
- REST APIs  
- Caching layer  

## Machine Learning
- XGBoost  
- Scikit-learn  
- Pandas  
- NumPy  

## Database
- PostgreSQL  
- Redis  

## External APIs
- Agmarknet API  
- OpenWeather API  

---

# 🚀 Why Khet2Mandi is Different

## Profit-Centric Intelligence
We do not only predict prices — we optimize profit.

## Personalized Advice
Two farmers with the same crop can receive different recommendations based on:
- Distance  
- Storage availability  
- Transport cost  

## Decision-Centric UX
One clear recommendation instead of complex dashboards.

## Multi-Factor Agriculture Intelligence
Combines:
- Price  
- Arrivals  
- Weather  
- Logistics  

---

# ⚠️ Challenges & Mitigation

## Data Quality Issues
Fallback datasets + anomaly detection pipeline  

## API Delays
Cached data + freshness indicators  

## Policy Shocks
Rule-based override engine for MSP/export bans  

## Rural Connectivity
Offline mode + SMS fallback  

---

# 📈 Roadmap

## Phase 1
8-week forecasting MVP (MP + Rajasthan)

## Phase 2
Warehouse + cold chain integration

## Phase 3
Collective farmer selling clusters

## Phase 4
Credit + insurance intelligence

## Phase 5
National agricultural intelligence platform

---

# 🌍 Potential Impact

- ₹18,000 average annual gain per farming family  
- 30% reduction in distress selling  
- 130M farmers addressable market  
- ₹45,000 crore recoverable margin  

---

# 👨‍💻 Team

**Team RRR**  
ABV-IIITM Gwalior  

- Ravi Ratnakar  
- Rashmi Nagora  
- Rishita Pareek  

---

# 🎯 Vision

> **"In agriculture, timing decides income. We make timing intelligent."**
```
