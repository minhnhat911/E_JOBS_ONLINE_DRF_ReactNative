from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    JobCategoryView,
    TagView,
    JobPostView,
    EmployerProfileView,
    CandidateProfileView,
    JobApplicationView,
    PaymentView,
    ApplicationReviewView,
    UserView,
    EmployerStatsView
)

router = DefaultRouter()
router.register('categories', JobCategoryView, basename='category')
router.register('tags', TagView, basename='tag')
router.register('jobs', JobPostView, basename='job')
router.register('employers', EmployerProfileView, basename='employer')
router.register('candidates', CandidateProfileView, basename='candidate')
router.register('job-applications', JobApplicationView, basename='job-application')
router.register('payments', PaymentView, basename='payment')
router.register('application-reviews', ApplicationReviewView, basename='application-review')
router.register('users', UserView, basename='user')

urlpatterns = [
    path('', include(router.urls)),

    # thống kê cho nhà tuyển dụng
    path(
        'stats/employer/',
        EmployerStatsView.as_view(),
        name='employer-stats'
    ),
]
