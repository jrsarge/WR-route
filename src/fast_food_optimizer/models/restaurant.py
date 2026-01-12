"""Data models for restaurant information.

This module defines the core Restaurant dataclass and supporting models for
representing fast food restaurant data collected from Google Maps API.

CRITICAL: Each unique place_id represents a distinct physical location.
Multiple restaurants can have the same name (chain locations).
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator

from fast_food_optimizer.utils.exceptions import DataValidationError


class Coordinates(BaseModel):
    """Geographic coordinates with validation.

    Attributes:
        latitude: Latitude in decimal degrees (-90 to 90)
        longitude: Longitude in decimal degrees (-180 to 180)
    """

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """Validate latitude is within valid range."""
        if not -90 <= v <= 90:
            raise DataValidationError(
                f"Invalid latitude: {v}. Must be between -90 and 90.",
                error_code="VAL_001",
                context={"latitude": v, "expected_range": "[-90, 90]"},
            )
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """Validate longitude is within valid range."""
        if not -180 <= v <= 180:
            raise DataValidationError(
                f"Invalid longitude: {v}. Must be between -180 and 180.",
                error_code="VAL_001",
                context={"longitude": v, "expected_range": "[-180, 180]"},
            )
        return v

    def to_tuple(self) -> Tuple[float, float]:
        """Convert to (latitude, longitude) tuple."""
        return (self.latitude, self.longitude)

    def __str__(self) -> str:
        """String representation of coordinates."""
        return f"({self.latitude:.6f}, {self.longitude:.6f})"


class DayHours(BaseModel):
    """Operating hours for a single day.

    Attributes:
        open_time: Opening time (HH:MM format, 24-hour)
        close_time: Closing time (HH:MM format, 24-hour)
        is_open_24h: True if open 24 hours
        is_closed: True if closed all day
    """

    open_time: Optional[str] = None
    close_time: Optional[str] = None
    is_open_24h: bool = False
    is_closed: bool = False

    @field_validator("open_time", "close_time")
    @classmethod
    def validate_time_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate time is in HH:MM format."""
        if v is None:
            return v

        try:
            # Validate format by parsing
            hours, minutes = v.split(":")
            h, m = int(hours), int(minutes)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
            return v
        except (ValueError, AttributeError):
            raise DataValidationError(
                f"Invalid time format: {v}. Expected HH:MM (24-hour).",
                error_code="VAL_003",
                context={"time": v, "expected_format": "HH:MM"},
            )

    def is_open_at(self, check_time: time) -> bool:
        """Check if location is open at specific time.

        Args:
            check_time: Time to check

        Returns:
            True if open at that time
        """
        if self.is_closed:
            return False
        if self.is_open_24h:
            return True
        if not self.open_time or not self.close_time:
            return False

        # Parse times
        open_h, open_m = map(int, self.open_time.split(":"))
        close_h, close_m = map(int, self.close_time.split(":"))

        open_minutes = open_h * 60 + open_m
        close_minutes = close_h * 60 + close_m
        check_minutes = check_time.hour * 60 + check_time.minute

        # Handle overnight hours (e.g., 22:00 to 02:00)
        if close_minutes < open_minutes:
            return check_minutes >= open_minutes or check_minutes <= close_minutes
        else:
            return open_minutes <= check_minutes <= close_minutes


class OperatingHours(BaseModel):
    """Weekly operating hours for a restaurant.

    Attributes:
        monday through sunday: Operating hours for each day
        notes: Optional notes about hours (e.g., "Holiday hours may vary")
    """

    monday: Optional[DayHours] = None
    tuesday: Optional[DayHours] = None
    wednesday: Optional[DayHours] = None
    thursday: Optional[DayHours] = None
    friday: Optional[DayHours] = None
    saturday: Optional[DayHours] = None
    sunday: Optional[DayHours] = None
    notes: Optional[str] = None

    def is_open_on_day(self, day_name: str, check_time: Optional[time] = None) -> bool:
        """Check if open on a specific day and optionally at a specific time.

        Args:
            day_name: Day of week (e.g., "monday", "tuesday")
            check_time: Optional time to check

        Returns:
            True if open
        """
        day_hours = getattr(self, day_name.lower(), None)
        if not day_hours:
            return False

        if check_time:
            return day_hours.is_open_at(check_time)
        else:
            return not day_hours.is_closed


