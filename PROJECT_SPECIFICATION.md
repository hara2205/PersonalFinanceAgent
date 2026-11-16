# Personal Finance Agent
## Projektna specifikacija

**Naziv projekta:** Personal Finance Agent – Inteligentni agent za upravljanje ličnim finansijama  
**Verzija dokumenta:** 1.0  
**Status:** Početna specifikacija  
**Programski jezik:** Python

---

## 1. Opis projekta

Personal Finance Agent je inteligentni softverski agent namijenjen praćenju, analizi i optimizaciji ličnih finansija korisnika.

Sistem omogućava evidentiranje prihoda i rashoda, definisanje mjesečnih budžeta i ciljeva štednje. Na osnovu prikupljenih podataka agent kontinuirano analizira finansijsko stanje korisnika, prepoznaje obrasce potrošnje, predviđa moguće prekoračenje budžeta i generiše personalizovane preporuke.

Za razliku od obične aplikacije za evidentiranje troškova, agent samostalno prati promjene, obrađuje nove događaje, donosi odluke i prilagođava prioritete svojih preporuka na osnovu povratnih informacija korisnika.

Sistem je namijenjen demonstraciji principa autonomnih softverskih agenata i primjene mašinskog učenja u oblasti ličnih finansija.

## 2. Ciljevi projekta

Glavni ciljevi su:

- Omogućiti jednostavno evidentiranje prihoda i rashoda.
- Pratiti ukupne i kategorijske budžete.
- Omogućiti definisanje ciljeva štednje.
- Kontinuirano analizirati finansijsko stanje korisnika.
- Predviđati buduću potrošnju.
- Prepoznavati neuobičajene transakcije.
- Generisati upozorenja i personalizovane preporuke.
- Prikupljati povratne informacije korisnika.
- Prilagođavati prioritete preporuka na osnovu prethodnih rezultata.
- Objasniti razloge zbog kojih je agent donio određenu odluku.

## 3. Opseg i ograničenja sistema

Sistem će biti razvijen kao demonstracijska aplikacija za jednog korisnika.

Osnovna ograničenja:

- Podržana valuta je konvertibilna marka (KM/BAM).
- Transakcije se unose ručno ili se učitavaju kao unaprijed generisani demonstracijski podaci.
- Neće postojati povezivanje sa stvarnim bankovnim računima.
- Sistem neće izvršavati finansijske transakcije.
- Agent će pružati informativne analize i preporuke, a konačne odluke ostaju na korisniku.
- Neće biti implementiran sistem registracije i prijave više korisnika.

## 4. Funkcionalni zahtjevi

### 4.1. Upravljanje transakcijama

Korisnik može:

- Dodati prihod ili rashod.
- Izmijeniti postojeću transakciju.
- Izbrisati transakciju.
- Odabrati kategoriju.
- Unijeti iznos, datum i opis.
- Pregledati i filtrirati transakcije.

Svaka transakcija sadrži iznos, tip, kategoriju, datum, opis i opcionalnu napomenu.

### 4.2. Upravljanje budžetima

Korisnik može definisati:

- Ukupni mjesečni budžet.
- Budžete za pojedinačne kategorije.
- Ciljeve štednje i željeni iznos.

Sistem prati ostvarenu potrošnju i napredak prema definisanim ciljevima.

### 4.3. Inteligentni agent

Agent automatski:

- Analizira nove transakcije.
- Prati potrošnju u odnosu na budžete.
- Predviđa ukupne rashode do kraja mjeseca.
- Detektuje neuobičajene transakcije.
- Identifikuje kategorije sa povećanom potrošnjom.
- Kreira upozorenja i preporuke.
- Evidentira svoje odluke i objašnjenja.

### 4.4. Povratne informacije

Korisnik može prihvatiti ili odbiti preporuku.

Za prihvaćenu preporuku korisnik naknadno može potvrditi da li ju je primijenio.

Sistem evidentira povratne informacije i prati promjene relevantnih troškova u narednom periodu.

### 4.5. Analitika

Aplikacija omogućava:

