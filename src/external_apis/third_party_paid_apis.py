import agentql
from playwright.sync_api import sync_playwright #requires chromedriver. install that locally if you want (Sri has 130.0.6723.69 installed)
import json
import requests
import os

##AGENT QL

#example dataquery with some prompt engineering
DATA_QUERY =  """
{
    pokemon_evolution_information(look for text like "evolves into X_1 at level Y_1, which evolves into X_2 at level Y_2" in a text block above Biology section)
    highlevel_pokemon_info_box(near top right section of page with a bunch of condensed statistics) {
        pokemon_type(underneath "type")[]
        height(just return meters)
        weight(just return kg)
    }
    Biology {
        entire_section (scrape the entire Biology section)
        location(the biome and location pokemon is found)
    }
    Base_stats(this is a table. just scrape the information on the left, not anything under Range) {
        HP
        Attack
        Defense
        Sp_Atk
        Sp_Def
        Speed
        Total
    }
    Type_effectiveness(this is a table) {
        Damaged_normally_by(ONLY include elements in the "Damaged normally by" ROW of the table)[]
        Weak_to(ONLY include elements in the "Weak to" ROW of the table)[]
        Immune_to(ONLY include elements in the "Immune to" ROW of the table)[]
        Resistant_to(ONLY include elements in the "Resistant to" ROW of the table)[]
    }
    By_leveling_up(this is a table) {
        Move[]
        Move_url(scrape all the urls associated with each move)[]
        Type[]
        Cat[]
        Pwr[]
        Acc[]
        PP[]
    }
}
"""

#can only run this from python script. there's an async version but just run the script.
def agentql_scrape_urls(DATA_QUERY, input_url, output_path):
    #what is this: rikai extract for websites. Agentql can do a lot more, but I think the scraping part is most useful for us.
    #refer to https://docs.agentql.com/agentql-query for query language documentation
    #this function scrapes urls on a defined data query and puts that into output folder

    def check_url_status(url): #if this check fails, then do not continue to scrape.
        try:
            response = requests.get(url, timeout=5)
            return response.status_code
        except requests.exceptions.RequestException as e:
            print(f"Error reaching {url}: {e}")
            return 400

    def scrape_url(input_url):
        url_status = check_url_status(input_url)
        if url_status == 200:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = agentql.wrap(browser.new_page())
                page.goto(input_url)
                data = page.query_data(DATA_QUERY)
                with open(output_path, 'w') as f: #it's a bit jank to put urls as name of json, but if it works it works.
                    json.dump(data, f, indent=4)
                browser.close()
            print(f"Processed {input_url}")
        else:
            print(f"Failed to process {input_url}")

    scrape_url(input_url)

#example query
agentql_scrape_urls(DATA_QUERY, "https://bulbapedia.bulbagarden.net/wiki/Bulbasaur_(Pok%C3%A9mon)", "scraped_output.json")