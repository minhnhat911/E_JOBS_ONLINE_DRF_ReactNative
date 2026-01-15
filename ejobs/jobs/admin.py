from django.contrib import admin
from django.db.models import Count, Sum
from django.template.response import TemplateResponse
from django.utils.safestring import mark_safe
from django import forms
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django.urls import path
from .models import User, JobCategory, JobPost, Tag, EmployerProfile, CandidateProfile, JobApplication, Payment, ApplicationReview
from datetime import datetime
from django.db.models.functions import TruncMonth, TruncYear


class JobPostForm(forms.ModelForm):
    description = forms.CharField(widget=CKEditorUploadingWidget)
    requirements = forms.CharField(widget=CKEditorUploadingWidget)
    benefits = forms.CharField(widget=CKEditorUploadingWidget)

    class Meta:
        model = JobPost
        fields = '__all__'


class JobPostAdmin(admin.ModelAdmin):
    form = JobPostForm
    list_display = ['id', 'title', 'employer', 'category', 'status', 'is_featured', 'created_date']
    search_fields = ['title', 'employer__company_name']
    list_filter = ['category', 'status', 'is_featured', 'location']
    filter_horizontal = ['tags']


class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'user', 'is_approved', 'created_date']
    list_editable = ['is_approved']
    readonly_fields = ['logo_view']

    def logo_view(self, obj):
        if obj.logo:
            return mark_safe(f"<img src='{obj.logo.url}' width='100' />")
        return "No Logo"


class MyJobAdminSite(admin.AdminSite):
    site_header = 'HỆ THỐNG QUẢN TRỊ E-JOBS'
    site_title = 'Admin E-Jobs'
    index_title = 'Báo cáo & Thống kê hệ thống'

    def get_urls(self):
        return [
            path(
                'ejobs-stats/',
                self.admin_view(self.system_report),
                name='ejobs_stats'
            ),
        ] + super().get_urls()

    def system_report(self, request):
        try:
            selected_year = int(request.GET.get('year', datetime.now().year))
        except ValueError:
            selected_year = datetime.now().year

        total_jobs = JobPost.objects.count()
        total_candidates = CandidateProfile.objects.count()
        total_applications = JobApplication.objects.count()

        years = list(range(2000, 2030))

        jobs_by_month = (
            JobPost.objects
            .filter(created_date__year=selected_year)
            .annotate(month=TruncMonth('created_date'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )

        revenue_by_month = (
            Payment.objects
            .filter(
                status='SUCCESS',
                created_date__year=selected_year
            )
            .annotate(month=TruncMonth('created_date'))
            .values('month')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        revenue_by_year = (
            Payment.objects
            .filter(status='SUCCESS')
            .annotate(year=TruncYear('created_date'))
            .values('year')
            .annotate(total=Sum('amount'))
            .order_by('year')
        )

        return TemplateResponse(
            request,
            'admin/ejobs_stats.html',
            {
                'years': years,
                'selected_year': selected_year,
                'total_jobs': total_jobs,
                'total_candidates': total_candidates,
                'total_applications': total_applications,
                'jobs_by_month': jobs_by_month,
                'revenue_by_month': revenue_by_month,
                'revenue_by_year': revenue_by_year,
            }
        )


class ApplicationReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'application', 'employer', 'score', 'created_date']
    list_filter = ['score', 'created_date']
    search_fields = ['application__candidate__full_name', 'employer__company_name']


admin_site = MyJobAdminSite(name='myadmin')

admin_site.register(User)
admin_site.register(JobCategory)
admin_site.register(Tag)
admin_site.register(CandidateProfile)
admin_site.register(JobApplication)
admin_site.register(Payment)
admin_site.register(EmployerProfile, EmployerProfileAdmin)
admin_site.register(JobPost, JobPostAdmin)
admin_site.register(ApplicationReview, ApplicationReviewAdmin)
