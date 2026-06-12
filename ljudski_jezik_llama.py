import json
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(script_dir, 'data.json')
from groq import Groq

#from sentence_transformers import SentenceTransformer  
try:
    client = Groq(
        api_key=os.getenv("API_KEY_LLAMA") # <--- UNESITE SVOJ KLJUČ OVDJE
    )
    # Brza provjera radi li ključ
    client.models.list() 
    print("Groq klijent uspješno inicijaliziran s ključem iz koda.")
except Exception as e:
    print(f"Greška pri inicijalizaciji Groq klijenta: {e}")
    print("Jeste li unijeli ispravan API ključ u kod?")
    exit()

with open(data_path, 'r', encoding='utf-8') as f:
    BANKA_PRIMJERA = json.load(f)

PROMPT_TEMPLATE = """
You are an expert programmer specialized in translating natural language into SPARQL queries.
Your task is to generate a valid SPARQL query for the EU Open Data Portal based on the user's question.
Use Virtuoso SPARQL endpoint syntax and standard prefixes.
The input question (pitanje) will be written in Croatian. However, always generate the SPARQL query using English keywords because the database primarily supports English.
If the question is sent in any other language, still generate the query in English.
For example, filter uses only english words like forest, energy, sea, ocean...

═══════════════════════════════════════
MANDATORY PREFIXES (always include all that are used):
═══════════════════════════════════════
PREFIX dcat: <http://www.w3.org/ns/dcat#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX foaf: <http://xmlns.com/foaf/0.1/>

═══════════════════════════════════════
CORE STRUCTURE:
═══════════════════════════════════════
Every dataset is: ?dataset a dcat:Dataset .

FIELDS:
- Title:         ?dataset dct:title ?title .
- Description:   ?dataset dct:description ?description .
- Date issued:   ?dataset dct:issued ?issued .
- Date modified: ?dataset dct:modified ?modified .
- Publisher:     ?dataset dct:publisher ?publisher .
                 ?publisher foaf:name ?publisherName .
- Format:        ?dataset dcat:distribution ?dist .
                 ?dist dct:format ?format .
- Theme:         ?dataset dcat:theme ?theme .
- Language:      ?dataset dct:language ?language .
Use these when user asks you for them, but do NOT use them in the query if user does not ask for them

═══════════════════════════════════════
IMPORTANT RULES FOR VIRTUOSO SPARQL:
═══════════════════════════════════════
✓ Use LCASE() instead of LOWER() or LOWERCASE()
✓ Text search:  FILTER(CONTAINS(LCASE(STR(?title)), "keyword"))
✓ Description:  FILTER(CONTAINS(LCASE(STR(?description)), "keyword"))
✓ Language:     FILTER(LANG(?title) = "en")
✓ Date range:   FILTER(?issued >= "2020-01-01"^^xsd:date && ?issued <= "2023-12-31"^^xsd:date)
✓ Date after:   FILTER(?issued > "2020-12-31"^^xsd:date)
✓ OR filter:    FILTER(CONTAINS(..., "word1") || CONTAINS(..., "word2"))
✓ AND filter:   FILTER(CONTAINS(..., "word1") && CONTAINS(..., "word2"))
✓ Optional:     OPTIONAL {{ ?dataset dct:description ?description . }}
✓ Count:        SELECT (COUNT(?dataset) AS ?total)
✓ Sort:         ORDER BY DESC(?issued)
✓ Always retrieve variables first THEN apply filters
✓ Short acronyms: REGEX(LCASE(STR(?title)), "(^|\\\\s)ai(\\\\s|$)") — use for keywords ≤3 letters to avoid partial matches (e.g. "ai" matching "obtained")
✓ Combine:  FILTER(CONTAINS(LCASE(STR(?title)), "artificial intelligence") || REGEX(LCASE(STR(?title)), "(^|\\\\s)ai(\\\\s|$)"))

✗ NEVER use LOWER() or LOWERCASE()
✗ NEVER use || for string concatenation
✗ NEVER filter a variable before binding it
✗ NEVER use foaf: or void: unless explicitly needed
✗ NEVER use uppercase in CONTAINS keywords — LCASE converts everything to lowercase
  WRONG: CONTAINS(LCASE(STR(?title)), "AIDS")
  RIGHT: CONTAINS(LCASE(STR(?title)), "aids")
═══════════════════════════════════════
URI SHORTCUTS (use simultaneously with FILTER when possible — faster and more precise!):
Do not use them in filter with CONTAINS, use them directly in triple pattern:
═══════════════════════════════════════
COUNTRIES (dct:spatial):
- Croatia:  <http://publications.europa.eu/resource/authority/country/HRV>
- Germany:  <http://publications.europa.eu/resource/authority/country/DEU>
- France:   <http://publications.europa.eu/resource/authority/country/FRA>
- Italy:    <http://publications.europa.eu/resource/authority/country/ITA>
- Spain:    <http://publications.europa.eu/resource/authority/country/ESP>

FILE FORMATS (dct:format on distribution):
- <http://publications.europa.eu/resource/authority/file-type/CSV>
- <http://publications.europa.eu/resource/authority/file-type/JSON>
- <http://publications.europa.eu/resource/authority/file-type/XML>
- <http://publications.europa.eu/resource/authority/file-type/PDF>

═══════════════════════════════════════
THEME URI (use this instead of text search for theme!):
═══════════════════════════════════════
WHEN a theme is detected, use URI directly — do NOT use CONTAINS for theme:
  ?dataset dcat:theme <http://publications.europa.eu/resource/authority/data-theme/CODE> .

Detected theme for this question:
{teme_odgovor}
Use this anytime you detect the theme in the question
═══════════════════════════════════════
DECISION LOGIC:
═══════════════════════════════════════
IF theme is detected BUT the question mentions a specific subtopic 
(e.g. "narcotics", "cancer", "solar energy"):
  → use dcat:theme URI for the broad theme
  → AND add FILTER(CONTAINS(LCASE(STR(?title)), "specific_keyword")) 
    to narrow down results
  → consider OPTIONAL description filter as well

IF question mentions a country:
  → use dct:spatial URI instead of CONTAINS on title

IF theme is detected (see above):
  → ALWAYS use dcat:theme URI for the broad category
  → ALWAYS ALSO add FILTER with the most specific keyword from the question translated to English
  → NEVER use the theme URI alone — a theme covers thousands of unrelated datasets
  → The keyword must be the SPECIFIC topic, NOT the theme name itself
    WRONG: theme=SOCI → FILTER keyword="family" (too broad)
    RIGHT:  theme=SOCI + question="obiteljsko nasilje" → FILTER keyword="domestic violence"
    RIGHT:  theme=HEAL + question="rak pluća" → FILTER keyword="lung cancer"
    RIGHT:  theme=ENVI + question="onečišćenje rijeka" → FILTER keyword="river pollution"
  → Translate the specific keyword to English, use synonyms with OR if needed
  
IF question asks for description:
  → add OPTIONAL {{ ?dataset dct:description ?description . }}
  → add FILTER(LANG(?description) = "en")

IF question asks between two dates:
  → use >= and <= with ^^xsd:date

IF question asks to count:
  → use SELECT (COUNT(?dataset) AS ?total)

IF question asks to sort:
  → use ORDER BY DESC(?issued) or ORDER BY ASC(?issued)

IF the question mentions a specific substance or topic:
  → translate to multiple English synonyms and use OR between them
  → e.g. "narkotici" → "narcotic" || "drug" || "controlled substance"
═══════════════════════════════════════
ONE-SHOT EXAMPLE (most similar to your question):
═══════════════════════════════════════
Question: {data_pitanje}
SPARQL:
{data_sparql}

this is an exaple of how your SPARQL query should look, if you need to add more thing add them
═══════════════════════════════════════
USER QUESTION:
═══════════════════════════════════════
{pitanje}

Generate ONLY the SPARQL query without additional explanations.
"""

