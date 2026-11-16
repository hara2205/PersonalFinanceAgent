# Personal Finance Agent
## Agent za predviđanje manjka sredstava kod korisnika s neredovnim prihodima

**Verzija:** 3.0  
**Status:** Implementirana demonstracijska aplikacija  
**Programski jezik:** Python  
**Valuta:** Konvertibilna marka (KM)

---

## 1. Opis problema

Osobe koje ostvaruju neredovne prihode često imaju problem s planiranjem plaćanja svojih finansijskih obaveza. Čak i kada očekuju određenu uplatu, ona može kasniti nekoliko dana, što može dovesti do nedostatka novca za račune, stanarinu, rate kredita i druge obaveze.

Cilj projekta je razvoj autonomnog softverskog agenta koji prati finansijsko stanje korisnika, analizira očekivane prihode i dospijeće obaveza te predviđa postoji li rizik da korisnik neće imati dovoljno sredstava prije pristizanja naredne uplate.

Za razliku od obične aplikacije za praćenje troškova, agent samostalno izvršava periodične provjere, predviđa kašnjenja prihoda na osnovu prethodnih uplata, donosi odluke o upozoravanju korisnika i prilagođava buduće procjene na osnovu novih podataka.

Poseban fokus projekta je na predviđanju likvidnosti, odnosno mogućnosti korisnika da pravovremeno izmiri svoje obaveze uprkos neredovnim datumima pristizanja prihoda.

## 2. Osnovni ciljevi

Osnovni ciljevi sistema su:

- Evidentiranje trenutnog stanja novca.
- Evidentiranje očekivanih i stvarnih prihoda.
- Evidentiranje finansijskih obaveza i njihovih datuma dospijeća.
- Praćenje kašnjenja za svaki izvor prihoda zasebno.
- Predviđanje datuma budućih uplata na osnovu historijskih kašnjenja.
- Hronološka simulacija budućih priliva i odliva novca.
- Predviđanje mogućeg nedostatka sredstava.
- Pravovremeno generisanje upozorenja.
- Prilagođavanje budućih predviđanja na osnovu novih stvarnih uplata.
- Objašnjavanje razloga zbog kojih je agent generisao određeno upozorenje.

## 3. Opseg sistema

Sistem je razvijen kao demonstracijska web aplikacija za jednog korisnika.

Korisnik može:

- Pregledati trenutno stanje novca.
- Evidentirati očekivane prihode.
- Unijeti izvor prihoda, očekivani datum i iznos.
- Evidentirati stvarni datum i iznos pristigle uplate.
- Evidentirati finansijske obaveze.
- Pregledati očekivane prihode i neplaćene obaveze.
- Pregledati prognozu budućeg novčanog toka.
- Pregledati upozorenja koja generiše agent.
- Ručno pokrenuti novu analizu finansijskog stanja.

Sistem nije povezan sa stvarnim bankovnim računima i ne izvršava automatska plaćanja.

Valuta sistema je konvertibilna marka (KM).

## 4. Arhitektura i ponašanje agenta

Centralna komponenta sistema je `FinancialAgentRunner`, implementirana u datoteci `app/agent.py`.

Agent se automatski pokreće zajedno sa FastAPI backend aplikacijom i periodično izvršava provjeru finansijskog stanja. Pored periodičnih provjera, analiza se pokreće i nakon relevantnih promjena finansijskih podataka.

Rad agenta organizovan je kroz četiri faze:

### 4.1. Sense – Opažanje

Agent prikuplja podatke iz baze:

- Trenutno stanje novca.
- Očekivane prihode.
- Zakazane buduće uplate.
- Historijske datume očekivanih i stvarnih uplata.
- Evidentirane finansijske obaveze.
- Datume dospijeća obaveza.

Prikupljeni podaci predstavljaju trenutno finansijsko stanje na osnovu kojeg agent izvršava narednu fazu.

### 4.2. Think – Analiza i predviđanje

Agent:

