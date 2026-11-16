# Personal Finance Agent
## Agent za predviđanje likvidnosti kod korisnika s neredovnim prihodima

**Verzija:** 2.0  
**Status:** Specifikacija za implementaciju  
**Programski jezik:** Python

## 1. Opis problema

Osobe koje ostvaruju neredovne prihode često imaju problem s planiranjem plaćanja svojih finansijskih obaveza. Čak i kada očekuju određenu uplatu, ona može kasniti nekoliko dana, što može dovesti do nedostatka novca za račune, stanarinu, rate kredita i druge obaveze.

Cilj projekta je razvoj autonomnog softverskog agenta koji prati finansijsko stanje korisnika, analizira očekivane prihode i dospijeće obaveza te predviđa postoji li rizik da korisnik neće imati dovoljno sredstava prije sljedeće uplate.

Za razliku od obične aplikacije za praćenje troškova, agent samostalno izvršava periodične provjere, predviđa kašnjenja prihoda, donosi odluke o upozoravanju korisnika i prilagođava buduće procjene na osnovu stvarnih datuma uplata.

## 2. Osnovni ciljevi

- Evidentiranje trenutnog stanja novca.
- Evidentiranje očekivanih i stvarnih prihoda.
- Evidentiranje finansijskih obaveza i njihovih datuma dospijeća.
- Predviđanje datuma budućih uplata na osnovu historijskih kašnjenja.
- Predviđanje mogućeg nedostatka sredstava.
- Pravovremeno generisanje upozorenja.
- Učenje iz stvarnih datuma pristiglih uplata.
- Prilagođavanje budućih odluka na osnovu prethodnog iskustva.
- Objašnjavanje razloga zbog kojih je agent generisao određeno upozorenje.

## 3. Opseg sistema

Sistem će biti razvijen kao demonstracijska aplikacija za jednog korisnika.

Korisnik može:
- Evidentirati trenutno stanje novca.
- Evidentirati izvore prihoda.
- Unijeti očekivane datume i iznose uplata.
- Evidentirati stvarne datume i iznose pristiglih uplata.
- Evidentirati obaveze, iznose i datume dospijeća.
- Pregledati upozorenja i prognoze agenta.

Sistem neće biti povezan sa stvarnim bankovnim računima i neće automatski izvršavati plaćanja.

Valuta sistema je konvertibilna marka (KM).

## 4. Osnovno ponašanje agenta

Agent kontinuirano radi u pozadini i svakodnevno provjerava finansijsko stanje korisnika.

Njegov rad podijeljen je u četiri faze:

### Sense – Opažanje
Agent prikuplja:
- Trenutno stanje novca.
- Očekivane prihode.
- Historijske datume i iznose uplata.
- Evidentirane finansijske obaveze.
- Datume dospijeća obaveza.

### Think – Razmišljanje
Agent:
- Analizira prethodna kašnjenja prihoda.
- Procjenjuje vjerovatni datum naredne uplate.
- Analizira buduće prilive i odlive novca.
- Identifikuje datume kada bi stanje novca moglo postati nedovoljno za pokrivanje obaveza.
- Procjenjuje pouzdanost svojih predviđanja.

### Act – Djelovanje
Agent samostalno odlučuje:
- Da li postoji rizik nedostatka sredstava.
- Kada treba upozoriti korisnika.
- Koje obaveze su ugrožene.
- Koliki se nedostatak sredstava očekuje.

Upozorenja se čuvaju u bazi i prikazuju korisniku.

### Learn – Učenje
Kada evidentirana uplata stvarno stigne, agent poredi očekivani i stvarni datum.

Na osnovu razlike:
- Ažurira podatke o kašnjenjima pojedinih izvora prihoda.
- Prilagođava procjenu budućih datuma uplata.
- Poboljšava procjenu rizika.
- Prilagođava vrijeme budućih upozorenja.

## 5. Predviđanje kašnjenja prihoda

Svaki očekivani prihod ima:
- Izvor prihoda.
- Očekivani datum.
- Očekivani iznos.
- Stvarni datum uplate, kada uplata stigne.
- Stvarni iznos, kada je poznat.

Kašnjenje se računa kao razlika između stvarnog i očekivanog datuma uplate.

Agent vodi historiju kašnjenja za svaki izvor prihoda.

Za početnu implementaciju koristit ćemo statističku analizu historijskih kašnjenja, uključujući prosjek, medijanu i varijabilnost. Kada postoji dovoljno podataka, koristit ćemo odgovarajući model mašinskog učenja za predviđanje budućeg kašnjenja.

Ako nema dovoljno historijskih podataka, agent će koristiti očekivani datum uz niži nivo pouzdanosti.

## 6. Predviđanje finansijskog rizika

Agent analizira buduće stanje novca na osnovu:

