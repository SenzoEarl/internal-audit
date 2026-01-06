from django.urls import path

from audit.views import (
    IndexView, Dashboard, LoginAjaxView, ClientDashboard, ReportDashboard,
    LogoutAjaxView, ClientDetailAjaxView, ClientUpdateAjaxView,
    AuditDetailView, AuditCreateView, AuditShareAjaxView,

)

app_name = 'audit'
urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path('dashboard/', Dashboard.as_view(), name='dashboard'),
    path('login-ajax/', LoginAjaxView.as_view(), name='login-ajax'),
    path('logout-ajax/', LogoutAjaxView.as_view(), name='logout-ajax'),
    path('clients/', ClientDashboard.as_view(), name='client-dashboard'),
    path('clients/<int:pk>/', ClientDetailAjaxView.as_view(), name='client-detail-ajax'),
    path('clients/<int:pk>/update/', ClientUpdateAjaxView.as_view(), name='client-update-ajax'),
    # Page view for client detail/edit
    # path('clients/<int:pk>/view/', ClientDetailView.as_view(), name='client-detail-view'),
    path('reports/', ReportDashboard.as_view(), name='report-dashboard'),
    path('reports/create/', AuditCreateView.as_view(), name='report-create-ajax'),
    path('reports/<int:pk>/', AuditDetailView.as_view(), name='report-detail'),
    path('reports/<int:pk>/share/', AuditShareAjaxView.as_view(), name='report-share-ajax'),
]