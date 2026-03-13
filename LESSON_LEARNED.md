# Lessons Learned — Customer Inquiry Manager

A full log of real errors encountered during this DevOps project
and exactly how each was resolved. Kept as a reference for future projects.

---

## Error 1 — Port 5000 Already in Use (Mac)


**Symptom:**
```
OSError: [Errno 48] Address already in use — port 5000
```
**Cause:**
macOS AirPlay Receiver uses port 5000 by default. Flask also defaults to port 5000, causing a conflict.

**Fix:**
System Settings → General → AirDrop & Handoff → disable **AirPlay Receiver**.
Alternatively run Flask on a different port:
```bash
flask run --port 5001
```

**Lesson:**
Always check what is running on a port before assuming your app is broken.
`sudo lsof -i :5000` shows which process owns the port.

---

## Error 2 — Python venv Not Available on Ubuntu


**Symptom:**
```
The virtual environment was not created successfully because ensurepip is not available.
```
**Cause:**
Ubuntu 22.04 ships Python 3.12 without the venv module included by default.

**Fix:**
```bash
sudo apt install python3.12-venv -y
python3 -m venv venv
```

**Lesson:**
On Ubuntu always install the venv package explicitly before creating a virtual environment.

---

## Error 3 — Port 8000 Already in Use (Gunicorn Orphan)


**Symptom:**
```
[ERROR] Connection in use: ('127.0.0.1', 8000)
```
**Cause:**
A previous Gunicorn process was still running in the background after being interrupted.

**Fix:**
```bash
sudo pkill gunicorn
```
Then restart Gunicorn normally. To check what is using the port:
```bash
sudo lsof -i :8000
```

**Lesson:**
Always kill orphan processes before restarting a server. Add `sudo pkill gunicorn` as a habit before every deployment.

---

## Error 4 — Azure SQL Region Capacity Error


**Symptom:**
```
Deployment failed — No available capacity in region East US 2
for the selected database configuration.
```
**Cause:**
East US 2 had no available serverless SQL capacity at that time.

**Fix:**
Changed region from **East US 2** to **East US** during database creation.

**Lesson:**
Azure services have regional capacity limits. If creation fails, try a neighbouring region. East US and East US 2 are different data centres.

---

## Error 5 — Azure Data Studio Retired


**Symptom:**
Azure Data Studio download page redirected to a deprecation notice.

**Cause:**
Microsoft retired Azure Data Studio on February 28, 2026.

**Fix:**
Used **VS Code** with the **mssql extension** instead.
Extension ID: `ms-mssql.mssql`
Provides identical functionality — connect, query, and manage Azure SQL directly from VS Code.

**Lesson:**
Cloud tools change fast. Always check the current status of a tool before spending time on installation.

---

## Error 6 — Environment Variables Showing as None


**Symptom:**
```python
DB_SERVER = None
DB_PASSWORD = None
```
All `os.getenv()` calls returned None despite values being in `~/.bashrc`.

**Cause:**
Variables were added to `.bashrc` without the `export` keyword:
```bash
DB_SERVER="value"         # wrong — only available in current shell
export DB_SERVER="value"  # correct — available to child processes
```
Without `export` the variable exists in the shell session but is not passed to child processes like Gunicorn.

**Fix:**
Added `export` keyword to every variable in `.bashrc`:
```bash
export DB_SERVER="customer-inquiry-server.database.windows.net"
```
Then reloaded:
```bash
source ~/.bashrc
```

**Lesson:**
Environment variables must be exported to be visible to processes launched from that shell. Always use `export`.

---

## Error 7 — pyodbc Module Not Found


**Symptom:**
```
ModuleNotFoundError: No module named 'pyodbc'
```
**Cause:**
Running `python app.py` from the system Python instead of the virtual environment. pyodbc was installed inside the venv, not system-wide.

**Fix:**
Always activate the virtual environment first:
```bash
source venv/bin/activate   # or source .venv/bin/activate
python app.py
```

