from fastapi import FastAPI, HTTPException
import phonenumbers
from phonenumbers import geocoder, carrier, timezone

app = FastAPI(
    title="Mobile Number Info API",
    description="API to extract region, carrier, and validity details of a phone number",
    version="1.0.0"
)

@app.get("/")
def home():
    return {"status": "API is active", "usage": "/api/mobile-info?number=+91XXXXXXXXXX"}

@app.get("/api/mobile-info")
def get_mobile_info(number: str):
    """
    Query Param: number (Country Code ke sath, e.g., +919876543210)
    """
    try:
        # Number parse karein
        parsed_number = phonenumbers.parse(number)

        # Validity Check
        is_valid = phonenumbers.is_valid_number(parsed_number)
        is_possible = phonenumbers.is_possible_number(parsed_number)

        if not is_valid:
            return {
                "success": False,
                "input_number": number,
                "is_valid": False,
                "message": "Invalid phone number provided"
            }

        # Country / Region Name (English)
        country_name = geocoder.description_for_number(parsed_number, "en")

        # Network Carrier (Service Provider)
        carrier_name = carrier.name_for_number(parsed_number, "en")

        # Timezones
        time_zones = timezone.time_zones_for_number(parsed_number)

        return {
            "success": True,
            "input_number": number,
            "is_valid": is_valid,
            "is_possible": is_possible,
            "country_code": f"+{parsed_number.country_code}",
            "national_number": str(parsed_number.national_number),
            "region": country_name if country_name else "Unknown",
            "carrier": carrier_name if carrier_name else "Unknown",
            "timezones": list(time_zones)
        }

    except phonenumbers.NumberParseException as e:
        raise HTTPException(status_code=400, detail=f"Invalid number format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")