from typing import Any

from external_apis.consensus_apis import send_smarty_request, ping_gmaps


def validate_address_using_smarty(
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
    return send_smarty_request(address, city, state, zip)


def validate_address_using_gmaps(address: str = None, city: str = None, state: str = None) -> Any:
    """
    Ping Google Maps API to validate address information.

    :param address: The address for which to fetch information.
    :param city: The city where the address is located.
    :param state: The state where the address is located.
    :return: A tuple containing the main address, city, and state.
    """
    return ping_gmaps(address, city, state)