**Lesson:**
The `(venv)` prefix in the terminal prompt confirms the venv is active. If it is missing you are using system Python.

---

## Error 8 — Old app.py Still Running on VM After Deploy


**Symptom:**
Code changes pushed to GitHub and pulled on VM but the old behaviour persisted. New routes returned 404.

**Cause:**
The file was pulled correctly but Gunicorn was still serving the old version loaded at startup. Gunicorn does not hot-reload by default.

**Fix:**
Always restart Gunicorn after pulling new code:
```bash
git pull
sudo pkill gunicorn
source .venv/bin/activate
.venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
```

**Lesson:**
Gunicorn loads the app once at startup. Code changes require a full restart to take effect.

---

## Error 9 — Flask Showing ModuleNotFoundError After Gunicorn Start


**Symptom:**
```
ModuleNotFoundError: No module named 'flask'
[ERROR] Worker failed to boot
```
Gunicorn was running but Flask was not found.

**Cause:**
The system had two virtual environments: `venv` and `.venv`. The wrong Gunicorn binary (from `/usr/lib/python3/dist-packages/gunicorn`) was being called instead of the one inside the venv.

**Fix:**
Always use the full path to the venv Gunicorn binary:
```bash
.venv/bin/gunicorn -w 2 -b 127.0.0.1:8000 app:app
```
Confirm which venv has all packages:
```bash
.venv/bin/pip list | grep -E "Flask|pyodbc|sendgrid|openai"
```

**Lesson:**
When multiple venvs exist use the full binary path to guarantee the correct Python environment is used.

---

## Error 10 — Cron Job Fails With SQL Login Timeout


**Symptom:**
```
[ERROR] Daily summary job failed: Login timeout expired (SQLDriverConnect)
```
The script worked fine when run manually but failed under cron.

**Cause:**
Cron runs in a minimal non-interactive shell with no access to `~/.bashrc`. All environment variables set with `export` in `.bashrc` were invisible to the cron job.

**Fix:**
Added `cd` to the project directory at the start of the cron command so `python-dotenv` could find and load the `.env` file:
```bash
*/2 * * * * cd /home/azureuser/customer-inquiry-manager && \
  /home/azureuser/customer-inquiry-manager/.venv/bin/python \
  /home/azureuser/customer-inquiry-manager/daily_summary.py \
  >> /home/azureuser/customer-inquiry-manager/cron.log 2>&1
```

**Lesson:**
Cron does not source `.bashrc`. Always use full absolute paths and load `.env` with python-dotenv or set vars directly in the crontab.

---

## Error 11 — Azure Functions Fails With KeyError on DB_SERVER


**Symptom:**
```
[ERROR] DailySummary function failed: 'DB_SERVER'
```
**Cause:**
App Settings were added in the Azure portal but the **Apply** and **Confirm** buttons were not clicked. Azure requires an explicit save step — navigating away without confirming discards all changes silently.

**Fix:**
After adding all App Settings:
1. Click **Apply** at the bottom of the page
2. Click **Confirm** in the popup dialog
3. Refresh the page to verify all variables appear in the list

**Lesson:**
Azure portal App Settings have a two-step save process. Changes are lost silently if you navigate away without clicking Apply → Confirm.

---

## Error 12 — Python Not Available on Consumption (Windows) Plan


**Symptom:**
Python was not listed as a runtime stack option when creating the Function App with Consumption (Windows) hosting plan.

**Cause:**
Python is only supported on Linux hosting plans in Azure Functions. The Windows Consumption plan does not support Python.

**Fix:**
Selected **Linux** as the OS when creating the Function App.
Consumption (Linux) has identical pricing and scaling to Consumption (Windows).

**Lesson:**
Always select Linux when creating Python-based Azure Function Apps.

---

## Error 13 — Azure Functions v2 Structure Different From Docs


**Symptom:**
`func new --name DailySummary --template "Timer trigger"` created a flat structure with `function_app.py` instead of a `DailySummary/` subfolder with `__init__.py`.

