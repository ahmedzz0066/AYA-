# AYA - Teams Meeting Summarizer

A web application that connects to Microsoft Teams, fetches meeting transcripts and chat messages, and generates AI-powered summaries with key points, decisions, and action items.

## Features

- **Microsoft Teams Integration** — Sign in with your Microsoft 365 account and fetch recent Teams meetings automatically
- **Transcript Capture** — Pulls meeting transcripts and chat messages via Microsoft Graph API
- **AI Summarization** — Uses OpenAI GPT-4o to generate structured summaries including:
  - Key discussion points
  - Decisions made
  - Action items with assignees
  - Important notes and deadlines
- **Paste & Summarize** — Paste any transcript or meeting notes for instant summarization
- **Export** — Download summaries as PDF, Markdown, or plain text

## Prerequisites

- Python 3.10+
- Microsoft 365 account with Teams
- Azure AD App Registration (for Graph API access)
- OpenAI API key

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ahmedzz0066/AYA-.git
cd AYA-
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Register an Azure AD App

1. Go to [Azure Portal](https://portal.azure.com) > **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Set the **Redirect URI** to `http://localhost:5000/callback` (Web platform)
4. Under **Certificates & secrets**, create a new client secret
5. Under **API permissions**, add the following **Microsoft Graph** delegated permissions:
   - `User.Read`
   - `OnlineMeetings.Read`
   - `OnlineMeetingTranscript.Read.All`
   - `Chat.Read`
   - `CallRecords.Read`
6. Click **Grant admin consent** for your organization

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```
MS_CLIENT_ID=<your Azure app client ID>
MS_CLIENT_SECRET=<your Azure app client secret>
MS_TENANT_ID=<your Azure tenant ID>
MS_REDIRECT_URI=http://localhost:5000/callback
OPENAI_API_KEY=<your OpenAI API key>
OPENAI_MODEL=gpt-4o
FLASK_SECRET_KEY=<random secret string>
FLASK_PORT=5000
```

### 6. Run the application

```bash
python run.py
```

Open your browser to `http://localhost:5000`.

## Usage

### Option A: Automatic (via Teams)

1. Click **Sign in with Microsoft** on the home page
2. Authorize the app to access your Teams data
3. Browse your recent Teams meetings
4. Click **Summarize** on any meeting
5. View the AI summary and export it

### Option B: Manual (paste transcript)

1. Click **Paste Transcript** in the navigation
2. Paste your meeting transcript or notes
3. Click **Summarize**
4. View and export the result

## Project Structure

```
AYA-/
├── app/
│   ├── __init__.py
│   ├── auth.py          # Microsoft OAuth2 authentication (MSAL)
│   ├── config.py        # Configuration from environment variables
│   ├── exporter.py      # Export summaries to PDF/Markdown/Text
│   ├── graph_client.py  # Microsoft Graph API client
│   ├── summarizer.py    # OpenAI-powered summarization
│   └── web.py           # Flask web application and routes
├── templates/
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Landing page
│   ├── meetings.html    # Meetings list page
│   ├── paste.html       # Paste transcript page
│   └── summary.html     # Summary display page
├── static/
│   └── style.css        # Application styles
├── exports/             # Generated export files
├── .env.example         # Environment variables template
├── .gitignore
├── requirements.txt
├── run.py               # Application entry point
└── README.md
```

## Notes

- **Transcription must be enabled** in your Teams meetings for transcript capture to work. Enable it in Teams meeting settings or start transcription during the meeting.
- The app uses **delegated permissions**, so it can only access meetings the signed-in user has access to.
- Meeting chat messages are fetched from the meeting's associated chat thread.
