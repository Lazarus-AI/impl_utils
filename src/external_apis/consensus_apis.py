import json
import os
from typing import Any
import googlemaps
import requests


def send_smarty_request(
    address: str = None, city: str = None, state: str = None, zip: str = None
) -> Any:
    """
    Ping the Smarty API to validate address information.

    :param address: The street address.
    :param city: The city name.
    :param state: The state abbreviation.
    :param zip: The ZIP code.
    :return: The closest matching address to the information given in the input determined by the Smarty API, or None if inputs are insufficient.
    :raises Exception: If there are errors in the response or if the response is empty.
    """
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
        print("Not enough inputs available for google maps api")
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
            raise Exception(f"Got errors from Smarty - Errors: {json.dumps(smarty_res['errors'])}")

            
def ping_gmaps(address: str = None, city: str = None, state: str = None) -> Any:
    """
    Ping Google Maps API to validate address information.

    :param address: The address for which to fetch information.
    :param city: The city where the address is located.
    :param state: The state where the address is located.
    :return: A tuple containing the main address, city, and state.
    """
    gmaps = googlemaps.Client(key=os.environ.get("GMAPS_API_KEY"))
    gmaps_res = gmaps_addr[0]["structured_formatting"]
    gmaps_address = gmaps_res["main_text"]
    gmaps_otherinfo = gmaps_res["secondary_text"].split(", ")
    gmaps_city = gmaps_otherinfo[0]
    gmaps_state = gmaps_otherinfo[1]

    return (gmaps_address, gmaps_city, gmaps_state)
  
  
  def get_npi_registry(npi: str) -> Any:
    """
    Ping the NPI Registry to get information for a given NPI number.

    :param npi: The NPI number to query.
    :return: A dictionary containing the response from the NPI Registry.
    """
    url = f"https://npiregistry.cms.hhs.gov/api/?number={npi}&pretty=&version=2.1"
    resp = requests.get(url).json()
    return resp