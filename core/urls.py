from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .resume_views import (ResumeListView, ResumeCreateView, 
                          ResumeUpdateView, ResumeDeleteView, 
                          SetPrimaryResumeView, ResumeDownloadView)
from .project_views import (ProjectListView, ProjectCreateView, 
                           ProjectUpdateView, ProjectDeleteView, 
                           ProjectDetailView, ProjectImageDeleteView)
from . import session_urls
from .mentor_views import (MentorSessionRequestsView, UpdateSessionStatusView, 
                         MentorUpcomingSessionsView, MentorCompletedSessionsView,
                         MentorAvailabilityView, MentorSessionsView, SessionUpdateView, SessionDeleteView)

app_name = 'core'

urlpatterns = [
    # Home
    path('', views.HomeView.as_view(), name='home'),
    
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        authentication_form=views.UserLoginForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logged_out.html',
        next_page='core:login'
    ), name='logout'),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        subject_template_name='registration/password_reset_subject.txt',
        success_url='password_reset_done/',
        html_email_template_name='registration/password_reset_email.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html',
        success_url='/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('mentor/profile/update/', views.ProfileView.as_view(), name='mentor_profile_update'),
    path('mentor/availability/', MentorAvailabilityView.as_view(), name='mentor_availability'),
    
    # Dashboards
    path('student/dashboard/', views.StudentDashboardView.as_view(), name='student_dashboard'),
    
    # Mentor session management
    path('mentor/sessions/', MentorSessionsView.as_view(), name='mentor_sessions'),
    path('mentor/sessions/requests/', MentorSessionRequestsView.as_view(), name='mentor_session_requests'),
    path('mentor/sessions/upcoming/', MentorUpcomingSessionsView.as_view(), name='mentor_upcoming_sessions'),
    path('mentor/sessions/completed/', MentorCompletedSessionsView.as_view(), name='mentor_completed_sessions'),
    path('mentor/sessions/<int:pk>/', SessionUpdateView.as_view(), name='mentor_session_update'),
    path('mentor/sessions/<int:pk>/delete/', SessionDeleteView.as_view(), name='mentor_session_delete'),
    path('sessions/<int:pk>/update-status/', UpdateSessionStatusView.as_view(), name='update_session_status'),
    path('mentor/dashboard/', views.MentorDashboardView.as_view(), name='mentor_dashboard'),
    
    # Resume Management
    path('resumes/', ResumeListView.as_view(), name='resume_list'),
    path('resumes/upload/', ResumeCreateView.as_view(), name='resume_upload'),
    path('resumes/<int:pk>/edit/', ResumeUpdateView.as_view(), name='resume_edit'),
    path('resumes/<int:pk>/delete/', ResumeDeleteView.as_view(), name='resume_delete'),
    path('resumes/<int:pk>/set-primary/', SetPrimaryResumeView.as_view(), name='set_primary_resume'),
    path('resumes/<int:pk>/download/', ResumeDownloadView.as_view(), name='resume_download'),
    
    # Projects
    path('projects/', include([
        path('', ProjectListView.as_view(), name='project_list'),
        path('create/', ProjectCreateView.as_view(), name='project_create'),
        path('<int:pk>/', ProjectDetailView.as_view(), name='project_detail'),
        path('<int:pk>/update/', ProjectUpdateView.as_view(), name='project_update'),
        path('<int:pk>/delete/', ProjectDeleteView.as_view(), name='project_delete'),
        path('project-images/<int:pk>/delete/', ProjectImageDeleteView.as_view(), name='project_image_delete'),
    ])),
    
    # Sessions
    path('sessions/', include(('core.session_urls', 'sessions'), namespace='sessions')),
]