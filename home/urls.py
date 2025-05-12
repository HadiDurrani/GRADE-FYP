# from django.urls import path
# from . import views

# app_name = 'home'

# urlpatterns = [
#     path('', views.home, name='home'),  # Root URL for the home app
#     path('learnmore/', views.learnmore, name='learnmore'), #learn more page
#     path("sandbox/", views.sandbox, name="sandbox"),
#     path('signup/', views.signup, name='signup'),
#     path('login/', views.login_view, name='login'),
#     path("teacher-dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
#     path("generate-assignment/", views.generate_assignment, name="generate_assignment"),
#     path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
#     path('logout/', views.logout_view, name='logout'),
# ]

from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home, name='home'),
    path('learnmore/', views.learnmore, name='learnmore'),
    path("sandbox/", views.sandbox, name="sandbox"),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path("teacher-dashboard/", views.teacher_dashboard, name="teacher_dashboard"),
    path("generate-assignment/", views.generate_assignment, name="generate_assignment"),
    path("student-dashboard/", views.student_dashboard, name="student_dashboard"),
    path('logout/', views.logout_view, name='logout'),

    # ✅ FIX: Change <int:class_id> to <str:class_id> for MongoDB compatibility
    path("manage-classes/", views.manage_classes, name="manage_classes"),
    path("class-details/<str:class_id>/", views.class_details, name="class_details"),  # Now accepts ObjectId
    path("student-classes/", views.student_classes, name="student_classes"),
    path("delete-class/<str:class_id>/", views.delete_class, name="delete_class"),
]
