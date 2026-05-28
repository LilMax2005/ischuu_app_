Write-Host "Preparando empaquetado de Ischuu..." -ForegroundColor Magenta
if (!(Test-Path ".venv")) { py -3.11 -m venv .venv }
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --name IschuuApp main.py
Write-Host "Compilación finalizada. Revisa la carpeta dist/" -ForegroundColor Green
