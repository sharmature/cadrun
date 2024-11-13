# siteplans/urls.py

from django.urls import path
from . import views

app_name = 'siteplans'

urlpatterns = [
    path('', views.siteplan_landing, name='siteplan_landing'),  # Landing page for site plans
    path('draw/', views.create_site_plan, name='create_site_plan'),  # Create a new site plan
    path('preview/<int:site_plan_id>/', views.drawing_preview, name='drawing_preview'),  # Preview an existing site plan
]
