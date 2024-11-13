from django.shortcuts import render, redirect
from django.contrib import messages

def landing_page(request):
    return render(request, 'frontend/landing_page.html')

def drawing_board(request):
    if request.method == 'POST':
        # Handle form submission here
        site_name = request.POST.get('site_name')
        address = request.POST.get('address')
        # Extract other form fields as needed...

        # Assuming form data is correct and valid for now.
        # For full form processing, consider adding Django form classes and validation logic.

        if site_name and address:
            # Generate preview image here - for now we'll use a placeholder
            base64_img = "placeholder_base64_encoded_image"

            # Pass the collected data to the preview template
            context = {
                'site_name': site_name,
                'address': address,
                'base64_img': base64_img,
            }
            return render(request, 'frontend/drawing_preview.html', context)
        else:
            # Flash an error message if important data is missing
            messages.error(request, "Please fill in all required fields.")
            return redirect('drawing_board')

    return render(request, 'frontend/drawing_board.html')

def drawing_preview_template(request):
    # To prevent direct access without context data, redirect back to drawing board
    if request.method == 'POST':
        # This means user accessed from drawing_board form submission (which is valid)
        return render(request, 'frontend/drawing_preview.html')

    # If someone tries to directly access this page without submitting data
    messages.warning(request, "You need to submit a site plan before viewing the preview.")
    return redirect('drawing_board')