- Trenutnog stanja.
- Očekivanih prihoda i procijenjenih datuma njihovog pristizanja.
- Iznosa i datuma dospijeća obaveza.

Na osnovu vremenskog slijeda priliva i odliva agent procjenjuje da li će stanje novca u nekom trenutku postati nedovoljno za pokrivanje dospjelih obaveza.

Posebno će prikazivati:
- Očekivani datum nedostatka sredstava.
- Očekivani iznos nedostatka.
- Obaveze koje doprinose riziku.
- Procijenjeni datum sljedeće uplate.
- Pouzdanost procjene.

Očekivane uplate neće se tretirati kao siguran novac. Agent će uzimati u obzir mogućnost kašnjenja.

## 7. Povratne informacije i prilagođavanje

Sistem će evidentirati:
- Očekivani datum uplate.
- Stvarni datum uplate.
- Predviđeno kašnjenje.
- Stvarno kašnjenje.
- Prethodno generisana upozorenja.
- Rezultat prethodnih predviđanja.

Na osnovu ovih podataka agent prilagođava buduće procjene.

Cilj je demonstrirati da agent nakon učenja iz prethodnih kašnjenja može ranije prepoznati budući rizik i promijeniti vrijeme upozoravanja.

## 8. Demonstracijski podaci

Sistem će koristiti automatski generisane simulirane podatke.

Podaci će obuhvatati:
- Više izvora prihoda.
- Različite očekivane datume uplata.
- Simulirana kašnjenja uplata.
- Mjesečne i jednokratne finansijske obaveze.
- Različite iznose i datume dospijeća.

Simulacija će omogućiti demonstraciju ponašanja agenta prije i nakon učenja iz prethodnih uplata.

## 9. Arhitektura

Sistem će koristiti jedan glavni FinancialAgentRunner koji se automatski pokreće zajedno sa FastAPI backend aplikacijom.

Runner izvršava metodu `step()`, pri čemu svaki Tick predstavlja jednu iteraciju agenta.

Obrada će se pokretati:
- Svakodnevno radi provjere finansijskog stanja.
- Nakon evidentiranja nove uplate.
- Nakon promjene obaveze ili očekivanog prihoda.
- Nakon drugih relevantnih finansijskih događaja.

API sloj služi za komunikaciju s frontend aplikacijom. Centralna logika donošenja odluka nalazi se u Agent Core komponenti.

Agent se izvršava pomoću Python asyncio mehanizma i uredno se zaustavlja pri gašenju backend aplikacije.

## 10. Tehnologije

| Tehnologija | Namjena |
|---|---|
| Python | Glavni programski jezik |
| FastAPI | Backend |
| HTML, CSS, JavaScript | Frontend |
| SQLite | Baza podataka |
| SQLAlchemy | Rad s bazom |
| pandas | Obrada podataka |
| scikit-learn | Mašinsko učenje |
| asyncio | Pozadinski rad agenta |
| Chart.js | Grafički prikaz |
| pytest | Testiranje |
| GitHub | Verzionar projekta |

## 11. Predložene komponente

- `main.py` – pokretanje backend aplikacije.
- `agent.py` – centralna logika agenta.
- `runner.py` – kontinuirano izvršavanje Tick iteracija.
- `decisions.py` – pravila donošenja odluka.
- `models.py` – modeli baze podataka.
- `income_service.py` – upravljanje prihodima.
- `obligation_service.py` – upravljanje obavezama.
- `cashflow_service.py` – analiza budućeg stanja novca.
- `income_prediction.py` – predviđanje kašnjenja uplata.
- `database/` – povezivanje i rad s bazom.
- `api/` – HTTP endpointi.

## 12. Testiranje

Planirani testni scenariji:

1. Korisnik ima dovoljno novca za sve obaveze.
2. Očekivana uplata kasni i dolazi do rizika nedostatka novca.
3. Agent predviđa datum mogućeg nedostatka sredstava.
4. Agent generiše upozorenje prije dospijeća ugrožene obaveze.
5. Stvarna uplata stigne kasnije od očekivane.
6. Agent evidentira kašnjenje i prilagođava narednu procjenu.
7. Agent nakon učenja ranije prepoznaje isti ili sličan rizik.
8. Agent nema dovoljno historijskih podataka i prikazuje nižu pouzdanost.
9. Agent nema novih događaja i završava Tick bez nepotrebnog rada.
10. Isti događaj ne proizvodi duplirana upozorenja.

## 13. Očekivani rezultat

Rezultat projekta je funkcionalna web aplikacija sa autonomnim softverskim agentom koji predviđa rizik nedostatka novca kod korisnika s neredovnim prihodima.

Glavna demonstracija projekta bit će poređenje ponašanja agenta prije i nakon učenja iz historijskih kašnjenja uplata.

Agent će pokazati kako iskustvo mijenja njegove buduće procjene i odluke o pravovremenom upozoravanju korisnika.