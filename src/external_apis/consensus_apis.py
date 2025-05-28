import requests
import googlemaps
import json
import os

def ping_gmaps(address: str = None, city: str = None, state: str = None):
    gmaps = googlemaps.Client(key=os.environ.get("GMAPS_API_KEY"))
    if address and city and state:
        gmaps_addr = gmaps.places_autocomplete_query(f"{address} {city},{state}")
    elif address and city:
        gmaps_addr = gmaps.places_autocomplete_query(f"{address} {city}")
    else:
        print("Not enough inputs available for Smarty")
        return None

    gmaps_res = gmaps_addr[0]["structured_formatting"]
    gmaps_address = gmaps_res["main_text"]
    gmaps_otherinfo = gmaps_res["secondary_text"].split(", ")
    gmaps_city = gmaps_otherinfo[0]
    gmaps_state = gmaps_otherinfo[1]

    return (gmaps_address, gmaps_city, gmaps_state)

def ping_smarty(
    address: str = None, city: str = None, state: str = None, zip: str = None
):
    SMARTY_ENDPOINT = "https://us-street.api.smartystreets.com/street-address"
    params = {
        "auth-id": os.environ.get("SMARTY_AUTH_ID"),
        "auth-token": os.environ.get("SMARTY_AUTH_TOKEN"),
        "license": os.environ.get("SMARTY_LICENSE"),
    }

    if address and city and state:
        params.update({"street": address, "city": city, "state": state})

    elif address and zip:
        params.update({"street": address, "zipcode": zip})
    else:
        print("Not enough inputs available for Smarty")
        return None

    try:
        smarty_response = requests.get(
            SMARTY_ENDPOINT,
            params=params,
        )
        smarty_res = smarty_response.json()
        if not smarty_res:
            raise Exception(
                f"Could not get result back from Smarty - Response: {smarty_response.text}"
            )
        if "errors" in smarty_res:
            raise Exception(
                f"Got errors from Smarty - Errors: {json.dumps(smarty_res['errors'])}"
            )

        return smarty_res[0]

    except Exception as e:
        raise Exception(
            {"message": f"Smarty Address Lookup Failure: {smarty_res}", "error": str(e)}
        )

def ping_npi():
    pass
