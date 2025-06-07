import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
import locale

URL = "https://karlstadsenergi.se/atervinning/atervinningscentraler"
CENTERS = [
    "Djupdalen",
    "Heden",
    "Vålberg",
    "Våxnäs",
    "Väse",
    "Kvarntorp (Forshaga)",
    "Molkom",
]

# Set Swedish locale for weekday names (if available)
try:
    locale.setlocale(locale.LC_TIME, 'sv_SE.UTF-8')
except locale.Error:
    pass  # fallback if not available

def extract_center_name(header_text):
    # Remove 'ÅVC ' prefix if present
    header_text = header_text.replace("ÅVC ", "")
    # Split on first digit or 'Stängt' or 'Öppet'
    match = re.match(r"([A-Za-zåäöÅÄÖ\s()]+?)(Stängt|Öppet|\d|$)", header_text)
    if match:
        return match.group(1).strip()
    return header_text.strip()

def fetch_opening_hours():
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    data = {}
    for header in soup.find_all("div", class_="ke-open-hours__header"):
        raw_header = header.get_text(strip=True)
        center_name = extract_center_name(raw_header)
        print(f"Found header: '{center_name}' (raw: '{raw_header}')")
        content = header.find_next_sibling("div", class_="ke-open-hours__content")
        today = None
        tomorrow = None
        if content:
            days = content.find_all("div", class_="ke-open-hours__day")
            for i, day in enumerate(days):
                label = day.find("p").get_text(strip=True)
                value = day.find_all("p")[1].get_text(strip=True)
                if label.lower().startswith("idag"):
                    today = value
                    # Tomorrow is the next entry, if available
                    if i + 1 < len(days):
                        tomorrow_value = days[i+1].find_all("p")[1].get_text(strip=True)
                        tomorrow = tomorrow_value
                    break
        data[center_name] = {"today": today, "tomorrow": tomorrow}
    return data

def main():
    data = fetch_opening_hours()
    for center, hours in data.items():
        print(f"{center}:")
        print(f"  Today:    {hours['today']}")
        print(f"  Tomorrow: {hours['tomorrow']}")
        print()

if __name__ == "__main__":
    main() 
