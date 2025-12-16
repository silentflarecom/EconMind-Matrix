# Setup Instructions

## First-Time Setup

### 1. Install Dependencies

**Backend:**
```bash
cd backend
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Configure User-Agent

⚠️ **CRITICAL**: The application comes with a placeholder User-Agent. **You MUST configure your own User-Agent before starting any crawl tasks.**

Wikipedia's [User-Agent Policy](https://meta.wikimedia.org/wiki/User-Agent_policy) strictly requires all API clients to identify themselves.

**Steps to Configure:**

1. Start the application (see section 3 below).
2. Go to the **Manage** page in the web interface.
3. Locate the **User Agent Configuration** panel (look for the yellow warning box).
4. Enter a User-Agent string that identifies YOUR project.
   
   **Format:** `ProjectName/Version (Contact Information)`

   **Valid Examples:**
   - `MyResearchBot/1.0 (mailto:me@university.edu)`
   - `CorpusBuilder/2.0 (https://github.com/myusername/myproject)`
   - `WikiDataTool/1.0 (mailto:dev@company.com)`

5. Click **💾 Save Settings**.

> **Note:** The default User-Agent `TermCorpusBot/1.0 (...)` is a placeholder. Using it for heavy crawling may result in IP blocking by Wikipedia.

**Privacy Note:** Your User-Agent is only sent to Wikipedia servers with your API requests. It is stored locally in your `corpus.db` and is never sent to any other third party.

### 3. Running the Application

**Start Backend:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Start Frontend:**
```bash
cd frontend
npm run dev
```

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
WikipediaPython/
├── backend/
│   ├── main.py           # FastAPI application
│   ├── database.py       # Database operations
│   ├── scheduler.py      # Batch crawling logic
│   ├── models.py         # Pydantic models
│   └── requirements.txt  # Python dependencies
├── frontend/
│   └── src/
│       ├── App.vue
│       └── components/
│           ├── BatchImport.vue
│           ├── TaskManager.vue
│           ├── ResultsTable.vue
│           └── ...
└── README.md
```

## Privacy & Data

- The database file (`corpus.db`) is gitignored by default
- No personal data is collected or transmitted
- All Wikipedia API requests use your configured User-Agent
- You can export and backup your data anytime via the Manage page

## Support

For issues or questions:
1. Check the [main README](README.md) for feature documentation
2. Review [Wikipedia's API documentation](https://www.mediawiki.org/wiki/API:Main_page)
3. Open an issue on GitHub

---

## Layer 3: News Crawler Configuration

The news crawler in Layer 3 supports advanced configuration options:

### Crawler Settings

| Setting | Default | Range | Description |
|:--------|:--------|:------|:------------|
| **Days Back** | 7 | 1-30 | How far back to crawl news |
| **Concurrency** | 3 | 1-10 | Parallel HTTP requests |
| **Delay** | 1.0 | 0.5-10 | Seconds between requests |
| **Rotate UA** | ✓ | on/off | Rotate User-Agent headers |

### Proxy Pool (Optional)

To use proxies, enable the "Enable Proxies" checkbox and enter your proxies:
```
http://proxy1:8080
socks5://user:pass@proxy2:1080
http://192.168.1.100:3128
```

**Supported protocols:** `http://`, `https://`, `socks5://`

### Running Crawler Detection

When you open the Crawl tab, the system automatically checks if a crawler from a previous session is still running. If detected, a yellow warning banner will appear with a "Force Stop" button.

---

## System Management

### Backing Up Data

Go to **⚙️ System** page to download database backups:

| Button | Downloads | Contents |
|:-------|:----------|:---------|
| 📚 Backup Layer 1 | `corpus.db` | Terms & bilingual definitions |
| 📊 Backup Layer 2 | `policy_corpus.db` | Policy reports & alignments |
| 📰 Backup Layer 3 | `sentiment_corpus.db` | News articles & annotations |

### Resetting All Data

⚠️ **WARNING:** The "Reset All Data" button will permanently delete:
- **Layer 1:** All tasks, terms, and associations
- **Layer 2:** All policy reports, paragraphs, and alignments
- **Layer 3:** All news articles and sentiment annotations

This action cannot be undone. Always backup your data first!

---

## Troubleshooting
 
 **1. `CORS` errors in browser console:**
 - Ensure the backend is running (`python -m uvicorn ...`).
 - Refresh the page. The backend might have been restarting.
 
 **2. Database locked errors:**
 - SQLite allows only one writer at a time. This usually resolves automatically.
 - If persistent, check if you have the database file open in another program (like a DB viewer).
 
 **3. "Term not found" errors:**
 - Check if the term exists on the selected language Wikipedia.
 - Verify your internet connection.
 - If crawling many terms, check if you've been rate-limited (slow down requests by increasing delay).
 - Verify your User-Agent is set correctly.

**4. News crawler not stopping:**
 - Click the "Stop Crawl" button and wait for verification (up to 15 seconds).
 - If the crawler appears stuck, refresh the page and check the System page.
 - Force stop using the yellow warning banner if a "running crawler" is detected.

**5. Layer 2/3 statistics showing "No data":**
 - Ensure the backend has been restarted after installation.
 - Check that all Layer 2 and Layer 3 database tables exist in `corpus.db`.
 
 ---
 
 **Note**: This is an educational project. Please use it responsibly and in compliance with Wikipedia's policies.

