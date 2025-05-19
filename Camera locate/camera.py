# Combined Python Script for Discovering Nearby IP Cameras
# This script uses:
# - ONVIF discovery for local network
# - Shodan API for public IP cameras
# - Overpass API (OpenStreetMap) for public surveillance cameras
# - Windy API for tourist/weather webcams

import requests
import shodan
from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery
from wsdiscovery import Scope
import geopy.distance

# === CONFIGURATION ===
SHODAN_API_KEY = 'miIFIaJWWTM3PzlbelfdeNprZNZZ6B2O'
WINDY_API_KEY = '17ixhAwJyMLWX4DAvVmRNcUjtMMejymF'
LATITUDE = -33.918861   # Example: Cape Town
LONGITUDE = 18.423300
RADIUS_KM = 0.1

# === 1. ONVIF Camera Discovery on Local Network ===
def discover_onvif_cameras():
    print("Discovering ONVIF cameras on local network...")
    wsd = WSDiscovery()
    wsd.start()
    services = wsd.searchServices(scopes=[Scope("onvif://www.onvif.org/Profile")])
    for svc in services:
        print("ONVIF Camera Found:", svc.getXAddrs())
    wsd.stop()

# === 2. Shodan Camera Discovery (Public IP Cameras) ===
def discover_shodan_cameras():
    print("Searching Shodan for public cameras near you...")
    api = shodan.Shodan(SHODAN_API_KEY)
    query = f"device:webcam geo:{LATITUDE},{LONGITUDE},{RADIUS_KM}"
    try:
        results = api.search(query)
        for cam in results['matches']:
            print(f"Shodan Camera: IP={cam['ip_str']}, Ports={cam.get('port')}, Info={cam.get('data')[:100]}...")
    except Exception as e:
        print("Error using Shodan API:", e)

# === 3. Overpass API for Public Surveillance Cameras ===
def discover_osm_surveillance():
    print("Querying OpenStreetMap Overpass API for surveillance cameras...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    delta = 0.005  # ~500m buffer
    query = f"""
    [out:json];
    node["man_made"="surveillance"]({LATITUDE - delta},{LONGITUDE - delta},{LATITUDE + delta},{LONGITUDE + delta});
    out center;
    """
    response = requests.post(overpass_url, data={'data': query})
    if response.status_code == 200:
        data = response.json()
        for element in data['elements']:
            lat, lon = element['lat'], element['lon']
            dist = geopy.distance.geodesic((LATITUDE, LONGITUDE), (lat, lon)).m
            print(f"OSM Surveillance Camera at {lat},{lon} - {int(dist)}m away")
    else:
        print("Overpass API Error:", response.text)

# === 4. Windy.com Webcams API ===
def discover_windy_webcams():
    print("Fetching webcams from Windy API...")
    url = f"https://api.windy.com/api/webcams/v2/list/nearby={LATITUDE},{LONGITUDE},{RADIUS_KM}?show=webcams:location,image,player&key={WINDY_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        webcams = response.json().get('result', {}).get('webcams', [])
        for cam in webcams:
            title = cam['title']
            location = cam['location']
            image = cam['image']['current']['preview']
            print(f"Windy Webcam: {title} at {location['city']} ({location['latitude']},{location['longitude']}) - Image: {image}")
    else:
        print("Windy API Error:", response.text)

# === Run All Discoveries ===
if __name__ == "__main__":
    discover_onvif_cameras()
    discover_shodan_cameras()
    discover_osm_surveillance()
    discover_windy_webcams()