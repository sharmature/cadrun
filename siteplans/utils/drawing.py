# siteplans/utils/drawing.py

import math
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
from .zoning import ALL_CITY_ZONINGS
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_city_zoning(city_name):
    """
    Retrieve zoning rules for the given city.
    """
    for zoning in ALL_CITY_ZONINGS:
        if zoning.city_name.lower() == city_name.lower():
            return zoning
    logger.warning(f"No zoning rules found for city: {city_name}")
    return None

def quadrant_to_azimuth(direction1, direction2, angle_deg, angle_min, angle_sec):
    """
    Converts quadrant bearings to azimuth angles.
    """
    angle = angle_deg + angle_min / 60 + angle_sec / 3600
    direction1 = direction1.upper()
    direction2 = direction2.upper()

    if direction1 == 'N':
        if direction2 == 'E':
            azimuth = angle
        elif direction2 == 'W':
            azimuth = 360 - angle
        else:
            raise ValueError(f"Invalid direction2: {direction2}")
    elif direction1 == 'S':
        if direction2 == 'E':
            azimuth = 180 - angle
        elif direction2 == 'W':
            azimuth = 180 + angle
        else:
            raise ValueError(f"Invalid direction2: {direction2}")
    else:
        raise ValueError(f"Invalid direction1: {direction1}")

    return azimuth % 360

def apply_zoning_rules(site_plan, boundary_points, city_zoning):
    """
    Applies zoning rules to determine setbacks and easements based on boundary directions.
    """
    easements = []
    for bp in boundary_points:
        # Find the zoning rule for the current boundary direction
        rule = city_zoning.rules.get(bp.direction2.upper())
        if not rule:
            logger.warning(f"No zoning rule found for boundary direction: {bp.direction2}")
            continue  # No zoning rule found for this boundary

        # Apply setbacks
        if rule.setback_landscape > 0:
            easements.append({
                'boundary_direction': bp.direction2.upper(),
                'type': 'Landscape Setback',
                'length': rule.setback_landscape
            })

        # Apply easements
        if rule.easement_landscape > 0:
            easements.append({
                'boundary_direction': bp.direction2.upper(),
                'type': 'Landscape Easement',
                'length': rule.easement_landscape
            })
        if rule.easement_utility > 0:
            easements.append({
                'boundary_direction': bp.direction2.upper(),
                'type': 'Utility Easement',
                'length': rule.easement_utility
            })
    return easements