- Pregled prihoda i rashoda.
- Grafički prikaz potrošnje po kategorijama.
- Poređenje različitih mjeseci.
- Pregled prognozirane potrošnje.
- Pregled ciljeva štednje.
- Historiju upozorenja i preporuka.
- Pregled prethodnih odluka agenta.

## 5. Kategorije transakcija

Predviđene kategorije prihoda:

- Plata.
- Stipendija.
- Freelance/honorar.
- Ostalo.

Predviđene kategorije rashoda:

- Hrana.
- Stanovanje.
- Prijevoz.
- Zdravlje.
- Odjeća.
- Restorani.
- Zabava.
- Računi.
- Obrazovanje.
- Ostalo.

Kategorije će biti moguće proširivati.

## 6. Demonstracijski podaci

Sistem će automatski generisati simulirane transakcije koje predstavljaju realistične finansijske aktivnosti.

Podaci će obuhvatati prihode i rashode za najmanje šest prethodnih mjeseci, kako bi agent imao historiju potrebnu za analizu i demonstraciju predviđanja.

Demonstracijski podaci bit će jasno označeni i odvojeni od transakcija koje korisnik sam unese.

## 7. Inteligentno ponašanje agenta

Agent koristi kombinaciju pravila odlučivanja i mašinskog učenja.

### 7.1. Praćenje budžeta

Početni pragovi upozorenja:

- 70% iskorištenog budžeta: informativno upozorenje.
- 90% iskorištenog budžeta: upozorenje visokog prioriteta.
- Prekoračenje budžeta: upozorenje o prekoračenju.

Pragovi će biti konfigurabilni.

Agent će sprječavati nepotrebno ponavljanje istih upozorenja.

### 7.2. Predviđanje potrošnje

Model mašinskog učenja analizira historijske transakcije i trenutnu potrošnju kako bi procijenio ukupne rashode do kraja mjeseca.

Ako prognoza ukazuje na vjerovatno prekoračenje budžeta, agent može generisati preventivnu preporuku.

### 7.3. Detekcija anomalija

Model za detekciju anomalija prepoznaje transakcije koje značajno odstupaju od uobičajenog ponašanja korisnika.

Planirana je primjena algoritma Isolation Forest.

Neuobičajena transakcija neće automatski biti označena kao pogrešna ili prevara, već će biti prikazana korisniku radi provjere.

### 7.4. Personalizacija preporuka

Agent evidentira prihvatanje i odbijanje preporuka, kao i naknadnu potvrdu njihove primjene.

Na osnovu prethodnih rezultata prilagođava prioritete budućih preporuka.

Personalizacija će u početnoj verziji koristiti jednostavan mehanizam prilagođavanja bodovanja preporuka, bez nepotrebno složenih algoritama.

## 8. Arhitektura agenta

Sistem će koristiti jedan glavni FinancialAgentRunner koji se pokreće automatski zajedno sa backend aplikacijom.

Runner kontinuirano izvršava metodu `step()`, pri čemu svaki Tick predstavlja jednu prepoznatljivu iteraciju agenta.

Jedan Tick obuhvata:

1. Sense – preuzimanje događaja i prikupljanje relevantnih podataka.
2. Think – analiza podataka, primjena pravila i ML modela te donošenje odluke.
3. Act – kreiranje upozorenja, preporuke ili druge odgovarajuće akcije.
4. Learn – obrada povratnih informacija i ažuriranje personalizacije kada postoje odgovarajući podaci.

Learn nije obavezan dio svakog Tick-a. Izvršava se kada postoje nove povratne informacije ili kada su ispunjeni uslovi za ažuriranje modela.

Runner neće sadržavati HTTP, routing ili korisničke interfejsne odgovornosti.

API sloj služi za komunikaciju sa frontend aplikacijom, dok se odluke o ponašanju agenta nalaze u centralnoj logici.

### 8.1. Obrada događaja

Agent reaguje na događaje kao što su:

- Dodavanje, izmjena ili brisanje transakcije.
- Promjena budžeta.
- Kreiranje cilja štednje.
- Nova povratna informacija korisnika.
- Periodična provjera finansijskog stanja.

