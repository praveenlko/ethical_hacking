from fastapi import FastAPI, HTTPException
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, PhoneNumberFormat
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI(title="Auto Footprint Checker API")

def check_google_dork_results(query_url: str) -> dict:
    """
    Google Dork Link ko backend se scrape karke checks karta hai ki results exist karte hain ya nahi.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(query_url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Google "No results found" warning check karta hai
        no_results = "did not match any documents" in response.text or "No results found" in response.text
        
        return {
            "found_public_indexed_data": not no_results,
            "dork_url": query_url
        }
    except Exception:
        return {
            "found_public_indexed_data": "Unable to verify automatically",
            "dork_url": query_url
        }

@app.get("/api/mobile-info")
def get_mobile_info(number: str):
    try:
        parsed_number = phonenumbers.parse(number, "IN")

        if not phonenumbers.is_valid_number(parsed_number):
            return {"success": False, "message": "Invalid phone number"}

        e164_fmt = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
        national_num = str(parsed_number.national_number)

        # Dork Search URLs
        social_dork = f"https://www.google.com/search?q=site:facebook.com OR site:twitter.com OR site:instagram.com \"{national_num}\""
        paste_dork = f"https://www.google.com/search?q=site:pastebin.com OR site:justpaste.it \"{national_num}\""

        # Backend Verification Runs
        social_check = check_google_dork_results(social_dork)
        paste_check = check_google_dork_results(paste_dork)

        return {
            "success": True,
            "target_number": e164_fmt,
            "footprints_detection": {
                "social_media": {
                    "is_detected_on_public_web": social_check["found_public_indexed_data"],
                    "search_url": social_check["dork_url"]
                },
                "paste_sites": {
                    "is_detected_on_public_web": paste_check["found_public_indexed_data"],
                    "search_url": paste_check["dork_url"]
                }
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))