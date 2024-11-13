from django.urls import path
from .views import landing_page, drawing_board, drawing_preview_template

urlpatterns = [
    path('', landing_page, name='landing_page'),  # Set the landing page as the home page
    path('drawing-board/', drawing_board, name='drawing_board'),  # New DrawingBoard page
    path('drawing-preview/', drawing_preview_template, name='drawing_preview'),  # New DrawingPreview page
]