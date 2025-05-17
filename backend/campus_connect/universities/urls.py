from django.urls import path
from .views import (
    UniversityListView, AcademicUnitListView,
    TeacherDesignationListView, UniversityUsersView
)

app_name = 'universities'

urlpatterns = [
    path('', UniversityListView.as_view(), name='university-list'),
    path('academic-units/', AcademicUnitListView.as_view(), name='academic-unit-list'),
    path('teacher-designations/', TeacherDesignationListView.as_view(), name='teacher-designation-list'),
    path('<str:university_short_name>/users/', UniversityUsersView.as_view(), name='university-users'),
]