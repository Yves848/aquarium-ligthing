import time
import json
import requests
import datetime
import os

CONFIG_PATH = "/opt/aquarium-lighting/config.json"
ESP32_BASE_URL = "http://192.168.50.202"

last_state = None  # "on", "off"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def get_current_timeslot(cfg):
    today = datetime.datetime.now().strftime("%A").lower()
    print(f"Jour actuel : {today}")
    now = datetime.datetime.now().time()

    horaires = cfg["jours"].get(today)
    if not horaires:
        return None
    print(horaires["on"])
    print(horaires["off"])
    on_time = datetime.datetime.strptime(horaires["on"], "%H:%M").time()
    off_time = datetime.datetime.strptime(horaires["off"], "%H:%M").time()

    if on_time <= now < off_time:
        return "on"
    else:
        return "off"

def call_endpoint(endpoint):
    try:
        url = f"{ESP32_BASE_URL}/{endpoint}"
        print(f"→ Appel {url}")
        requests.post(url, timeout=5)
    except Exception as e:
        print(f"Erreur lors de l'appel à {endpoint}: {e}")
        
def get_esp_state():
    try:
        url = f"{ESP32_BASE_URL}/data"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get("state")
        else:
            print(f"Erreur lors de la récupération de l'état : {response.status_code}")
            return None
    except Exception as e:
        print(f"Erreur lors de la récupération de l'état : {e}")
        return None


def run_loop():
    global last_state
    print("Démarrage du service d'éclairage aquarium")

    while True:
        try:
            config = load_config()
            if config.get("mode") != "auto":
                print("Mode manuel actif")
                time.sleep(30)
                continue

            current_state = get_current_timeslot(config)
            esp_state = get_esp_state()
            if current_state and (current_state != last_state or current_state != esp_state):
                print(f"→ État changé : {current_state.upper()}")
                call_endpoint("day" if current_state == "on" else "night")
                last_state = current_state

        except Exception as ex:
            print(f"Erreur générale : {ex}")

        time.sleep(30)

if __name__ == "__main__":
    run_loop()
