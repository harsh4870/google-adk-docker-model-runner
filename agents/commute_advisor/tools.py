"""
Mock commute data tools that simulate real-world transit and weather APIs.

In production these would be replaced with actual API integrations:
  - Weather:  OpenWeatherMap, weather.gov, Met Office API
  - Train:    National Rail Enquiries, GTFS-RT feeds, TfL Rail API
  - Bus:      TfL Bus API, TransLink, NextBus / GTFS-RT
  - Traffic:  Google Maps Platform, HERE Traffic, TomTom Traffic

The function signatures and return shapes are designed to match what a real
integration would return so swapping out the mock body is a one-file change.
"""

import json
import random
from datetime import datetime, timedelta
from typing import Optional


# --------------------------------------------------------------------------- #
# Weather
# --------------------------------------------------------------------------- #

def get_weather_data(location: str, datetime_str: Optional[str] = None) -> dict:
    """
    Fetch current weather conditions relevant to commute planning.

    Args:
        location: City or area name (e.g., "London Bridge", "New York")
        datetime_str: ISO datetime string; defaults to now

    Returns:
        dict matching WeatherReport schema
    """
    scenarios = [
        {
            "temperature_celsius": 18.5,
            "conditions": "partly_cloudy",
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 15.0,
            "visibility_km": 10.0,
            "commute_impact": "low",
            "advisory": None,
        },
        {
            "temperature_celsius": 9.0,
            "conditions": "heavy_rain",
            "precipitation_mm": 12.5,
            "wind_speed_kmh": 48.0,
            "visibility_km": 3.0,
            "commute_impact": "high",
            "advisory": "Storm warning: significant delays expected across all transport modes",
        },
        {
            "temperature_celsius": -3.0,
            "conditions": "snow",
            "precipitation_mm": 8.0,
            "wind_speed_kmh": 28.0,
            "visibility_km": 1.2,
            "commute_impact": "severe",
            "advisory": "Black ice warning: avoid driving; allow 2x normal journey time",
        },
        {
            "temperature_celsius": 23.0,
            "conditions": "sunny",
            "precipitation_mm": 0.0,
            "wind_speed_kmh": 10.0,
            "visibility_km": 15.0,
            "commute_impact": "low",
            "advisory": None,
        },
        {
            "temperature_celsius": 13.0,
            "conditions": "dense_fog",
            "precipitation_mm": 0.3,
            "wind_speed_kmh": 5.0,
            "visibility_km": 0.5,
            "commute_impact": "moderate",
            "advisory": "Dense fog: reduced motorway visibility; train services may be delayed",
        },
    ]

    data = random.choice(scenarios)
    data["location"] = location
    data["timestamp"] = datetime.now().isoformat()
    return data


# --------------------------------------------------------------------------- #
# Train
# --------------------------------------------------------------------------- #

def get_train_status(origin: str, destination: str, departure_time: Optional[str] = None) -> dict:
    """
    Fetch real-time train service status between two stations.

    Args:
        origin: Departure station name
        destination: Arrival station name
        departure_time: Desired departure time (HH:MM); defaults to next service

    Returns:
        dict matching TrainReport schema
    """
    now = datetime.now()
    next_dep = (now + timedelta(minutes=random.randint(5, 22))).strftime("%H:%M")
    line_prefix = origin[:3].upper()

    scenarios = [
        {
            "line": f"{line_prefix} Express",
            "status": "on_time",
            "delay_minutes": 0,
            "next_departure": next_dep,
            "platform": str(random.randint(1, 12)),
            "disruptions": [],
            "crowding_level": "moderate",
        },
        {
            "line": f"{line_prefix} Metro Line",
            "status": "minor_delay",
            "delay_minutes": 9,
            "next_departure": next_dep,
            "platform": str(random.randint(1, 12)),
            "disruptions": ["Signal fault at junction — engineers on site, expect 10 min delays"],
            "crowding_level": "high",
        },
        {
            "line": f"{line_prefix} Central",
            "status": "major_delay",
            "delay_minutes": 38,
            "next_departure": next_dep,
            "platform": None,
            "disruptions": [
                "Points failure between stations",
                "Emergency services attending lineside incident",
                "Services running every 30 minutes until further notice",
            ],
            "crowding_level": "high",
        },
        {
            "line": f"{line_prefix} Overground",
            "status": "suspended",
            "delay_minutes": 0,
            "next_departure": "Service suspended — no ETA",
            "platform": None,
            "disruptions": [
                "Full line suspension due to overhead wire damage",
                "Rail replacement bus service operating — allow extra 45 minutes",
                "Estimated resumption: subject to engineer report",
            ],
            "crowding_level": "low",
        },
    ]

    data = random.choice(scenarios)
    data["origin"] = origin
    data["destination"] = destination
    data["timestamp"] = datetime.now().isoformat()
    return data


# --------------------------------------------------------------------------- #
# Bus
# --------------------------------------------------------------------------- #

