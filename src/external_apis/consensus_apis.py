import os
from typing import Any

import googlemaps


def ping_gmaps(address: str = None, city: str = None, state: str = None) -> Any:
    """
    Ping Google Maps API to validate address information.

    :param address: The address for which to fetch information.
    :param city: The city where the address is located.
    :param state: The state where the address is located.
    :return: A tuple containing the main address, city, and state.
    """
    gmaps = googlemaps.Client(key=os.environ.get("GMAPS_API_KEY"))
    if address and city and state:
        gmaps_addr = gmaps.places_autocomplete_query(f"{address} {city},{state}")
    elif address and city:
        gmaps_addr = gmaps.places_autocomplete_query(f"{address} {city}")
    else:
        print("Not enough inputs available for google maps api")
        return None

    gmaps_res = gmaps_addr[0]["structured_formatting"]
    gmaps_address = gmaps_res["main_text"]
    gmaps_otherinfo = gmaps_res["secondary_text"].split(", ")
    gmaps_city = gmaps_otherinfo[0]
    gmaps_state = gmaps_otherinfo[1]

    return (gmaps_address, gmaps_city, gmaps_state)
