from fastapi import FastAPI, HTTPException
import phonenumbers
from phonenumbers import geocoder, carrier, timezone, PhoneNumberFormat, PhoneNumberType
import urllib.parse

app = FastAPI(title="Mobile Info & Footprint API")

def get_number_type_name(num_type):
    type_dict = {
        PhoneNumberType.FIXED_LINE: "Fixed Line",
        PhoneNumberType.MOBILE: "Mobile",
        PhoneNumberType.VOIP: "VoIP",
        PhoneNumberType.UNKNOWN: "Unknown"
    }
    return type_dict.get(num_type, "Mobile/Other")

def generate_osint_dorks(formatted_number: str, national_number: str):
    encoded_num = urllib.parse.quote(formatted_number)
    return {
        "google_search": f"https://www.google.com/search?q=\"{encoded_num}\"",
        "google_dorks": {
            "social_media": f"https://www.google.com/search?q=site:facebook.com OR site:twitter.com OR site:instagram.com \"{national_number}\"",
            "paste_sites": f"https://www.google.com/search?q=site:pastebin.com OR site:justpaste.it \"{national_number}\"",
            "documents": f"https://www.google.com/search?q=filetype:pdf OR filetype:xlsx \"{national_number}\""
        },
        "public_aggregators": [
            f"https://intelx.io/?s={encoded_num}",
            f"https://epieos.com"
        ]
    }

@app.get("/api/mobile-info")
def get_mobile_info(number: str):
    try:
        parsed_number = phonenumbers.parse(number, "IN")

        if not phonenumbers.is_valid_number(parsed_number):
            return {"success": False, "message": "Invalid phone number"}

        # Basic Info
        country_name = geocoder.description_for_number(parsed_number, "en")
        carrier_name = carrier.name_for_number(parsed_number, "en")
        time_zones = timezone.time_zones_for_number(parsed_number)
        
        # Formats
        e164_fmt = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
        intl_fmt = phonenumbers.format_number(parsed_number, PhoneNumberFormat.INTERNATIONAL)
        national_num = str(parsed_number.national_number)

        # OSINT Footprints
        footprints = generate_osint_dorks(e164_fmt, national_num)

        return {
            "success": True,
            "input_number": number,
            "details": {
                "formatted": intl_fmt,
                "e164": e164_fmt,
                "country_code": f"+{parsed_number.country_code}",
                "region": country_name if country_name else "Unknown",
                "carrier": carrier_name if carrier_name else "Unknown",
                "timezones": list(time_zones)
            },
            "digital_footprints": footprints
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))