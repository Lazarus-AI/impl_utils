import re

from lazarus_implementation_tools.general.core import sanitize_string


def get_data_from_json_map(json_data, json_map):
    """Retrieves data from a nested JSON structure using a dot-separated path.

    :param json_data: The nested JSON data.
    :param json_map: A dot-separated string representing the path to the desired data.

    :returns: The data at the specified path, or None if the path is invalid.

    """
    parts = json_map.split(".")
    current_location = json_data
    try:
        for part in parts:
            if "[" in part and "]" in part:
                try:
                    bits = part.split("[")
                    index = bits[1][:-1]
                    index = int(index) if index else 0
                    current_location = current_location.get(bits[0])[index]
                except KeyError:
                    current_location = {}
                continue

            current_location = current_location.get(part)
        value = current_location
    except Exception:
        value = None

    return value


def normalize_text(text: str) -> str:
    """This removes non-alphanumeric characters and lower cases the string.

    Useful for comparing strings without worrying about special characters making the
    comparison non-valid.

    :param text: Text to normalize

    :returns: normalized string

    """
    allowed_characters = [" ", "'", "-"]
    text = re.sub(r"\s+", " ", text)
    text = text.lower()
    text = "".join(char for char in text if char.isalnum() or char in allowed_characters)
    return sanitize_string(text.strip())
