# Pokretanje projekta

U nastavku sijede koraci pravilne instalacije programa

## 1. Instalacija ovisnosti

Provjeri je li na sustavu instaliran Python (preporučena verzija: Python 3.12 ili novija).

U korijenskoj mapi projekta otvori terminal i instaliraj potrebne biblioteke:

```bash
pip install -r requirements.txt
```

## 2. Konfiguracija API ključeva

Za rad aplikacije potrebno je konfigurirati API ključeve za podržane AI servise.

1. Pronađi datoteku `.env.example` u korijenskoj mapi projekta.
2. Napravi njezinu kopiju i preimenuj je u `.env`.
3. Uredi `.env` datoteku i unesi svoje API ključeve:

```env
API_KEY_GPT=your_openai_api_key
API_KEY_GEMINI=your_gemini_api_key
API_KEY_CLAUDE=your_anthropic_api_key
API_KEY_LLAMA=your_llama_api_key
```

> Napomena: Datoteku `.env` nemoj dodavati u Git repozitorij jer sadrži osjetljive podatke.

## 3. Pokretanje aplikacije

Nakon instalacije ovisnosti i konfiguracije API ključeva, aplikaciju možeš pokrenuti naredbom:



Ako projekt podržava dodatne argumente ili konfiguracijske opcije, one se mogu navesti prilikom pokretanja skripte.

##4. Rješavanje problema pri pokretanju

Prilikom prvog pokretanja aplikacije može se pojaviti pogreška povezana s učitavanjem pojedinih modula ili biblioteka. Ova pojava nije povezana s logikom programa te se najčešće javlja samo pri inicijalnom pokretanju.

Ako dođe do takve pogreške, jednostavno ponovno pokreni aplikaciju u istom terminalu:

```bash
python slanje_dohvat_podataka_final.py
```

U većini slučajeva aplikacija će se nakon ponovnog pokretanja ispravno inicijalizirati i nastaviti s radom bez dodatnih intervencija.