LOGIC_CHECK_PROMPT_TEMPLATE = """
You are an expert SPARQL developer and code reviewer for the EU Open Data Portal.
Your task is to review the GENERATED SPARQL QUERY against the USER QUESTION.

CRITICAL REVIEW RULES:
1. If the generated query logically and structurally answers the user's question, you MUST return ONLY the word "ISPRAVNO".
2. DO NOT optimize, rewrite, or "improve" the query if it already works correctly.
3. DO NOT add redundant text filters (e.g., CONTAINS) if the query already uses the correct URI (e.g., dcat:theme). 
4. DO NOT translate terms back into Croatian for filtering. Filters should remain in English unless specifically requested.
5. ONLY return a corrected SPARQL query if there is a FATAL SYNTAX ERROR or a CLEAR LOGICAL MISS (e.g., missing a date range explicitly asked for, or using the wrong variable).

When fixing is absolutely necessary, preserve the structure of the original query as much as possible and only change the broken parts.

USER QUESTION:
{pitanje}

GENERATED SPARQL QUERY:
```sparql
{originalni_upit}
"""
CORRECTION_PROMPT_TEMPLATE = """
You are an expert SPARQL developer for the EU Open Data Portal.
A SPARQL query was generated but failed. Fix it so it works with the Virtuoso SPARQL endpoint and follows DCAT-AP conventions.

USER QUESTION:
{pitanje}

ORIGINAL SPARQL QUERY:
```sparql
{originalni_upit}
```

ERROR MESSAGE:
{poruka_greske}

IMPORTANT RULES (DCAT-AP + Virtuoso):
- Use only these prefixes:
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
- The main class for datasets is dcat:Dataset.
- Use dct:title for titles and dct:description for descriptions.
- For text search use LCASE(STR(?var)) and CONTAINS.
- Prefer English results: FILTER(LANG(?title) = "en" || LANG(?title) = "") (and similarly for descriptions).
- Use && for logical AND, || for logical OR.

Return ONLY the corrected SPARQL query with no additional explanation.
"""

