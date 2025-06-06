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
    # Extract center name before first occurrence of 'Stängt' or 'Öppet' or '(' or whitespace + uppercase
    match = re.match(r"([A-Za-zåäöÅÄÖ\s()]+?)(Stängt|Öppet|\(|$)", header_text)
    if match:
        return match.group(1).replace("ÅVC ", "").strip()
    return header_text.replace("ÅVC ", "").strip()

def fetch_opening_hours():
    resp = requests.get(URL)
    soup = BeautifulSoup(resp.text, "html.parser")
    data = {}
    found_any = False
    for header in soup.find_all("div", class_="ke-open-hours__header"):
        raw_header = header.get_text(strip=True)
        center_name = extract_center_name(raw_header)
        # print(f"Found header: {center_name}")
        if center_name not in CENTERS:
            continue
        found_any = True
        content = header.find_next_sibling("div", class_="ke-open-hours__content")
        today = None
        tomorrow = None
        if content:
            days = content.find_all("div", class_="ke-open-hours__day")
            found_today = False
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
    if not found_any:
        print("No headers found. Dumping a snippet of the HTML:")
        print(soup.prettify()[:2000])
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
