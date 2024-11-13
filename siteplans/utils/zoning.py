# siteplans/utils/zoning.py

from dataclasses import dataclass
from typing import Dict
from venv import logger

@dataclass
class ZoningRule:
    boundary_direction: str  # 'N', 'S', 'E', 'W'
    setback_landscape: float = 0.0  # in feet
    easement_landscape: float = 0.0  # in feet
    easement_utility: float = 0.0  # in feet

@dataclass
class CityZoning:
    city_name: str
    rules: Dict[str, ZoningRule]  # Keyed by boundary_direction

# Helper function to create uniform zoning rules for all directions
def create_uniform_zoning(city_name, setback_landscape, easement_landscape, easement_utility):
    return CityZoning(
        city_name=city_name,
        rules={
            direction: ZoningRule(
                boundary_direction=direction,
                setback_landscape=setback_landscape,
                easement_landscape=easement_landscape,
                easement_utility=easement_utility
            )
            for direction in ['N', 'S', 'E', 'W']
        }
    )

# Define zoning rules for Prosper, Texas
PROSPER_ZONING = create_uniform_zoning(
    city_name='Prosper',
    setback_landscape=5.0,
    easement_landscape=15.0,
    easement_utility=10.0
)

# Define zoning rules for CityX
CITYX_ZONING = CityZoning(
    city_name='CityX',
    rules={
        'N': ZoningRule(
            boundary_direction='N',
            setback_landscape=7.0,
            easement_landscape=20.0,
            easement_utility=12.0
        ),
        'S': ZoningRule(
            boundary_direction='S',
            setback_landscape=7.0,
            easement_landscape=20.0,
            easement_utility=12.0
        ),
        # Define for 'E', 'W' as needed...
    }
)

# Default Zoning for cities not defined
DEFAULT_ZONING = create_uniform_zoning(
    city_name='Default',
    setback_landscape=5.0,
    easement_landscape=10.0,
    easement_utility=8.0
)

# Aggregate all city zonings into a dictionary for efficient lookup
ALL_CITY_ZONINGS = {
    'Prosper': PROSPER_ZONING,
    'CityX': CITYX_ZONING,
    'Default': DEFAULT_ZONING,
}

# Function to get city zoning
def get_city_zoning(city_name):
    """
    Retrieve zoning rules for the given city.
    If the city is not found, return default zoning.
    """
    zoning = ALL_CITY_ZONINGS.get(city_name.capitalize(), DEFAULT_ZONING)
    if zoning.city_name == 'Default':
        logger.warning(f"No zoning rules found for city: {city_name}. Using default zoning.")
    return zoning