ANALYSIS_CORRECTION_PROMPT_TEMPLATE = """
You are an expert SPARQL developer for the EU Open Data Portal.
A query verification step found problems. Based on the analysis below, generate a corrected SPARQL query that works with the Virtuoso SPARQL endpoint and follows DCAT-AP conventions.

ANALYSIS:
{analiza}

USER QUESTION:
{pitanje}

IMPORTANT RULES (DCAT-AP + Virtuoso):
- Use only these prefixes:
  PREFIX dcat: <http://www.w3.org/ns/dcat#>
  PREFIX dct: <http://purl.org/dc/terms/>
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
- The main class for datasets is dcat:Dataset.
- Use dct:title for titles and dct:description for descriptions.
- Do not use other vocabularies (e.g., void:, foaf:, dcterms:) unless explicitly required.
- For text search use LCASE(STR(?var)) and CONTAINS.
- Prefer English results: FILTER(LANG(?title) = "en" || LANG(?title) = "") (and similarly for descriptions).
- Use && for logical AND, || for logical OR.

Return ONLY the corrected SPARQL query with no additional explanation.
"""
SIMILARITY_BASE_ONE_SHOT_PROMPT_TEMPLATE = """
You are a SPARQL query structure analyzer.

Your task is to find the most structurally similar question from the bank of examples below.

IMPORTANT RULES:
- Ignore specific topics, countries, keywords (e.g. "Croatia", "COVID", "energy")
- Focus ONLY on the SPARQL structure needed:
  * Does it filter by date range? (between X and Y) (HIGH)
  * Does it filter by date after/before? (HIGH)
  * Does it need description field? (LOW)
  * Does it use OR between keywords? (LOW)
  * Does it need publisher/format? (MEDIUM)
  * Does it count results? (LOW)
  * Does it sort by date? (HIGH)
  * What is the LIMIT? (LOW)

In other words:
- date_range match → automatic winner, ignore everything else
- if no date_range match exists → then look at description, date_after...
- never pick a match based only on keyword_search or limit
BANK OF EXAMPLES:
{banka_primjera}

NEW QUESTION:
{pitanje}



"""

TEME = {
    "AGRI": "Agriculture, farming, food, fisheries",
    "ENVI": "Environment, climate, nature, pollution",
    "HEAL": "Health, medicine, hospitals, disease",
    "TRAN": "Transport, mobility, roads, aviation",
    "ENER": "Energy, electricity, renewables, oil",
    "ECON": "Economy, finance, trade, GDP",
    "EDUC": "Education, schools, universities",
    "TECH": "Technology, innovation, digital",
    "SOCI": "Society, population, demographics",
    "GOVE": "Government, politics, law, justice",
    "JUST": "Justice, legal system, crime, courts",
    "REGI": "Regions, cities, local government, urban"
}

URI_CREATION_PROMPT = """
You are an expert in creating thematic URIs for datasets based on their titles and descriptions.
Given a question about datasets, analyze the content and determine the most relevant theme from the following list:
{pitanje}
THEMES:
{teme}
return ONLY the 4-letter code of the most relevant theme, without any additional text or explanation.
if the question does not clearly match any theme, return "this query does not match any theme" (for "none") and dont use uri for theme.
"""

def detect_theme(pitanje, teme=TEME):
    detailed_prompt = URI_CREATION_PROMPT.format(
        pitanje=pitanje,
        teme = teme
    )
    try:
        response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": detailed_prompt}],
        temperature=0.0
        )
        ai_odgovor = response.choices[0].message.content
        return ai_odgovor         
    except Exception as e:
        print(f"❌ Greška pri provjeri logike: {e}")
        return None

def similarity_base_upit(banka_primjera, pitanje):
    
    print(f"\nProvjeri najslicnije pitanje'{pitanje}'")
    
    detailed_prompt = SIMILARITY_BASE_ONE_SHOT_PROMPT_TEMPLATE.format(
        banka_primjera=banka_primjera,
        pitanje=pitanje
    )

    try:
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": detailed_prompt}],
        temperature=0.0
        )
        ai_odgovor = response.choices[0].message.content
        # Provjeri je li AI rekao da je upit ispravan
        for entry in BANKA_PRIMJERA:
            if entry['pitanje'] in ai_odgovor:
                return entry['sparql'], entry['pitanje']
        return None, None
    except Exception as e:
        print(f"❌ Greška pri provjeri logike: {e}")
        return None, None
    
