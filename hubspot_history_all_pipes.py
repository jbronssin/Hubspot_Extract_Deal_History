import requests
import csv
import os
import glob
from dotenv import load_dotenv
from datetime import datetime
from collections import defaultdict
from termcolor import colored
import sys


print(r""" 
  _    _       _                     _     ______      _                  _   
 | |  | |     | |                   | |   |  ____|    | |                | |  
 | |__| |_   _| |__  ___ _ __   ___ | |_  | |__  __  _| |_ _ __ __ _  ___| |_ 
 |  __  | | | | '_ \/ __| '_ \ / _ \| __| |  __| \ \/ / __| '__/ _` |/ __| __|
 | |  | | |_| | |_) \__ \ |_) | (_) | |_  | |____ >  <| |_| | | (_| | (__| |_ 
 |_|  |_|\__,_|_.__/|___/ .__/ \___/ \__| |______/_/\_\\__|_|  \__,_|\___|\__|
                        | |                                                   
                        |_|                                                   
    """)

print(colored("HubSpot Deal Stage History Extractor", "green"))
print(colored("Par Jean-Baptiste Ronssin - @jbronssin", "blue"))
print(colored("https://github.com/jbronssin/Hubspot_Extract_Deal_History", "blue"))
print("###############################################")
print(colored("You can interupt the script when you want by pressing Ctrl+C", "red"))
print("###############################################")
print(colored("This script will create a folder named 'extract' in the same folder as the script", "yellow"))
print("###############################################")

def main():

    # Folder creation if not exist
    if not os.path.exists("extract"):
        os.makedirs("extract")

    load_dotenv()
    TOKEN = os.environ["HUBSPOT_TOKEN"]

    # Check if the .env file is present and if the API key is set
    if not TOKEN:
        print(" ")
        print(" ")
        print("###############################################")
        print(" ")
        print("¯\_(ツ)_/¯")
        print(" ")
        print(colored("It seems you have not set your Hubspot API key in the .env file or the .env file is missing.", "red", attrs=["blink"]))
        print(colored("Please read the README and follow the process to set up your Hubspot API key.", "blue"))
        sys.exit(0)

    HUBSPOT_API_URL = "https://api.hubapi.com"

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }

    # Get all the pipelines
    def get_pipelines():
        url = f"{HUBSPOT_API_URL}/crm/v3/pipelines/deals"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pipelines_data = response.json()
        return [{"id": pipeline["id"], "label": pipeline["label"]} for pipeline in pipelines_data['results']]

    # Make the user choose a pipeline
    pipelines = get_pipelines()
    print(f"Your pipelines list between 1 and {len(pipelines)}:")
    for index, pipeline in enumerate(pipelines):
        print(f"{index + 1}. {pipeline['label']} (ID: {pipeline['id']})")

    print(colored(f"Enter the Pipeline number from 1 to {len(pipelines)} or 'all' for all your pipelines: ", "red"))
    choice = input()

    if choice.lower() == "all":
        PIPELINE_ID = None
    else:
        choice_index = int(choice) - 1
        if 0 <= choice_index < len(pipelines):
            PIPELINE_ID = pipelines[choice_index]["id"]
        else:
            print("Your choice is not valid, using the first pipeline in the list as default.")
            PIPELINE_ID = pipelines[0]["id"]
    
    def get_pipeline_stages(pipeline_id):
        url = f"{HUBSPOT_API_URL}/crm/v3/pipelines/deals/{pipeline_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        pipeline_data = response.json()
        stages = pipeline_data["stages"]
        
        stage_dict = {}
        for stage in stages:
            stage_dict[stage["id"]] = stage["label"]
        
        return stage_dict

    stage_dict = get_pipeline_stages(PIPELINE_ID) if PIPELINE_ID else None


    def get_deals(after=None):
        url = f"{HUBSPOT_API_URL}/crm/v3/objects/deals/search"
        json = {
            "properties": ["dealstage", "dealname"],
            "sort": [{"propertyName": "createdate", "direction": "ASCENDING"}],
            "limit": 20,
        }
        
        # Ajouter un filtre pour le pipeline si PIPELINE_ID est défini.
        if PIPELINE_ID:
            json["filterGroups"] = [
                {
                    "filters": [
                        {
                            "propertyName": "pipeline",
                            "operator": "EQ",
                            "value": PIPELINE_ID
                        }
                    ]
                }
            ]
        
        if after:
            json["after"] = after

        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        return response.json()

    def get_property_history(deal_id, property_name):
        url = f"{HUBSPOT_API_URL}/deals/v1/deal/{deal_id}"
        params = {
            "includePropertyVersions": "true",
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()["properties"][property_name]["versions"]

    def save_deals_to_csv(deals, file_name):
        with open(file_name, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Deal ID", "Deal Name", "Number of Stage Changes"])

            for deal in deals:
                deal_id = deal["id"]
                deal_name = deal["properties"]["dealname"]
                property_name = "dealstage"
                histories = get_property_history(deal_id, property_name)

                stage_changes_count = 0
                for history in histories:
                    if 'value' in history:
                        stage_changes_count += 1

                writer.writerow([deal_id, deal_name, stage_changes_count])

    offset = None
    file_counter = 1
    total_deals_processed = 0

    # Delete the previous files
    import glob
    previous_csv_files = glob.glob("extract/deal_stage_changes_*.csv")
    for file in previous_csv_files:
        os.remove(file)

    print("Starting the script...")

    while True:
        print(f"Retrieving deals (offset: {offset})...")
        deals_data = get_deals(offset)
        deals = deals_data["results"]

        if not deals:
            break

        print(f"Processing {len(deals)} deals...")
        file_name = f"extract/deal_stage_changes_{file_counter}.csv"
        save_deals_to_csv(deals, file_name)
        print(f"Saved: {file_name}")

        total_deals_processed += len(deals)
        print(f"{total_deals_processed} deals processed so far")

        file_counter += 1
        offset = deals_data.get("paging", {}).get("next", {}).get("after")
        if not offset:
            break

pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nYou chose to interrupt the script. Good bye!")
        sys.exit(0)

print("This is it! Well done!")
