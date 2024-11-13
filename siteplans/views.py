from django.shortcuts import render, redirect, get_object_or_404
from .forms import SitePlanForm
from .models import SitePlan, BoundaryPoint
from django.http import HttpResponse
from django.contrib import messages
from .utils.drawing import generate_site_plan_image
from .utils.zoning import ALL_CITY_ZONINGS
import logging

# Configure logging
logger = logging.getLogger(__name__)

def siteplan_landing(request):
    return render(request, 'siteplans/landing.html')

def drawing_preview(request, site_plan_id):
    site_plan = get_object_or_404(SitePlan, id=site_plan_id)
    boundary_points = site_plan.boundary_points.all()

    if boundary_points.count() < 2:
        messages.error(request, "Insufficient boundary points to generate a preview.")
        return redirect('siteplans:create_site_plan')

    try:
        img_str = generate_site_plan_image(site_plan, boundary_points, ALL_CITY_ZONINGS)
    except Exception as e:
        logger.error(f"Error generating site plan image: {e}")
        messages.error(request, f"Error generating site plan image: {e}")
        return redirect('siteplans:create_site_plan')

    context = {
        'site_name': site_plan.site_name,
        'address': site_plan.address,
        'base64_img': img_str,
    }
    return render(request, 'frontend/drawing_preview.html', context)

def validate_boundary_point(direction1, direction2, angle_degrees, angle_minutes, angle_seconds, length, index):
    if direction1.upper() not in ['N', 'S']:
        logger.error(f"Invalid primary direction: {direction1} at Boundary Point {index}")
        return False
    if direction2.upper() not in ['E', 'W']:
        logger.error(f"Invalid secondary direction: {direction2} at Boundary Point {index}")
        return False

    try:
        angle_deg = int(angle_degrees)
        angle_min = int(angle_minutes)
        angle_sec = int(angle_seconds)
        if not (0 <= angle_deg <= 90 and 0 <= angle_min < 60 and 0 <= angle_sec < 60):
            raise ValueError("Angles out of valid range.")
    except ValueError as e:
        logger.error(f"Invalid angles at Boundary Point {index}: {e}")
        return False

    try:
        length = float(length)
        if length <= 0:
            raise ValueError("Length must be positive.")
    except ValueError as e:
        logger.error(f"Invalid length at Boundary Point {index}: {e}")
        return False

    return True

def create_site_plan(request):
    if request.method == 'POST':
        form = SitePlanForm(request.POST)
        if form.is_valid():
            site_plan = form.save()
            index = 1
            while True:
                direction1 = request.POST.get(f'D{index}')
                angle_degrees = request.POST.get(f'AD{index}')
                angle_minutes = request.POST.get(f'AM{index}')
                direction2 = request.POST.get(f'DO{index}')
                length = request.POST.get(f'L{index}')

                if not direction1:
                    break

                angle_seconds = request.POST.get(f'AS{index}', 0)

                if validate_boundary_point(direction1, direction2, angle_degrees, angle_minutes, angle_seconds, length, index):
                    BoundaryPoint.objects.create(
                        site_plan=site_plan,
                        direction1=direction1.upper(),
                        angle_degrees=int(angle_degrees),
                        angle_minutes=int(angle_minutes),
                        angle_seconds=int(angle_seconds),
                        direction2=direction2.upper(),
                        length=float(length)
                    )
                index += 1
            return redirect('siteplans:drawing_preview', site_plan_id=site_plan.id)
    else:
        form = SitePlanForm()
    return render(request, 'frontend/drawing_board.html', {'form': form})
