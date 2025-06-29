import requests
from django.conf import settings
from geopy.geocoders import Nominatim
# services/google_api.py

def validate_coordinates(lat, lng):
    """Validate that coordinates are within valid ranges"""
    return (-90 <= lat <= 90) and (-180 <= lng <= 180)


def get_current_location():
    """Get location with coordinate validation"""
    try:
        response = requests.get('https://ipinfo.io/json')
        if response.status_code == 200:
            data = response.json()
            loc = data.get('loc', '').split(',')
            if len(loc) == 2:
                lat, lng = float(loc[0]), float(loc[1])
                if validate_coordinates(lat, lng):
                    return lat, lng
    except Exception:
        pass
    return None, None
def geocode_address(address):
    """Convert address to coordinates"""
    geolocator = Nominatim(user_agent="nearmeconnect")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

def get_nearby_services(latitude, longitude, service_type, radius=5000):
    """
    Fetch nearby services using Google Places API.
    Uses `type` for known categories, falls back to `keyword` for custom ones.
    """
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

    # Mapping known service names to official Google Place types
    SERVICE_TYPE_MAP = {
        "plumber": "plumber",
        "electrician": "electrician",
        "mechanic": "car_repair",
        "doctor": "doctor",
        "tailor": "clothing_store",
        "carpenter": None,  # Google doesn’t support this as a type
        "ac technician": "hvac_contractor",
        "barber": "hair_care",
        "salon": "beauty_salon",
        "painter": None,
        "mover": "moving_company",
        "tutor": None,
        "laundry": "laundry"
        # Add more mappings as needed
    }

    google_type = SERVICE_TYPE_MAP.get(service_type.lower())
    
    params = {
        'location': f"{latitude},{longitude}",
        'radius': radius,
        'key': settings.GOOGLE_API_KEY
    }

    # Use `type` if valid, else use `keyword`
    if google_type:
        params['type'] = google_type
    else:
        params['keyword'] = service_type  # fallback to custom keyword

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Add Google Maps links to results
        if data.get('results'):
            for place in data['results']:
                place['maps_link'] = generate_maps_link(
                    place.get('geometry', {}).get('location', {}),
                    place.get('place_id')
                )

        return data

    except requests.exceptions.RequestException as e:
        raise Exception(f"Google Places API error: {str(e)}")


def generate_maps_link(location, place_id=None):
    """Generate Google Maps URL for directions"""
    if not location or 'lat' not in location or 'lng' not in location:
        return None
    
    base_url = "https://www.google.com/maps/search/?api=1"
    query = f"query={location['lat']},{location['lng']}"
    if place_id:
        query += f"&query_place_id={place_id}"
    return f"{base_url}&{query}"


def get_place_details(place_id):
    """
    Get detailed information about a specific place
    """
    base_url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,geometry,rating,user_ratings_total,photos,website',
        'key': settings.GOOGLE_API_KEY
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Google Places Details API error: {str(e)}")