- Analizira historijska kašnjenja za svaki izvor prihoda.
- Predviđa datum pristizanja očekivanih uplata.
- Analizira buduće prilive i odlive novca.
- Simulira stanje računa kroz vremenski slijed događaja.
- Identifikuje prvi datum na koji stanje novca postaje negativno.
- Izračunava najveći predviđeni nedostatak sredstava.
- Procjenjuje nivo finansijskog rizika i pouzdanost predviđanja.

### 4.3. Act – Djelovanje

Na osnovu rezultata analize agent samostalno odlučuje da li postoji rizik nedostatka sredstava.

Ako prepozna rizik:

- Identifikuje datum prvog predviđenog manjka.
- Određuje obavezu koja izaziva prvi manjak.
- Izračunava očekivani nedostatak sredstava.
- Procjenjuje nivo rizika.
- Generiše upozorenje i preporuku korisniku.

Upozorenja se čuvaju u bazi podataka. Postojeća aktivna upozorenja mogu se ažurirati, a upozorenja se deaktiviraju kada predviđeni manjak više ne postoji.

### 4.4. Learn – Učenje

Agent koristi podatke o stvarno pristiglim uplatama kako bi prilagodio buduća predviđanja.

Za svaku uplatu čuva se:

- Izvor prihoda.
- Očekivani datum uplate.
- Stvarni datum uplate.
- Očekivani iznos.
- Stvarni iznos.
- Izračunato kašnjenje u danima.

Na osnovu historijskih uplata agent ponovo izračunava prosječno kašnjenje za odgovarajući izvor prihoda.

Kada stigne nova uplata, ona postaje dio historije i utiče na naredna predviđanja.

## 5. Predviđanje kašnjenja prihoda

Svaki prihod sadrži sljedeće podatke:

- Izvor prihoda.
- Očekivani datum.
- Očekivani iznos.
- Stvarni datum uplate, kada je poznat.
- Stvarni iznos, kada je poznat.
- Status uplate.

Kašnjenje se računa kao razlika između stvarnog i očekivanog datuma uplate:

**Kašnjenje = Stvarni datum − Očekivani datum**

Za početnu implementaciju koristi se statistička metoda zasnovana na historijskom prosječnom kašnjenju.

Predviđeni datum buduće uplate dobija se dodavanjem procijenjenog kašnjenja na očekivani datum.

Predviđeno kašnjenje ne može biti negativno, pa se ranije pristigle uplate ne koriste za predviđanje ranijeg datuma od očekivanog.

Medijana i broj historijskih uplata koriste se kao dodatne informacije pri analizi predviđanja.

Ako nema historijskih podataka za određeni izvor prihoda, agent koristi očekivani datum uplate i prikazuje niži nivo pouzdanosti.

Pouzdanost predviđanja određuje se heuristički na osnovu broja dostupnih historijskih uplata. Ona ne predstavlja statistički kalibrisanu vjerovatnoću.

## 6. Predviđanje finansijskog rizika

Agent analizira buduće stanje novca na osnovu:

- Trenutnog stanja računa.
- Očekivanih prihoda i njihovih predviđenih datuma.
- Zakazanih budućih uplata.
- Iznosa i datuma dospijeća obaveza.

Svi finansijski događaji organizuju se hronološki i koriste za simulaciju budućeg stanja računa.

Pri događajima koji se odvijaju istog dana, finansijske obaveze obrađuju se prije uplata. Na taj način agent koristi konzervativniju procjenu i ne pretpostavlja da će uplata nužno stići prije dospijeća obaveze.

Agent posebno prikazuje:

- Početno stanje računa.
- Predviđene prilive i odlive.
- Promjene stanja računa kroz vrijeme.
- Datum prvog predviđenog manjka.
- Najveći predviđeni nedostatak sredstava.
- Obavezu koja izaziva prvi manjak.
- Procijenjeni nivo rizika.

Očekivani prihod ne tretira se kao siguran novac. Njegov datum pristizanja prilagođava se na osnovu historijskih kašnjenja.

## 7. Procjena rizika i upozorenja

Agent koristi pravila za klasifikaciju finansijskog rizika na tri nivoa:

- **Nizak rizik:** manjak sredstava nije neposredan i iznos manjka nije velik.
- **Srednji rizik:** približava se datum manjka ili je iznos nedostatka značajan.
- **Visok rizik:** manjak se očekuje u kratkom roku ili je njegov iznos veoma velik.