def generiraj_sparql(pitanje):
    """Generira SPARQL upit iz pitanja na prirodnom jeziku."""
    data_sparql, data_pitanje = similarity_base_upit(BANKA_PRIMJERA, pitanje)
    if data_sparql is None or data_pitanje is None:
        print("⚠️ Nema odgovarajućeg primjera u bazi primjera. Generiram SPARQL izravno.")
        data_sparql = ""
        data_pitanje = ""
    teme_odgovor = detect_theme(pitanje, TEME)
    final_prompt = PROMPT_TEMPLATE.format(pitanje=pitanje, data_pitanje=data_pitanje, data_sparql=data_sparql, teme_odgovor=teme_odgovor)
    print(final_prompt)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": final_prompt}], 
            temperature=0.0
        )
        ai_odgovor = response.choices[0].message.content
        if "```sparql" in ai_odgovor:
            sparql_kod = ai_odgovor.split("```sparql\n")[1].split("```")[0]
        else:
            sparql_kod = ai_odgovor
        
        print("✅ SPARQL upit uspješno generiran.")
        return sparql_kod.strip() 

    except Exception as e:
        print(f"❌ Greška pri generiranju SPARQL-a: {e}")
        return None

def ispravi_sparql(originalni_upit, poruka_greske, pitanje):
    """Pokušava ispraviti SPARQL upit na temelju greške."""
    print("\n🔧 Pokušavam ispraviti upit na temelju greške...")
    
    prompt_ispravka = CORRECTION_PROMPT_TEMPLATE.format(
        pitanje=pitanje,
        originalni_upit=originalni_upit,
        poruka_greske=poruka_greske,
    )
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": prompt_ispravka}], 
            temperature=0.0
        )
        ai_odgovor = response.choices[0].message.content
        if "```sparql" in ai_odgovor:
            sparql_kod = ai_odgovor.split("```sparql\n")[1].split("```")[0]
        else:
            sparql_kod = ai_odgovor
        
        print("✅ Ispravljeni SPARQL upit generiran.")
        return sparql_kod.strip()
        
    except Exception as e:
        print(f"❌ Greška pri ispravljanju SPARQL-a: {e}")
        return None

def provjeri_logiku_upita(originalni_upit, pitanje):
    """Provjerava logičku korektnost SPARQL upita u odnosu na pitanje."""
    print(f"\n🔍 PROVJERA LOGIKE: Analiziram upit za pitanje: '{pitanje}'")
    
    detailed_prompt = LOGIC_CHECK_PROMPT_TEMPLATE.format(
        pitanje=pitanje,
        originalni_upit=originalni_upit,
    )


    try:
        response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": detailed_prompt}],
        temperature=0.0
        )
        ai_odgovor = response.choices[0].message.content
        # Provjeri je li AI rekao da je upit ispravan
        if "ISPRAVNO" in ai_odgovor.upper() and "NE" not in ai_odgovor.upper():
            print("✅ Logička provjera: upit je sintaktički i semantički ispravan.")
            return "ISPRAVNO"
        else:
            print("⚠️  Logička provjera otkrila probleme:")
            print(ai_odgovor)
            
            # Ako AI nije rekao "ISPRAVNO", pokušaj ispraviti upit
            prompt_za_ispravak = ANALYSIS_CORRECTION_PROMPT_TEMPLATE.format(
                analiza=ai_odgovor,
                pitanje=pitanje,
            )
            
            response_ispravak = client.chat.completions.create(
                model="llama-3.3-70b-versatile", 
                messages=[{"role": "user", "content": prompt_za_ispravak}], 
                temperature=0.0
            )
            ispravljeni_upit = response_ispravak.choices[0].message.content
            
            # Ekstrahiraj SPARQL kod ako je u bloku
            if "```sparql" in ispravljeni_upit:
                ispravljeni_upit = ispravljeni_upit.split("```sparql\n")[1].split("```")[0]
            
            print(f"✅ Generiran ispravljeni upit")
            return ispravljeni_upit.strip()
            
    except Exception as e:
        print(f"❌ Greška pri provjeri logike: {e}")
        return None




# Glavni program
if __name__ == "__main__":
    pitanje = "Prikaži mi 20 skupova podataka o hrvatskoj ekonomiji izmedu 2022 i 2024 s njiovim opisima."
    sparql_upit = generiraj_sparql(pitanje)
    detect_theme(pitanje)
    if sparql_upit:
        print("\n" + "="*50)
        print("GENERIRANI SPARQL UPIT:")
        print("="*50)
        print(sparql_upit)
        print("="*50)
    else:
        print("Nije moguće generirati SPARQL upit.")