Događaji će se evidentirati u bazi i obrađivati kroz Runner.

Sistem će koristiti identifikatore događaja i evidenciju obrade kako bi se smanjila mogućnost dupliranja akcija.

### 8.2. Pokretanje i zaustavljanje

Agent se pokreće automatski prilikom pokretanja FastAPI backend aplikacije.

Za upravljanje pozadinskim izvršavanjem koristit će se Python asyncio i FastAPI lifespan mehanizam.

Pri gašenju backend aplikacije agent će biti uredno zaustavljen.

### 8.3. Učenje i ponovno treniranje

Ažuriranje personalizacije i ponovno treniranje ML modela neće se izvršavati nakon svake pojedinačne povratne informacije.

Sistem će periodično provjeravati postoje li uslovi za novo treniranje, uz minimalni broj novih relevantnih podataka.

## 9. Tehnologije

| Tehnologija | Namjena |
|---|---|
| Python | Glavni programski jezik |
| FastAPI | Backend i REST API |
| HTML | Struktura korisničkog interfejsa |
| CSS | Stilizacija interfejsa |
| JavaScript | Interakcija sa backendom |
| SQLite | Relacijska baza podataka |
| scikit-learn | Algoritmi mašinskog učenja |
| pandas | Obrada i analiza podataka |
| Chart.js | Grafički prikaz finansijskih podataka |
| asyncio | Pozadinsko izvršavanje agenta |
| Git i GitHub | Verzionar i praćenje razvoja |

## 10. Predložena struktura projekta

```text
PersonalFinanceAgent/
│
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   ├── agent.py
│       │   ├── runner.py
│       │   └── decisions.py
│       ├── database/
│       │   ├── connection.py
│       │   └── models.py
│       ├── services/
│       │   ├── transaction_service.py
│       │   ├── budget_service.py
│       │   └── recommendation_service.py
│       ├── ml/
│       │   ├── forecasting.py
│       │   ├── anomaly_detection.py
│       │   └── recommendation_learning.py
│       └── api/
│           ├── transactions.py
│           ├── budgets.py
│           └── agent.py
│
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
│
├── data/
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

Struktura će se razvijati postepeno, u skladu sa implementacijom.

## 11. Testiranje

Planirani testni scenariji:

- Dodavanje i izmjena transakcija.
- Ispravno izračunavanje potrošnje i budžeta.
- Generisanje upozorenja na definisanim pragovima.
- Predviđanje mogućeg prekoračenja budžeta.
- Detekcija neuobičajenih transakcija.
- Obrada događaja bez dupliranja akcija.
- Sigurno završavanje Tick-a kada nema posla.
- Evidentiranje korisničkih povratnih informacija.
- Prilagođavanje prioriteta preporuka.
- Provjera ponašanja sistema u slučaju nedostatka podataka ili greške ML modela.

Rezultati ML modela bit će evaluirani na odgovarajućim testnim podacima, bez pretpostavke da je svaka prognoza tačna.

## 12. Plan razvoja

Razvoj će se odvijati u sljedećim fazama:

1. Priprema Python okruženja i projekta.
2. Implementacija baze podataka.
3. Implementacija osnovnog backend API-ja.
4. Implementacija Agent Core logike i Runnera.
5. Implementacija prognoze potrošnje.
6. Implementacija detekcije anomalija.
7. Implementacija personalizacije i povratnih informacija.
8. Implementacija frontend interfejsa.
9. Testiranje i priprema demonstracije.

Svaka veća faza bit će evidentirana kroz Git commitove.

## 13. Očekivani rezultat

Konačni rezultat je funkcionalna web aplikacija koja omogućava korisniku upravljanje ličnim finansijama i demonstrira rad autonomnog softverskog agenta.

Agent će kontinuirano pratiti finansijske događaje, analizirati podatke, donositi odluke, izvršavati odgovarajuće akcije i prilagođavati preporuke na osnovu povratnih informacija.

Poseban naglasak bit će na jasnom prikazu ciklusa Sense → Think → Act → Learn, objašnjivosti odluka i razdvajanju poslovne logike od API i korisničkog interfejsa.