Klasifikacija se zasniva na broju dana do prvog manjka i iznosu predviđenog nedostatka.

Upozorenje sadrži informacije o datumu manjka, iznosu nedostajućih sredstava, ugroženoj obavezi, nivou rizika i preporuci za korisnika.

Sistem izbjegava nepotrebno kreiranje dupliranih aktivnih upozorenja i ažurira postojeće upozorenje kada je to potrebno.

## 8. Povratne informacije i demonstracija učenja

Glavni cilj učenja je pokazati kako prethodna iskustva mijenjaju buduće odluke agenta.

Za demonstraciju je implementiran kontrolisani scenario koji koristi zasebnu SQLite bazu podataka.

Scenario koristi iste finansijske podatke prije i poslije učenja:

- Početno stanje: 1.000 KM.
- Očekivana plata: 1.500 KM.
- Očekivani datum plate: četvrti dan scenarija.
- Finansijska obaveza: 1.200 KM.
- Datum dospijeća obaveze: peti dan scenarija.

### 8.1. Odluka prije učenja

Agent nema historijske podatke o kašnjenju plate.

Zbog toga koristi očekivani datum uplate.

Plata se predviđa prije dospijeća računa, pa agent ne prepoznaje manjak sredstava i ne generiše upozorenje.

### 8.2. Dodavanje novog iskustva

Agent dobija tri historijske uplate istog izvora prihoda.

Svaka od njih kasnila je tri dana.

Na osnovu novih podataka prosječno kašnjenje iznosi tri dana.

### 8.3. Odluka nakon učenja

Agent ponovo analizira potpuno iste finansijske podatke.

Ovaj put predviđa da će plata stići tri dana nakon očekivanog datuma.

Račun dospijeva prije pristizanja plate, pa stanje računa postaje negativno za 200 KM.

Agent prepoznaje manjak, procjenjuje finansijski rizik i samostalno generiše upozorenje.

### 8.4. Rezultat demonstracije

Demonstracija potvrđuje da dodavanje novih historijskih iskustava mijenja predviđeni datum buduće uplate i može dovesti do drugačije odluke agenta.

Učenje se realizuje statističkim prilagođavanjem na osnovu novih historijskih podataka, bez treniranja posebnog modela mašinskog učenja.

## 9. Tehnička arhitektura

Sistem je organizovan u tri osnovna sloja:

**Frontend:** Web interfejs za unos i pregled finansijskih podataka.

**Backend:** FastAPI aplikacija koja obrađuje zahtjeve, upravlja podacima i pokreće agenta.

**Agent Core:** Komponente koje prikupljaju podatke, predviđaju prihode, analiziraju novčani tok i donose odluke.

Centralna klasa `FinancialAgentRunner` povezuje četiri faze rada agenta.

Pozadinski rad realizovan je pomoću Python `asyncio` mehanizma. Agent periodično izvršava provjere, a backend omogućava i pokretanje analize nakon relevantnih finansijskih promjena.

## 10. Korištene tehnologije

| Tehnologija | Namjena |
|---|---|
| Python | Glavni programski jezik |
| FastAPI | Backend i REST API |
| HTML | Struktura korisničkog interfejsa |
| CSS | Stilizacija korisničkog interfejsa |
| JavaScript | Interaktivnost frontend aplikacije |
| SQLite | Relacijska baza podataka |
| SQLAlchemy | ORM i komunikacija s bazom |
| asyncio | Pozadinsko izvršavanje agenta |
| pytest | Automatizovano testiranje |
| Git i GitHub | Verzionar i upravljanje izvornim kodom |

## 11. Struktura projekta

Glavne komponente implementacije:

