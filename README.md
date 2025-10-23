Playwright Python minimal scaffold

Quick start (PowerShell):

```powershell
cd c:\Users\david\Documents\Projects\Python\Automation
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# install browsers
python -m playwright install
# run tests
pytest -q
# generate playwright script using codegen
python -m playwright codegen https://siyakhokha.ekurhuleni.gov.za// --target python --output scripts/animePahe.py
```
