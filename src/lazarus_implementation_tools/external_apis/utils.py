from typing import Any

from lazarus_implementation_tools.external_apis.consensus_apis import (
    get_npi_registry,
    ping_gmaps,
    send_smarty_request,
)


def validate_address_using_smarty(
    address: str = None, city: str = None, state: str = None, zip: str = None
) -> Any:
    """Ping the Smarty API to validate address information.

    :param address: The street address.
    :param city: The city name.
    :param state: The state abbreviation.
    :param zip: The ZIP code.

    :returns: The closest matching address to the information given in the input
        determined by the Smarty API, or None if inputs are insufficient.

    :raises Exception: If there are errors in the response or if the response is empty.

    """
    return send_smarty_request(address, city, state, zip)


def validate_address_using_gmaps(address: str = None, city: str = None, state: str = None) -> Any:
    """Ping Google Maps API to validate address information.

    :param address: The address for which to fetch information.
    :param city: The city where the address is located.
    :param state: The state where the address is located.

    :returns: A tuple containing the main address, city, and state.

    """
    return ping_gmaps(address, city, state)


def validate_npi(npi: str) -> Any:
    """Ping the NPI Registry to get information for a given NPI number.

    :param npi: The NPI number to query.

    :returns: A dictionary containing the response from the NPI Registry.

    """
    return get_npi_registry(npi)
