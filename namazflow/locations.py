"""Explicit town-centre coordinates; never geocode a district as another town."""

LOCATIONS = {
    "darmstadt": {
        "label": "Darmstadt",
        "city": "Darmstadt",
        "country": "Germany",
        "latitude": 49.8728,
        "longitude": 8.6512,
    },
    "niederhoechstadt": {
        "label": "Niederhöchstadt · Eschborn",
        "city": "Niederhöchstadt",
        "country": "Germany",
        "latitude": 50.1586,
        "longitude": 8.5467,
    },
}


def selected_location(config):
    """Keep existing custom city settings unless a preset is explicitly selected."""
    key = config.get("location", "")
    return LOCATIONS.get(key)


def location_label(config):
    location = selected_location(config)
    return location["label"] if location else config["city"]
