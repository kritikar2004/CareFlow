# CareFlow — Healthcare Demand, Disease & Resource Forecasting

CareFlow is a B.Tech Computer Engineering final-year project designed to support hospital planning through demand forecasting, disease intelligence, and resource analysis.

CareFlow is a decision-support system. Its forecasts are estimates and do not replace professional healthcare judgement.

## Features

- Hospital admissions forecasting
- ICU demand forecasting
- Resource demand forecasting and bottleneck detection
- Disease intelligence and predictions
- Weather display for the registered hospital city
- Dataset upload, validation, versioning, and management
- User authentication and hospital-specific data access

## Technology Stack

**Frontend**
- React
- JavaScript, HTML5, and CSS3
- React Router
- Axios
- Recharts
- Vite

**Backend**
- Python
- FastAPI
- SQLAlchemy
- Uvicorn
- JWT-based authentication

**Machine Learning and Data Processing**
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- Joblib

**Database**
- PostgreSQL

## Project Structure

```text
CareFlow/
├── backend/
├── frontend/
├── ml/
├── datasets/
├── database/
├── .gitignore
└── README.md
```

## Prerequisites

The following tools are required to set up CareFlow on a new machine:

- Python
- Node.js and npm
- PostgreSQL
- Git

**Note:** If these tools are already installed and configured on your system, you do not need to install them again.

## Local Setup

### 1. Backend Setup

Open a terminal in the project root and run:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure the required environment variables in `backend/.env` locally. Ensure PostgreSQL is running and the database is configured.

Start the backend from the `backend` directory:

```powershell
uvicorn main:app --reload
```

The backend should be available at:

`http://127.0.0.1:8000`

### 2. Frontend Setup

Open a second terminal in the project root and run:

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite. Ensure the frontend is configured to communicate with the running backend.

### 3. Database Setup

Review `database/schema.sql` and configure the PostgreSQL database before using the application. Back up important data before making database schema changes.

## Dataset Privacy

- Use synthetic or appropriately licensed public datasets for demonstrations.
- Do not publish private hospital datasets or patient-identifiable information.
- Do not represent synthetic or public datasets as real records from an individual hospital.
- Check dataset licensing and attribution requirements before redistributing data.
- Keep uploaded files, local test artifacts, and credentials out of the public repository.

## Security

Never commit the following to GitHub:

- `.env` files, API keys, passwords, or JWT secrets
- Session cookies and login credentials
- Private hospital datasets or restricted clinical data
- Local uploads and generated credentials
- Virtual environments and installed dependency directories

Review `.gitignore` and staged files before every commit.

## Limitations

- Forecast reliability depends on historical data quality, quantity, and model performance.
- Predictions are estimates and should be interpreted accordingly.
- Resource forecasts may be unreliable when historical observations are insufficient.
- Weather is a dashboard feature and is not used as an input to the current disease-forecasting implementation.
- CareFlow does not replace professional healthcare judgement.

## License

No open-source license has been declared for this repository. Check the terms of third-party code, assets, and datasets before reuse or redistribution.
