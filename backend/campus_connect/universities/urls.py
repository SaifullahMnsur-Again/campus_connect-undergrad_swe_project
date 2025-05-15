from django.urls import path
from .views import (
    UniversityListView, DepartmentListView, InstituteListView,
    TeacherDesignationListView, DepartmentInstituteListView, UniversityUsersView
)

urlpatterns = [
    path('', UniversityListView.as_view(), name='university-list'),
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('institutes/', InstituteListView.as_view(), name='institute-list'),
    path('teacher-designations/', TeacherDesignationListView.as_view(), name='teacher-designation-list'),
    path('departments-institutes/', DepartmentInstituteListView.as_view(), name='department-institute-list'),
    path('<str:university_short_name>/users/', UniversityUsersView.as_view(), name='university-users'),
]