"""
Pydantic schemas for structured commute data across all agent outputs.
Each model enforces typed, validated data flowing through session state.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class WeatherReport(BaseModel):
    location: str = Field(description="Location queried")
    temperature_celsius: float = Field(description="Current temperature in Celsius")
    conditions: str = Field(description="Weather conditions (sunny, rainy, foggy, snow, etc.)")
    precipitation_mm: float = Field(description="Precipitation in mm/hour")
    wind_speed_kmh: float = Field(description="Wind speed in km/h")
    visibility_km: float = Field(description="Visibility in km")
    commute_impact: Literal["low", "moderate", "high", "severe"] = Field(
        description="Impact level on commute"
    )
    advisory: Optional[str] = Field(default=None, description="Weather advisory if conditions are notable")


class TransitStatus(str):
    ON_TIME = "on_time"
    MINOR_DELAY = "minor_delay"
    MAJOR_DELAY = "major_delay"
    SUSPENDED = "suspended"
    DIVERTED = "diverted"


class TrainReport(BaseModel):
    line: str = Field(description="Train line name")
    origin: str = Field(description="Departure station")
    destination: str = Field(description="Arrival station")
    status: Literal["on_time", "minor_delay", "major_delay", "suspended", "diverted"] = Field(
        description="Current service status"
    )
    delay_minutes: int = Field(description="Current delay in minutes (0 if on time)")
    next_departure: str = Field(description="Next departure time (HH:MM or 'Service suspended')")
    platform: Optional[str] = Field(default=None, description="Platform number if known")
    disruptions: List[str] = Field(default_factory=list, description="Active disruptions")
    crowding_level: Literal["low", "moderate", "high"] = Field(description="Current crowding level")


class BusReport(BaseModel):
    route_number: str = Field(description="Bus route identifier")
    status: Literal["on_time", "minor_delay", "major_delay", "suspended", "diverted"] = Field(
        description="Current service status"
    )
    delay_minutes: int = Field(description="Current delay in minutes")
    next_arrival: str = Field(description="Next bus arrival time (HH:MM)")
    capacity_percent: int = Field(description="Current bus capacity as percentage (0-100)")
    disruptions: List[str] = Field(default_factory=list, description="Active service disruptions")
    alternate_routes: List[str] = Field(default_factory=list, description="Alternative route suggestions")


class TrafficReport(BaseModel):
    origin: str = Field(description="Journey start point")
    destination: str = Field(description="Journey end point")
    congestion_level: Literal["free_flow", "light", "moderate", "heavy", "standstill"] = Field(
        description="Current traffic congestion level"
    )
    incidents: List[str] = Field(default_factory=list, description="Active road incidents")
    estimated_delay_minutes: int = Field(description="Additional delay due to traffic in minutes")
    alternate_routes: List[str] = Field(default_factory=list, description="Suggested alternate routes")
    road_conditions: str = Field(description="Road surface conditions (dry, wet, icy, flooded)")
    travel_time_normal_minutes: int = Field(description="Baseline travel time in minutes")
    travel_time_current_minutes: int = Field(description="Current estimated travel time in minutes")


class CommuteRecommendation(BaseModel):
    """
    Structured commute recommendation produced by CommuteAnalyzer.
    Synthesizes weather, train, bus, and traffic data into a single actionable output.
    """
    overall_severity: Literal[
        "all_clear", "minor_disruption", "significant_disruption",
        "severe_disruption", "do_not_commute"
    ] = Field(description="Overall commute condition severity")
    recommended_mode: Literal["train", "bus", "drive", "walk", "work_from_home", "bike"] = Field(
        description="Best recommended commute mode given all conditions"
    )
    estimated_duration_minutes: int = Field(
        description="Estimated total journey duration in minutes"
    )
    confidence_score: float = Field(
        description="Recommendation confidence from 0.0 (uncertain) to 1.0 (highly confident)",
        ge=0.0,
        le=1.0
    )
    primary_alerts: List[str] = Field(
        description="Critical alerts the commuter must know before leaving"
    )
    actionable_advice: str = Field(
        description="Clear, specific guidance for the commuter in plain language"
    )
    backup_plan: Optional[str] = Field(
        default=None,
        description="Contingency plan if primary mode fails or worsens"
    )
    data_freshness: str = Field(description="ISO timestamp from most recent data source")
