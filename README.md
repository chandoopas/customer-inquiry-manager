# Customer Inquiry Manager

An AI-powered customer inquiry management system built on Microsoft Azure.

## 🎥 Demo
*(Video link coming — Week 4)*

## 🚀 What It Does
- Customers submit inquiries via a web form
- Azure OpenAI automatically categorizes each inquiry as
  Sales, Billing, Support, or General
- Urgent inquiries (Sales, Billing) trigger instant email alerts
- All inquiries stored in Azure SQL Database
- Admin dashboard to view and manage all inquiries *(coming Week 3)*
- Automated daily summary emails *(coming Week 3)*

## 🏗️ Architecture
```
Customer → Web Form → Flask App (Azure VM)
                           ↓
                     Azure SQL Database
                           ↓
                     Azure OpenAI (categorization)
                           ↓
                     SendGrid (email notifications)
```

## ☁️ Azure Services Used
| Service | Purpose |
|---------|---------|
| Azure Virtual Machine (Ubuntu) | Hosts the Flask web application |
| Azure SQL Database | Stores customers, inquiries, AI categories |
| Azure OpenAI (gpt-4o-mini) | Categorizes and summarizes inquiries |
| SendGrid | Sends urgent email notifications |

## 🛠️ Tech Stack
- Python 3.12
- Flask + Gunicorn + Nginx
- Azure SQL (pyodbc)
- Azure OpenAI
- SendGrid

## 📁 Project Structure
```
customer-inquiry-manager/
├── app.py              # Flask web application
├── database.py         # Azure SQL database functions
├── ai_service.py       # Azure OpenAI categorization
├── notifications.py    # SendGrid email notifications
├── requirements.txt    # Python dependencies
└── LESSONS_LEARNED.md  # Errors encountered and solutions
```

## 🔧 Local Setup
1. Clone the repo
2. Create virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with your credentials (see `.env` section below)
5. Run: `python app.py`

## 🔑 Environment Variables Required
```
DB_SERVER=your-server.database.windows.net
DB_NAME=your-database-name
DB_USERNAME=your-sql-username
DB_PASSWORD=your-sql-password
AZURE_OPENAI_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
SENDGRID_API_KEY=SG.your-sendgrid-key
SENDGRID_FROM_EMAIL=your-verified-sender@email.com
NOTIFICATION_EMAIL=alerts-recipient@email.com
```

## 📖 Lessons Learned
See [LESSONS_LEARNED.md](LESSONS_LEARNED.md) for a full log of
errors encountered during this project and how each was resolved.

## 👨‍💻 Author
Built as a 30-day DevOps/Cloud learning project.
