import requests
from datetime import datetime
import pytz
import argparse
from datetime import timedelta
import asyncio

from modules.image_gen import ImageGenerator
from modules.ipixel import IPixelScreen

# API configuration
IRAIL_API_BASE = "https://api.irail.be"
MECHELEN_STATION = "Mechelen"
USER_AGENT = "MechelenTrainKiosk (github.com/aleokdev/train-display; aperea@aleok.dev)"

def get_train_departures():
    """Fetch train departures from Mechelen station"""
    try:
        url = f"{IRAIL_API_BASE}/liveboard/"
        params = {
            'station': MECHELEN_STATION,
            'format': 'json',
            'lang': 'en',
            'arrdep': 'departure'
        }
        
        headers = {
            'User-Agent': USER_AGENT
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract and format departure information
        departures = []
        if 'departures' in data and 'departure' in data['departures']:
            for departure in data['departures']['departure']:
                try:
                    # Convert timestamp to readable time
                    departure_time = datetime.fromtimestamp(int(departure['time']), tz=pytz.timezone('Europe/Brussels'))
                    
                    # Calculate delay in minutes
                    delay_seconds = int(departure.get('delay', '0'))
                    delay_minutes = delay_seconds // 60
                    
                    # Get platform information
                    platform = departure.get('platform', 'TBD')
                    
                    # Get train name from vehicle info
                    if 'vehicleinfo' in departure and 'shortname' in departure['vehicleinfo']:
                        train_name = departure['vehicleinfo']['shortname']
                    else:
                        train_name = departure.get('vehicle', 'Unknown')
                    
                    # Get destination from station field or stationinfo
                    destination = "Unknown"
                    if 'stationinfo' in departure and 'name' in departure['stationinfo']:
                        destination = departure['stationinfo']['name']
                    elif 'station' in departure:
                        destination = departure['station']
                    
                    departures.append({
                        'time': departure_time.strftime('%H:%M'),
                        'train': train_name,
                        'destination': destination,
                        'platform': platform,
                        'delay': delay_minutes,
                        'canceled': int(departure.get('canceled', '0')) == 1
                    })
                except (ValueError, KeyError, TypeError) as e:
                    print(f"Error processing individual departure: {e}")
                    print(f"Departure data: {departure}")
                    continue
        
        # Sort by departure time and limit to next 10 trains
        departures.sort(key=lambda x: x['time'])
        return departures[:10]
        
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except Exception as e:
        print(f"Error processing data: {e}")
        return []
    
def main():
    parser = argparse.ArgumentParser(
        description="Create 128x16 display with digits, min.png, text, and platform number"
    )
    parser.add_argument("mac", help="MAC address of display to use")

    args = parser.parse_args()
        
    img_gen = ImageGenerator(64, 16, "#000000", "#ffffff")

    departures = get_train_departures()
    print(departures)

    images = []
    for departure in departures:
        tz = pytz.timezone('Europe/Brussels')
        now = datetime.now(tz)
        hh, mm = map(int, departure['time'].split(':'))
        dep_dt = tz.localize(datetime(now.year, now.month, now.day, hh, mm))
        # if departure time already passed today, assume it's tomorrow
        if dep_dt < now:
            dep_dt = dep_dt + timedelta(days=1)
        minutes_until = int((dep_dt - now).total_seconds() // 60)
        if minutes_until < 0:
            minutes_until = 0

        images.append(img_gen.gen_image(minutes_until, departure['destination'], int(departure['delay'])))

    asyncio.run(IPixelScreen(args.mac).update_screen(images[0]))

if __name__ == '__main__':
    main()
