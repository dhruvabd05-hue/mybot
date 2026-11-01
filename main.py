from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os
import re

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to Number Info API",
        "usage": "/info?number=PHONE_NUMBER"
    })

def extract_numerology(soup):
    """Pull the numerology sentence or traits from the page."""
    # Try a table row first (label might be 'Numerology' or 'Numerology Analysis')
    for label in ("Numerology", "Numerology Analysis", "Numerology experts"):
        cell = soup.find(string=re.compile(label, re.I))
        if cell:
            row = cell.find_parent("tr")
            if row:
                tds = row.find_all("td")
                if len(tds) > 1:
                    text = tds[1].get_text(" ", strip=True)
                    if text and text != "N/A":
                        return text
            # If not in a table, grab the parent paragraph/div text
            parent = cell.find_parent(["p", "div", "span"])
            if parent:
                text = parent.get_text(" ", strip=True)
                if text:
                    return text

    # Fallback: search for the whole sentence containing 'Numerology experts'
    pattern = re.compile(r"According to Numerology experts.*?based on numerology analysis", re.I | re.S)
    match = pattern.search(soup.get_text(" ", strip=True))
    if match:
        return match.group(0).strip()

    # Last-ditch: any element whose text mentions 'Unreflective' or 'Haughty'
    for trait in ("Unreflective", "Haughty", "Scrupulous", "Ritualistic"):
        el = soup.find(string=re.compile(trait, re.I))
        if el:
            parent = el.find_parent(["p", "div", "td"])
            if parent:
                return parent.get_text(" ", strip=True)

    return "N/A"

@app.route('/info', methods=['GET'])
def number_info():
    phone_number = request.args.get('number')
    if not phone_number:
        return jsonify({"error": "Please provide ?number= parameter"}), 400

    if not phone_number.isdigit() and not (phone_number.startswith('+') and phone_number[1:].isdigit()):
        return jsonify({"error": "Invalid phone number format"}), 400

    try:
        url = "https://calltracer.in"
        headers = {
            "Host": "calltracer.in",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"country": "IN", "q": phone_number}

        response = requests.post(url, headers=headers, data=payload, timeout=10)
        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch data. HTTP {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')

        def get_value(label):
            # Exact match first, then case-insensitive regex
            cell = soup.find(string=lambda t: t and t.strip() == label)
            if not cell:
                cell = soup.find(string=re.compile(re.escape(label), re.I))
            if cell:
                row = cell.find_parent("tr")
                if row:
                    tds = row.find_all("td")
                    if len(tds) > 1:
                        return tds[1].get_text(strip=True)
            return "N/A"

        numerology = extract_numerology(soup)

        data = {
            "Number": phone_number,
            "Complaints": get_value("Complaints"),
            "Owner Name": get_value("Owner Name"),
            "SIM Card": get_value("SIM card"),
            "Mobile State": get_value("Mobile State"),
            "IMEI Number": get_value("IMEI number"),
            "MAC Address": get_value("MAC address"),
            "Connection": get_value("Connection"),
            "IP Address": get_value("IP address"),
            "Owner Address": get_value("Owner Address"),
            "Hometown": get_value("Hometown"),
            "Reference City": get_value("Refrence City"),
            "Owner Personality": get_value("Owner Personality"),
            "Language": get_value("Language"),
            "Mobile Locations": get_value("Mobile Locations"),
            "Country": get_value("Country"),
            "Tracking History": get_value("Tracking History"),
            "Tracker ID": get_value("Tracker Id"),
            "Tower Locations": get_value("Tower Locations"),
            "Numerology": numerology
        }

        if all(v == "N/A" for v in data.values()):
            return jsonify({"error": "No data found for this number."}), 404

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)