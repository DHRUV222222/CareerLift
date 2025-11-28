from django.urls import path
from . import session_views

# Define app_name for URL namespacing
app_name = 'sessions'

# Define urlpatterns as a list of URL patterns
urlpatterns = [
    # Mentor listing and session booking
    path('mentors/', session_views.MentorListView.as_view(), name='mentor_list'),
    path('mentors/<int:mentor_id>/book/', session_views.BookSessionView.as_view(), name='book_session'),
    
    # Session management
    path('sessions/<int:pk>/', session_views.SessionDetailView.as_view(), name='session_detail'),
    path('sessions/<int:pk>/update/', session_views.SessionUpdateView.as_view(), name='update_session'),
    path('sessions/<int:pk>/cancel/', session_views.cancel_session, name='cancel_session'),
]
