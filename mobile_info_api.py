from fastapi import FastAPI, HTTPException
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, PhoneNumberFormat, PhoneNumberType
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI(
    title="Combined Mobile Info & Footprint Scraper API",
    description="API to get mobile details, carrier, formats, and scraped public footprints."
)

def get_number_type_name(num_type):
    type_dict = {
        PhoneNumberType.FIXED_LINE: "Fixed Line",
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.UNKNOWN: "Unknown"
    }
    return type_dict.get(num_type, "Mobile/Other")

def scrape_google_dork_details(query: str):
    """
    Google Dorks query chala kar Title, URL aur Snippet scrape karta hai.
    """
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.google.com/search?q={encoded_query}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    scraped_data = []
    
    try:
        response = requests.get(search_url, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Google Search Result Container
            for result in soup.select("div.g"):
                title_elem = result.select_one("h3")
                link_elem = result.select_one("a")
                snippet_elem = result.select_one("div.VwiC3b")
                
                if title_elem and link_elem:
                    scraped_data.append({
                        "title": title_elem.get_text(),
                        "url": link_elem.get("href"),
                        "snippet": snippet_elem.get_text() if snippet_elem else "No description available"
                    })
                    
                if len(scraped_data) >= 3: # Top 3 Results Limit
                    break
    except Exception as e:
        print(f"Scraping Error: {e}")
        
    return {
        "found_count": len(scraped_data),
        "results": scraped_data,
        "search_link": search_url
    }

@app.get("/")
def home():
    return {"status": "API is live", "endpoint": "/api/mobile-info?number=+91XXXXXXXXXX"}

@app.get("/api/mobile-info")
def get_mobile_info(number: str):
    try:
        # 1. Parse & Validate Mobile Number (Default India 'IN')
        parsed_number = phonenumbers.parse(number, "IN")

        if not phonenumbers.is_valid_number(parsed_number):
            return {"success": False, "message": "Invalid phone number"}

        # 2. Extract Basic Carrier & Region Info
        country_name = geocoder.description_for_number(parsed_number, "en")
        carrier_name = carrier.name_for_number(parsed_number, "en")
        time_zones = timezone.time_zones_for_number(parsed_number)
        num_type_enum = phonenumbers.number_type(parsed_number)

        # Formatted Variants
        e164_fmt = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
        intl_fmt = phonenumbers.format_number(parsed_number, PhoneNumberFormat.INTERNATIONAL)
        national_num = str(parsed_number.national_number)

        # 3. Scrape Footprints (Social Media & Paste Sites)
        social_query = f'site:facebook.com OR site:twitter.com OR site:instagram.com "{national_num}"'
        paste_query = f'site:pastebin.com OR site:justpaste.it "{national_num}"'

        social_footprints = scrape_google_dork_details(social_query)
        paste_footprints = scrape_google_dork_details(paste_query)

        # 4. Final Combined Output
        return {
            "success": True,
            "input_number": number,
            "mobile_details": {
                "e164_format": e164_fmt,
                "international_format": intl_fmt,
                "country_code": f"+{parsed_number.country_code}",
                "region": country_name if country_name else "Unknown",
                "carrier": carrier_name if carrier_name else "Unknown",
                "number_type": get_number_type_name(num_type_enum),
                "timezones": list(time_zones)
            },
            "digital_footprints": {
                "social_media": social_footprints,
                "paste_sites": paste_footprints
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))