def get_bus_status(route_number: str, stop_id: Optional[str] = None) -> dict:
    """
    Fetch real-time bus service status and capacity for a route.

    Args:
        route_number: Bus route number or identifier (e.g., "42", "X1", "188")
        stop_id: Bus stop code for real-time tracking (optional)

    Returns:
        dict matching BusReport schema
    """
    now = datetime.now()
    next_arr = (now + timedelta(minutes=random.randint(2, 18))).strftime("%H:%M")
    alt = str(int(route_number) + 2) if route_number.isdigit() else f"N{route_number}"

    scenarios = [
        {
            "route_number": route_number,
            "status": "on_time",
            "delay_minutes": 0,
            "next_arrival": next_arr,
            "capacity_percent": 42,
            "disruptions": [],
            "alternate_routes": [],
        },
        {
            "route_number": route_number,
            "status": "minor_delay",
            "delay_minutes": 11,
            "next_arrival": next_arr,
            "capacity_percent": 88,
            "disruptions": ["Heavy congestion on primary route — running 11 minutes late"],
            "alternate_routes": [f"Route {alt} runs parallel and is currently on time"],
        },
        {
            "route_number": route_number,
            "status": "major_delay",
            "delay_minutes": 30,
            "next_arrival": next_arr,
            "capacity_percent": 97,
            "disruptions": [
                "Road closure: diversion adding ~25 minutes to journey",
                "Bus is at capacity — next service in 15 minutes",
            ],
            "alternate_routes": [
                "Nearest underground station recommended",
                f"Route {alt} not affected by closure",
            ],
        },
        {
            "route_number": route_number,
            "status": "diverted",
            "delay_minutes": 16,
            "next_arrival": next_arr,
            "capacity_percent": 55,
            "disruptions": ["Emergency road closure — bus diverted via alternate streets"],
            "alternate_routes": [
                "10-min walk to parallel route recommended",
                "Taxi/rideshare pickup unaffected at junction",
            ],
        },
    ]

    data = random.choice(scenarios)
    data["timestamp"] = datetime.now().isoformat()
    return data


# --------------------------------------------------------------------------- #
# Traffic
# --------------------------------------------------------------------------- #

def get_traffic_conditions(
    origin: str,
    destination: str,
    departure_time: Optional[str] = None,
) -> dict:
    """
    Fetch real-time road traffic conditions for a driving route.

    Args:
        origin: Starting location
        destination: End destination
        departure_time: Planned departure time for predictive routing

    Returns:
        dict matching TrafficReport schema
    """
    scenarios = [
        {
            "congestion_level": "free_flow",
            "incidents": [],
            "estimated_delay_minutes": 0,
            "alternate_routes": [],
            "road_conditions": "dry",
            "travel_time_normal_minutes": 38,
            "travel_time_current_minutes": 38,
        },
        {
            "congestion_level": "light",
            "incidents": [],
            "estimated_delay_minutes": 6,
            "alternate_routes": [],
            "road_conditions": "dry",
            "travel_time_normal_minutes": 38,
            "travel_time_current_minutes": 44,
        },
        {
            "congestion_level": "moderate",
            "incidents": ["Broken-down vehicle on A406 — 1 lane closed"],
            "estimated_delay_minutes": 22,
            "alternate_routes": ["Via ring road — 8 km longer but saving ~14 minutes"],
            "road_conditions": "wet",
            "travel_time_normal_minutes": 38,
            "travel_time_current_minutes": 60,
        },
        {
            "congestion_level": "heavy",
            "incidents": [
                "Multi-vehicle collision — 2 lanes blocked on motorway",
                "Emergency services on scene, expect 45-60 min clearance",
            ],
            "estimated_delay_minutes": 68,
            "alternate_routes": [
                "A316 via Richmond — estimated 48 min",
                "A4 via Hammersmith — estimated 54 min",
            ],
            "road_conditions": "wet",
            "travel_time_normal_minutes": 38,
            "travel_time_current_minutes": 106,
        },
        {
            "congestion_level": "standstill",
            "incidents": [
                "Major incident — motorway fully closed both directions",
                "Police and fire service on scene — no clearance estimate",
            ],
            "estimated_delay_minutes": 130,
            "alternate_routes": [
                "Public transport strongly advised",
                "Consider delaying departure by 90+ minutes",
            ],
            "road_conditions": "flooded",
            "travel_time_normal_minutes": 38,
            "travel_time_current_minutes": 210,
        },
    ]

    data = random.choice(scenarios)
    data["origin"] = origin
    data["destination"] = destination
    data["timestamp"] = datetime.now().isoformat()
    return data


# --------------------------------------------------------------------------- #
# Historical Commute Patterns (personalization)
# --------------------------------------------------------------------------- #

def get_historical_commute_patterns(
    user_id: str,
    origin: str,
    destination: str,
) -> dict:
    """
    Retrieve a user's historical commute patterns for personalized recommendations.

    Args:
        user_id: User identifier
        origin: Starting location
        destination: End destination

    Returns:
        dict with historical patterns and user preferences
    """
    now = datetime.now()
    hour = now.hour
    day = now.strftime("%A")

    return {
        "user_id": user_id,
        "preferred_mode": random.choice(["train", "bus", "drive"]),
        "average_commute_minutes": random.randint(32, 72),
        "typical_departure_time": f"{random.randint(7, 9):02d}:{random.choice(['00', '15', '30', '45'])}",
        "historical_patterns": [
            f"{day}s are typically {'busier than usual' if day in ['Monday', 'Friday'] else 'average'} on this route",
            f"{'Rush hour' if 7 <= hour <= 9 or 17 <= hour <= 19 else 'Off-peak'} travel detected — "
            f"{'expect crowding' if 7 <= hour <= 9 else 'capacity should be fine'}",
        ],
        "saved_routes": [
            {"name": "Primary", "mode": "train", "avg_minutes": random.randint(35, 50)},
            {"name": "Backup", "mode": "bus", "avg_minutes": random.randint(50, 70)},
            {"name": "Drive", "mode": "drive", "avg_minutes": random.randint(30, 65)},
        ],
        "accessibility_needs": None,
        "timestamp": now.isoformat(),
    }