def draw_dashed_line(draw, start, end, fill, width, dash_type):
    """
    Draws dashed or dotted lines on the image.

    Parameters:
    - draw: ImageDraw.Draw object
    - start: Tuple (x, y) for the start point
    - end: Tuple (x, y) for the end point
    - fill: Color of the line
    - width: Width of the line
    - dash_type: 'dotted', 'dashed', or 'dashdot'
    """
    x1, y1 = start
    x2, y2 = end

    if dash_type == 'dotted':
        dash_length = 5
        gap_length = 5
        pattern = [dash_length, gap_length]
    elif dash_type == 'dashed':
        dash_length = 10
        gap_length = 5
        pattern = [dash_length, gap_length]
    elif dash_type == 'dashdot':
        dash_length = 15
        gap_length = 5
        pattern = [dash_length, gap_length, dash_length // 3, gap_length]
    else:
        pattern = None

    if pattern:
        total_length = math.hypot(x2 - x1, y2 - y1)
        angle = math.atan2(y2 - y1, x2 - x1)
        cos_angle = math.cos(angle)
        sin_angle = math.sin(angle)

        pos = 0
        while pos < total_length:
            for segment_length in pattern:
                if pos >= total_length:
                    break
                current_dash = min(segment_length, total_length - pos)
                x_start = x1 + cos_angle * pos
                y_start = y1 + sin_angle * pos
                x_end = x1 + cos_angle * (pos + current_dash)
                y_end = y1 + sin_angle * (pos + current_dash)
                draw.line([(x_start, y_start), (x_end, y_end)], fill=fill, width=width)
                pos += segment_length
    else:
        draw.line([start, end], fill=fill, width=width)

def add_legend(draw, margin, font):
    """
    Adds a legend to the image explaining line styles.

    Parameters:
    - draw: ImageDraw.Draw object
    - margin: Margin in pixels
    - font: ImageFont object
    """
    legend_x = margin + 10
    legend_y = margin + 10
    legend_spacing = 30

    legend_items = [
        {'type': 'Boundary', 'style': 'solid', 'color': 'black'},
        {'type': 'Landscape Setback', 'style': 'dotted', 'color': 'green'},
        {'type': 'Landscape Easement', 'style': 'dashed', 'color': 'orange'},
        {'type': 'Utility Easement', 'style': 'dashdot', 'color': 'blue'},
    ]

    for idx, item in enumerate(legend_items):
        y_position = legend_y + idx * legend_spacing
        start = (legend_x, y_position)
        end = (legend_x + 50, y_position)
        if item['style'] in ['dotted', 'dashed', 'dashdot']:
            draw_dashed_line(draw, start, end, fill=item['color'], width=2, dash_type=item['style'])
        else:
            draw.line([start, end], fill=item['color'], width=2)
        
        # Add text
        draw.text((legend_x + 60, y_position - 10), item['type'], fill='black', font=font)

def calculate_offset_point(x, y, offset_distance, azimuth):
    """
    Calculates a new point offset from (x, y) by offset_distance in the direction of azimuth.

    Parameters:
    - x, y: Original coordinates
    - offset_distance: Distance to offset (in pixels)
    - azimuth: Angle in degrees (0-360)

    Returns:
    - Tuple (new_x, new_y)
    """
    rad = math.radians(azimuth)
    new_x = x + offset_distance * math.sin(rad)
    new_y = y - offset_distance * math.cos(rad)  # Invert y-axis for image coordinates
    return (new_x, new_y)

def generate_site_plan_image(site_plan, boundary_points, zoning_rules, scale=30, ppi=96, margin=100):
    """
    Generates a site plan image with boundaries, setbacks, and easements.

    Parameters:
    - site_plan: SitePlan instance
    - boundary_points: QuerySet of BoundaryPoint instances
    - zoning_rules: List of CityZoning instances
    - scale: Scale in feet per inch
    - ppi: Pixels per inch
    - margin: Margin in pixels

    Returns:
    - Base64 encoded PNG image string
    """
    PPF = ppi / scale  # Pixels per foot

    # Retrieve zoning for the site_plan's city
    city_zoning = get_city_zoning(site_plan.city.name)
    if not city_zoning:
        logger.error(f"No zoning rules found for city: {site_plan.city.name}")
        raise ValueError(f"No zoning rules found for city: {site_plan.city.name}")

    # Initialize starting point
    current_x, current_y = 0, 0
    points = [(current_x, current_y)]

    # Track min and max coordinates for dynamic sizing
    min_x, min_y = current_x, current_y
    max_x, max_y = current_x, current_y

    # Plot boundaries
    for bp in boundary_points:
        try:
            azimuth = quadrant_to_azimuth(
                bp.direction1,
                bp.direction2,
                bp.angle_degrees,
                bp.angle_minutes,
                bp.angle_seconds
            )
            logger.debug(f"Boundary Point {bp.id}: Azimuth={azimuth}")
        except ValueError as e:
            logger.error(f"Error converting azimuth for Boundary Point {bp.id}: {e}")
            continue  # Skip this boundary point

        rad = math.radians(azimuth)
        delta_x = bp.length * PPF * math.sin(rad)
        delta_y = -bp.length * PPF * math.cos(rad)  # Invert y-axis for image coordinates

        new_x = current_x + delta_x
        new_y = current_y + delta_y

        points.append((new_x, new_y))

        # Update min and max
        min_x = min(min_x, new_x)
        min_y = min(min_y, new_y)
        max_x = max(max_x, new_x)
        max_y = max(max_y, new_y)

        # Update current position
        current_x, current_y = new_x, new_y

    # Apply zoning rules to determine setbacks and easements
    easement_objs = apply_zoning_rules(site_plan, boundary_points, city_zoning)

    # Calculate positions for easements and setbacks based on boundaries
    easement_points = []
    for easement in easement_objs:
        # Find the boundary point corresponding to the easement's boundary direction
        bp = boundary_points.filter(direction2=easement['boundary_direction']).first()
        if not bp:
            logger.warning(f"No boundary point found for easement direction: {easement['boundary_direction']}")
            continue  # Skip if no boundary point found

        try:
            azimuth = quadrant_to_azimuth(
                bp.direction1,
                bp.direction2,
                bp.angle_degrees,
                bp.angle_minutes,
                bp.angle_seconds
            )
        except ValueError as e:
            logger.error(f"Error converting azimuth for Easement {easement['type']}: {e}")
            continue  # Skip this easement

        # Offset distance in pixels
        offset_distance = easement['length'] * PPF

        # Calculate the perpendicular azimuth (for setbacks and easements)
        perp_azimuth = (azimuth + 90) % 360

        # Calculate the offset point (inner boundary)
        inner_start = calculate_offset_point(current_x, current_y, offset_distance, perp_azimuth)

        inner_end = calculate_offset_point(inner_start[0], inner_start[1], offset_distance, perp_azimuth)
        
        # Label Easement
        easement_label = f"{easement['type']} {easement['length']}ft"

        easement_points.append({
            'type': easement['type'],
            'start': inner_start,
            'end': inner_end,
            'label': easement_label
        })

        # Update min and max for image sizing
        min_x = min(min_x, inner_start[0], inner_end[0])
        min_y = min(min_y, inner_start[1], inner_end[1])
        max_x = max(max_x, inner_start[0], inner_end[0])
        max_y = max(max_y, inner_start[1], inner_end[1])

    # Determine image size with margins
    width = int(math.ceil(max_x - min_x)) + 2 * margin
    height = int(math.ceil(max_y - min_y)) + 2 * margin

    # Shift points to fit within the image with margins
    shifted_points = [(
        int(x - min_x) + margin,
        int(y - min_y) + margin
    ) for (x, y) in points]

    # Shift easement points and add labels
    shifted_easements = []
    for easement in easement_points:
        shifted_start = (
            int(easement['start'][0] - min_x) + margin,
            int(easement['start'][1] - min_y) + margin
        )
        shifted_end = (
            int(easement['end'][0] - min_x) + margin,
            int(easement['end'][1] - min_y) + margin
        )
        shifted_easements.append({
            'type': easement['type'],
            'start': shifted_start,
            'end': shifted_end,
            'label': easement['label']
        })

    # Create Image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw outer boundaries
    draw.line(shifted_points, fill='black', width=3)

    # Draw easements and setbacks as inner boundaries
    for easement in shifted_easements:
        if 'Setback' in easement['type']:
            line_style = 'dotted'
            fill = 'green'
        elif 'Easement' in easement['type']:
            if 'Landscape' in easement['type']:
                line_style = 'dashed'
                fill = 'orange'
            elif 'Utility' in easement['type']:
                line_style = 'dashdot'
                fill = 'blue'
            else:
                line_style = 'solid'
                fill = 'gray'
        else:
            line_style = 'solid'
            fill = 'gray'

        if line_style in ['dotted', 'dashed', 'dashdot']:
            draw_dashed_line(draw, easement['start'], easement['end'], fill=fill, width=2, dash_type=line_style)
        else:
            draw.line([easement['start'], easement['end']], fill=fill, width=2)

        # Draw label for easement
        label_x, label_y = (easement['start'][0] + 10, easement['start'][1] - 10)
        draw.text((label_x, label_y), easement['label'], fill='black', font=ImageFont.load_default())

    # Add markers for each boundary point for debugging (optional)
    for idx, (x, y) in enumerate(shifted_points):
        draw.ellipse((x-5, y-5, x+5, y+5), fill='red', outline='black')
        draw.text((x + 10, y - 10), f"P{idx}", fill='blue', font=ImageFont.load_default())

    # Add a legend
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
        logger.warning("Arial font not found. Using default font.")

    add_legend(draw, margin, font)

    # Convert image to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    return img_str

