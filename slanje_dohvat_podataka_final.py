from SPARQLWrapper import SPARQLWrapper, JSON
import os 
from dotenv import load_dotenv
load_dotenv()

#from ljudski_jezik import generiraj_sparql, ispravi_sparql,provjeri_logiku_upita
model_choice = 0
while model_choice not in ["1", "2", "3", "4", "5"]:
    model_choice = input("Koji model želite korsititi? \n 1. llama-3.3-70b-verstitile\n 2. gpt-5.4-mini \n 3. claude-haiku-4-5 \n 4. gemini-3.5-flash \n 5. Lokalni model (llama-3.1-8b) \n Unesite broje željenog modela: " )

if model_choice == "1":
    from ljudski_jezik_llama import generiraj_sparql, ispravi_sparql,provjeri_logiku_upita
elif model_choice == "2":
    from ljudski_jezik_chatgpt import generiraj_sparql, ispravi_sparql,provjeri_logiku_upita
elif model_choice == "3":
    from ljudski_jezik_claude import generiraj_sparql, ispravi_sparql,provjeri_logiku_upita
elif model_choice == "4":
    from ljudski_jezik_gemini import generiraj_sparql, ispravi_sparql,provjeri_logiku_upita
elif model_choice == "5":
    from ljudski_jezik_local import generiraj_sparql, ispravi_sparql,provjeri_logiku_upita

# Generiraj SPARQL upit iz pitanja na prirodnom jeziku
pitanje = input("Unesite pitanje na prirodnom jeziku: ")
#pitanje = "Prikazi mi 1 dataset u kojem se spominju  tehnologija i inovacije."
sparql_query = generiraj_sparql(pitanje)

if not sparql_query:
    print("Nije moguće generirati upit. Završavam program.")
    exit()

print(f"\nGENERIRANI SPARQL UPIT:\n{sparql_query}\n")

# Naziv datoteke u koju želite spremiti rezultate
output_filename = "rezultati_upita_final.json"

# Maksimalan broj pokušaja ispravljanja
MAX_POKUSAJA = 3
pokusaj = 0
logic_result = provjeri_logiku_upita(sparql_query, pitanje)
if logic_result != "ISPRAVNO":
    old_sparql_query = sparql_query
    sparql_query = ispravi_sparql(sparql_query, logic_result, pitanje)
    #print(old_sparql_query + "\n\n ==================================\n\n" + sparql_query)
    #dane = input("Zelite li poslati ispravljeni upit? (da/ne) \n Ako je odgovor ne poslat će se orginalni upit.")
    #if dane.lower() != "da":
    #    sparql_query = old_sparql_query

while pokusaj < MAX_POKUSAJA:
    pokusaj += 1
    print(f"\n{'='*50}")
    print(f"POKUŠAJ {pokusaj}/{MAX_POKUSAJA}")
    print(f"{'='*50}")
    
    # Korak 2: Postavljanje konekcije prema EU Open Data Portalu
    print("Spajam se na EU Open Data Portal...")
    sparql = SPARQLWrapper("https://data.europa.eu/sparql")
    sparql.setQuery(sparql_query)
    # Tražimo rezultate u JSON formatu jer je najlakši za obradu u Pythonu
    sparql.setReturnFormat(JSON)

    try:
        # Korak 3: Izvršavanje upita i dohvaćanje rezultata
        print("Šaljem upit...")
        results = sparql.query().convert()
        print("Upit uspješan, rezultati su primljeni.")

        # Korak 4: Spremanje rezultata u tekstualnu datoteku
        print(f"Spremam rezultate u datoteku '{output_filename}'...")

        with open(output_filename, "w", encoding="utf-8") as f:
            import json
            f.write(json.dumps(results, indent=2, ensure_ascii=False))

        # Dobijemo punu putanju do datoteke za lakše snalaženje
        full_path = os.path.abspath(output_filename)
        print(f"\nSpremanje je završeno!")
        print(f"Podaci su spremljeni u datoteku: {full_path}")
        break  # Uspješno - izlazimo iz petlje

    except Exception as e:
        poruka_greske = str(e)
        print(f"\n❌ Dogodila se greška prilikom izvršavanja upita: {poruka_greske}")
        
        if pokusaj < MAX_POKUSAJA:
            # Pokušaj ispraviti upit pomoću Groq-a
            sparql_query = ispravi_sparql(sparql_query, poruka_greske, pitanje)
            
            if not sparql_query:
                print("Nije moguće generirati ispravljeni upit. Završavam program.")
                break
                
            print("\n📝 NOVI UPIT:")
            print(sparql_query)
        else:
            print(f"\n❌ Dostignut maksimalan broj pokušaja ({MAX_POKUSAJA}). Program se završava.")
