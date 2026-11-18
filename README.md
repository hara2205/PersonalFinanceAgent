# Personal Finance Agent
## Agent za predviđanje likvidnosti kod korisnika s neredovnim prihodima

 Agent procjenjuje da li korisnik može izmiriti obaveze prije nego što očekivani prihodi postanu dostupni. Predviđa datume prihoda na osnovu historijskih kašnjenja, simulira budući novčani tok i generiše upozorenja o potencijalnom manjku novca.

**GitHub:** https://github.com/hara2205/PersonalFinanceAgent

### Funkcionalnosti
- Evidencija trenutnog stanja računa, očekivanih prihoda i finansijskih obaveza.
- Evidencija očekivanog i stvarnog datuma/iznosa uplata.
- Predviđanje datuma buduće uplate na osnovu historijskog prosječnog kašnjenja za isti izvor prihoda.
- Hronološka simulacija budućih prihoda i obaveza.
- Identifikacija prvog datuma manjka i najvećeg predviđenog manjka.
- Heuristička procjena rizika (LOW / MEDIUM / HIGH).
- Kreiranje, ažuriranje i deaktivacija upozorenja.
- Agentov ciklus Sense → Think → Act → Learn.
- Web korisnički interfejs i REST API.
- Demonstracija promjene odluke prije i poslije dodavanja historijskih podataka.
- Testovi pomoću pytest.

> Učenje u trenutnoj verziji je adaptivno statističko učenje na osnovu historijskih kašnjenja (prosjek). Projekat ne koristi trenirani model mašinskog učenja. Indeks pouzdanosti je heuristički, nije kalibrisana statistička vjerovatnoća.

### Tehnologije
- Python
- FastAPI
- SQLAlchemy
- SQLite
- HTML, CSS, JavaScript
- pytest

### Struktura projekta
```text
PersonalFinanceAgent/
├── app/
│   ├── database.py
│   ├── models.py
│   ├── seed.py
│   ├── income_prediction.py
│   ├── cashflow_service.py
│   ├── decisions.py
│   ├── learning.py
│   ├── agent.py
│   ├── main.py
│   ├── demo_scenario.py
│   └── learning_demo.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/
├── data/
├── requirements.txt
└── PROJECT_SPECIFICATION.md
```

### Pokretanje na Windowsu

1. Instalirati Python (projekat je razvijan i testiran u Python 3.15.2 okruženju).
2. Klonirati repozitorij:
   ```powershell
   git clone https://github.com/hara2205/PersonalFinanceAgent.git
   cd PersonalFinanceAgent
   ```
3. Kreirati virtualno okruženje:
   ```powershell
   py -3.15 -m venv .venv
   ```
   Ako nije instaliran Python 3.15, koristiti instaliranu kompatibilnu verziju Pythona:
   ```powershell
   py -m venv .venv
   ```
4. Aktivirati virtualno okruženje:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   Ako PowerShell blokira aktivaciju skripte, za trenutni terminal može se koristiti:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```
5. Instalirati zavisnosti:
   ```powershell
   pip install -r requirements.txt
   ```
6. Pokrenuti backend i web aplikaciju:
   ```powershell
   uvicorn app.main:app --reload
   ```
7. Otvoriti aplikaciju u pregledniku:
   - UI: http://127.0.0.1:8000/ui
   - API dokumentacija: http://127.0.0.1:8000/docs
   - Health endpoint: http://127.0.0.1:8000/health

Za zaustavljanje servera pritisnuti `Ctrl+C` u terminalu.

### Testiranje

Iz root direktorija projekta, uz aktivirano virtualno okruženje:
```powershell
python -m pytest tests -v
```

Posljednji rezultat u razvojnom okruženju: **27 uspješno izvršenih testova**. Rezultat se može razlikovati ako se promijeni kod ili okruženje.

### Demonstracije agenta

Demonstracija osnovnog scenarija koristi zasebnu demo bazu:
```powershell
python -m app.demo_scenario
```

Demonstracija adaptivnog učenja prije i poslije dodavanja historijskih kašnjenja koristi zasebnu bazu:
```powershell
python -m app.learning_demo
```

Demonstracija učenja prikazuje isti finansijski scenario prije i poslije dodavanja historijskih uplata. U početnom stanju agent nema historiju kašnjenja pa predviđa prihod na očekivani datum. Nakon dodavanja historijskih uplata s kašnjenjem, predviđeni datum se pomjera, agent prepoznaje manjak prije dospijeća obaveze i kreira upozorenje.

Demo skripte koriste izolovane baze kako ne bi mijenjale glavnu bazu aplikacije.

### Agentov ciklus

- **Sense:** prikuplja stanje računa, očekivane i planirane prihode i neizmirene obaveze.
- **Think:** predviđa datume uplata, simulira novčani tok i procjenjuje rizik.
- **Act:** kreira, ažurira ili deaktivira upozorenje.
- **Learn:** analizira realizovane uplate i historijska kašnjenja po izvoru prihoda.

Agent se pokreće ručno putem interfejsa/API-ja, a backend ima i periodično pozadinsko izvršavanje.