- `app/main.py` – FastAPI aplikacija, API endpointi i pozadinsko pokretanje agenta.
- `app/agent.py` – centralna klasa `FinancialAgentRunner` i Sense–Think–Act–Learn ciklus.
- `app/models.py` – modeli baze podataka.
- `app/database.py` – povezivanje s bazom i upravljanje sesijama.
- `app/income_prediction.py` – predviđanje datuma uplata na osnovu historijskih kašnjenja.
- `app/cashflow_service.py` – hronološka simulacija budućeg novčanog toka.
- `app/decisions.py` – procjena rizika i upravljanje upozorenjima.
- `app/learning.py` – demonstracija prilagođavanja predviđanja novim historijskim podacima.
- `app/demo_scenario.py` – demonstracijski scenario finansijskog stanja.
- `app/learning_demo.py` – poređenje odluka prije i poslije učenja.
- `frontend/` – HTML, CSS i JavaScript datoteke korisničkog interfejsa.
- `tests/` – automatizovani testovi sistema.
- `data/` – SQLite baze podataka.

Demonstracijski scenariji koriste odvojene baze kako bi se izbjegla izmjena glavnih korisničkih podataka.

## 12. Testiranje

Sistem je testiran pomoću biblioteke `pytest`.

Implementirani testovi obuhvataju:

1. Prikupljanje finansijskih podataka u Sense fazi.
2. Učenje iz stvarno pristiglih uplata.
3. Provjeru ponašanja agenta kada stanje računa nije evidentirano.
4. Izvršavanje kompletnog agentnog ciklusa.
5. Ispravno funkcionisanje API endpointa.
6. Prikaz finansijskog pregleda.
7. Predviđanje budućeg novčanog toka.
8. Prepoznavanje finansijskog manjka.
9. Obradu obaveza prije prihoda koji stižu istog dana.
10. Prepoznavanje privremenog manjka prije kasnije uplate.
11. Kreiranje upozorenja kada se prepozna manjak.
12. Ažuriranje postojećih upozorenja.
13. Deaktiviranje upozorenja kada manjak nestane.
14. Procjenu niskog, srednjeg i visokog rizika.
15. Predviđanje bez historijskih podataka.
16. Predviđanje na osnovu prosječnog kašnjenja.
17. Razdvajanje historijskih podataka po izvoru prihoda.
18. Prilagođavanje predviđanja nakon nove zakašnjele uplate.
19. Obradu zakazanih budućih uplata.

**Rezultat testiranja:** 27 uspješno izvršenih testova.

## 13. Ograničenja sistema

Trenutna implementacija ima nekoliko ograničenja:

- Sistem je namijenjen jednom korisniku.
- Podaci se unose ručno i nisu povezani s bankovnim računima.
- Predviđanje kašnjenja zasniva se na historijskom prosjeku, a ne na treniranom modelu mašinskog učenja.
- Pouzdanost predviđanja je heuristička procjena.
- Tačnost predviđanja zavisi od količine i kvaliteta historijskih podataka.
- Sistem ne izvršava plaćanja i ne garantuje da će predviđene uplate zaista stići.

## 14. Moguća buduća unapređenja

Sistem se može unaprijediti kroz:

- Uvođenje naprednijih statističkih i mašinskih modela za predviđanje kašnjenja.
- Analizu varijabilnosti i trendova kašnjenja.
- Podršku za više korisnika.
- Automatski uvoz finansijskih podataka iz bankovnih sistema.
- Naprednije metode procjene pouzdanosti predviđanja.
- Dodatne vizualizacije i izvještaje o historijskim prognozama.

Ove mogućnosti nisu dio trenutne implementacije.

## 15. Zaključak

Personal Finance Agent predstavlja demonstracijsku implementaciju autonomnog softverskog agenta za predviđanje manjka sredstava kod korisnika s neredovnim prihodima.

Sistem objedinjuje prikupljanje finansijskih podataka, statističko predviđanje datuma uplata, simulaciju budućeg novčanog toka, procjenu finansijskog rizika i generisanje upozorenja.

Najvažnija karakteristika sistema je sposobnost prilagođavanja budućih predviđanja na osnovu stvarnih datuma prethodnih uplata.

Demonstracija prije i poslije učenja pokazuje da nova historijska iskustva mogu promijeniti predviđeni datum prihoda, otkriti ranije neprepoznat finansijski manjak i dovesti do samostalnog generisanja upozorenja.

Na taj način projekat demonstrira praktičnu primjenu agentnog pristupa u rješavanju problema upravljanja likvidnošću kod korisnika s neredovnim prihodima.