@dataclass
class Restaurant:
    """Restaurant location data model.

    CRITICAL: place_id is the unique identifier. Multiple restaurants can
    share the same name (e.g., multiple McDonald's locations). This is
    intentional and valuable for route optimization.

    Attributes:
        place_id: Google Places unique identifier (PRIMARY KEY)
        name: Restaurant/chain name (CAN be duplicate across locations)
        address: Physical street address
        coordinates: GPS coordinates (lat, lng)
        place_types: Google Places types (e.g., ['restaurant', 'food'])
        operating_hours: Weekly operating schedule
        phone: Phone number (optional)
        website: Website URL (optional)
        rating: Google rating 0-5 (optional)
        is_fast_food: True if classified as fast food
        confidence_score: Classification confidence 0-1
        cluster_id: Assigned cluster ID (None until clustered)
        last_updated: When data was collected/updated
    """

    place_id: str
    name: str
    address: str
    coordinates: Coordinates
    place_types: List[str] = field(default_factory=list)
    operating_hours: Optional[OperatingHours] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    is_fast_food: bool = False
    confidence_score: float = 0.0
    cluster_id: Optional[int] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate restaurant data after initialization."""
        # Validate required fields
        if not self.place_id or len(self.place_id.strip()) < 10:
            raise DataValidationError(
                "Invalid or missing place_id",
                error_code="VAL_002",
                context={"place_id": self.place_id},
            )

        if not self.name or len(self.name.strip()) < 2:
            raise DataValidationError(
                "Restaurant name missing or too short",
                error_code="VAL_002",
                context={"name": self.name},
            )

        # Validate rating if present
        if self.rating is not None and not (0 <= self.rating <= 5):
            raise DataValidationError(
                f"Invalid rating: {self.rating}. Must be between 0 and 5.",
                error_code="VAL_003",
                context={"rating": self.rating, "expected_range": "[0, 5]"},
            )

        # Validate confidence score
        if not (0 <= self.confidence_score <= 1):
            raise DataValidationError(
                f"Invalid confidence score: {self.confidence_score}. Must be between 0 and 1.",
                error_code="VAL_003",
                context={"confidence_score": self.confidence_score},
            )

    def distance_to(self, other: "Restaurant") -> float:
        """Calculate distance to another restaurant in kilometers.

        Uses Haversine formula for great circle distance.

        Args:
            other: Another Restaurant instance

        Returns:
            Distance in kilometers
        """
        from math import asin, cos, radians, sin, sqrt

        lat1, lon1 = self.coordinates.to_tuple()
        lat2, lon2 = other.coordinates.to_tuple()

        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        # Earth radius in kilometers
        r = 6371.0

        return c * r

    def is_open_now(self) -> Optional[bool]:
        """Check if restaurant is currently open.

        Returns:
            True if open, False if closed, None if hours unknown
        """
        if not self.operating_hours:
            return None

        now = datetime.now()
        day_name = now.strftime("%A").lower()
        current_time = now.time()

        return self.operating_hours.is_open_on_day(day_name, current_time)

    def to_dict(self) -> dict:
        """Convert restaurant to dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "coordinates": {
                "latitude": self.coordinates.latitude,
                "longitude": self.coordinates.longitude,
            },
            "place_types": self.place_types,
            "operating_hours": (
                self.operating_hours.model_dump() if self.operating_hours else None
            ),
            "phone": self.phone,
            "website": self.website,
            "rating": self.rating,
            "is_fast_food": self.is_fast_food,
            "confidence_score": self.confidence_score,
            "cluster_id": self.cluster_id,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Restaurant":
        """Create Restaurant from dictionary.

        Args:
            data: Dictionary with restaurant data

        Returns:
            Restaurant instance
        """
        # Parse coordinates
        coords_data = data.get("coordinates", {})
        coordinates = Coordinates(
            latitude=coords_data.get("latitude"),
            longitude=coords_data.get("longitude"),
        )

        # Parse operating hours if present
        operating_hours = None
        if data.get("operating_hours"):
            operating_hours = OperatingHours(**data["operating_hours"])

        # Parse last_updated
        last_updated = datetime.fromisoformat(data.get("last_updated", datetime.utcnow().isoformat()))

        return cls(
            place_id=data["place_id"],
            name=data["name"],
            address=data.get("address", ""),
            coordinates=coordinates,
            place_types=data.get("place_types", []),
            operating_hours=operating_hours,
            phone=data.get("phone"),
            website=data.get("website"),
            rating=data.get("rating"),
            is_fast_food=data.get("is_fast_food", False),
            confidence_score=data.get("confidence_score", 0.0),
            cluster_id=data.get("cluster_id"),
            last_updated=last_updated,
        )

    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return f"Restaurant('{self.name}', {self.address}, place_id={self.place_id[:12]}...)"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Restaurant("
            f"place_id={self.place_id!r}, "
            f"name={self.name!r}, "
            f"address={self.address!r}, "
            f"coordinates={self.coordinates}, "
            f"is_fast_food={self.is_fast_food}"
            f")"
        )