**Cause:**
Newer versions of Azure Functions Core Tools use the **v2 programming model** by default. The v2 model uses a single `function_app.py` file with decorators instead of separate folders per function.

**Fix:**
Used the v2 decorator syntax in `function_app.py`:
```python
@app.timer_trigger(schedule="0 0 8 * * *", arg_name="mytimer")
def DailySummary(mytimer: func.TimerRequest) -> None:
    ...
```
No `__init__.py` or `function.json` needed in v2.

**Lesson:**
Azure Functions has two programming models. v2 (current default) uses decorators in a single file. v1 uses folder-per-function with `__init__.py`. Check which version your Core Tools generates.

---

## Error 14 — Heartbeat Alert Requires Log Analytics Agent


**Symptom:**
Heartbeat alert was created successfully in Azure Monitor but never fired. The Logs query `Heartbeat | take 10` returned no results.

**Cause:**
The Heartbeat metric only exists if the Azure Monitor Agent is installed on the VM and actively sending data. Creating the alert rule alone is not enough.

**Fix:**
1. Go to VM → Monitoring → Insights (now Monitor)
2. Click Enable and select the Log Analytics workspace
3. Wait 5–10 minutes for the agent to install
4. Verify with: `Heartbeat | take 10` in the Logs query editor

**Lesson:**
Azure Monitor alerts based on Log Analytics data require the monitoring agent to be installed first. The alert rule and the data pipeline are two separate steps.

---

## Error 15 — Azure SQL Login Timeout When Running Locally


**Symptom:**
```
pyodbc.OperationalError: Login timeout expired (SQLDriverConnect)
```
App worked fine on the VM but timed out when running on local machine.

**Cause:**
Azure SQL has its own firewall completely separate from the VM Network Security Group. The VM IP was already whitelisted but the local machine IP was not.

**Fix:**
1. Go to portal.azure.com → SQL servers → your server
2. Security → Networking → Firewall rules
3. Click **Add your client IPv4 address**
4. Click **Save**

**Lesson:**
Azure SQL firewall and VM NSG are completely independent. Adding a rule to one does not affect the other. When connecting from a new machine always check the SQL firewall first.

---

## Summary Table

| # | Error | Day | Root Cause | Fix |
|---|-------|-----|-----------|-----|
| 1 | Port 5000 in use | 3 | Mac AirPlay Receiver | Disable AirPlay or use different port |
| 2 | venv not available | 4 | Ubuntu missing venv package | `apt install python3.12-venv` |
| 3 | Port 8000 in use | 4 | Gunicorn orphan process | `sudo pkill gunicorn` |
| 4 | SQL region capacity | 5 | East US 2 capacity limit | Switch to East US |
| 5 | Azure Data Studio retired | 5 | Deprecated Feb 2026 | Use VS Code mssql extension |
| 6 | Env vars showing None | 6 | Missing `export` keyword | Add `export` to all vars in .bashrc |
| 7 | pyodbc not found | 6 | Wrong Python environment | Activate venv first |
| 8 | Old code on VM | 6 | Gunicorn not restarted | `pkill gunicorn` after every `git pull` |
| 9 | Flask not found in Gunicorn | 15 | Wrong Gunicorn binary | Use `.venv/bin/gunicorn` full path |
| 10 | Cron SQL timeout | 17 | Cron has no .bashrc vars | Use `cd` + python-dotenv in cron command |
| 11 | Azure Functions KeyError | 18 | App Settings not saved | Click Apply → Confirm in portal |
| 12 | Python not in runtime stack | 18 | Windows plan no Python | Select Linux OS for Function App |
| 13 | Functions v2 structure different | 18 | v2 programming model | Use decorator syntax in function_app.py |
| 14 | Heartbeat alert never fired | 20 | No monitoring agent installed | Enable VM Insights first |
| 15 | SQL timeout locally | 22 | SQL firewall blocked local IP | Add local IP to SQL firewall rules |