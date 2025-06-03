from typing import Any

from external_apis.consensus_apis import ping_gmaps


def validate_address_using_gmaps(address: str = None, city: str = None, state: str = None) -> Any:
    """
    Ping Google Maps API to validate address information.

    :param address: The address for which to fetch information.
    :param city: The city where the address is located.
    :param state: The state where the address is located.
    :return: A tuple containing the main address, city, and state.
    """
    return ping_gmaps(address, city, state)
