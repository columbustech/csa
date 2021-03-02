from django.urls import path
from . import views

urlpatterns = [
    path('specs/', views.Specs.as_view()),
    path('access-token/', views.AuthenticationToken.as_view()),
    path('execute/', views.ExecuteJob.as_view()),
    path('status/', views.JobStatus.as_view())
]
