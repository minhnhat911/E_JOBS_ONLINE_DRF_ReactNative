from rest_framework import viewsets, generics, status, parsers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import JobCategory, JobPost, User, JobApplication, CandidateProfile, Tag, Payment, EmployerProfile
from . import serializers, paginators, perms
from .serializers import UserSerializer
from django.db.models import Count
from django.db.models.functions import TruncMonth
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated


class JobCategoryView(viewsets.ViewSet, generics.ListAPIView):
    queryset = JobCategory.objects.all()
    serializer_class = serializers.CategorySerializer

class TagView(viewsets.ViewSet, generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer

class JobPostView(viewsets.ViewSet, generics.ListAPIView):
    queryset = JobPost.objects.filter(status='OPEN')
    serializer_class = serializers.JobPostSerializer
    pagination_class = paginators.ItemPaginator

    def get_queryset(self):
        query = self.queryset.select_related(
            'category', 'employer'
        ).prefetch_related('tags')

        params = self.request.query_params

        q = params.get('q')
        if q:
            query = query.filter(title__icontains=q)

        company = params.get('company')
        if company:
            query = query.filter(employer__company_name__icontains=company)

        category_id = params.get('category_id')
        if category_id:
            query = query.filter(category_id=category_id)

        location = params.get('location')
        if location:
            query = query.filter(location__icontains=location)

        salary_min = params.get('salary_min')
        if salary_min:
            query = query.filter(salary_min__gte=salary_min)

        salary_max = params.get('salary_max')
        if salary_max:
            query = query.filter(salary_max__lte=salary_max)

        featured = params.get('featured')
        if featured:
            query = query.filter(is_featured=True)

        order_by = params.get('order_by')
        if order_by == 'salary_asc':
            query = query.order_by('salary_min')
        elif order_by == 'salary_desc':
            query = query.order_by('-salary_max')
        elif order_by == 'newest':
            query = query.order_by('-created_date')

        return query

    @action(methods=['get'], detail=True, url_path='detail')
    def get_detail(self, request, pk):
        job = self.get_object()
        return Response(
            serializers.JobPostDetailSerializer(job).data,
            status=status.HTTP_200_OK
        )

class EmployerProfileView(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = EmployerProfile.objects.filter(is_approved=True)
    serializer_class = serializers.EmployerSerializer

class CandidateProfileView(viewsets.ViewSet, generics.RetrieveAPIView):
    queryset = CandidateProfile.objects.all()
    serializer_class = serializers.CandidateSerializer



class JobApplicationView(viewsets.ViewSet, generics.ListCreateAPIView):
    serializer_class = serializers.JobApplicationSerializer
    parser_classes = [parsers.MultiPartParser]
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), perms.IsCandidate()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user

        if user.role == 'CANDIDATE':
            return JobApplication.objects.filter(
                candidate__user=user
            )

        if user.role == 'EMPLOYER':
            return JobApplication.objects.filter(
                job__employer=user.employerprofile
            )

        return JobApplication.objects.none()

    def create(self, request):
        serializer = serializers.JobApplicationSerializer(data={
            'job': request.data.get('job'),
            'candidate': request.user.candidateprofile.id,
            'cv_file': request.data.get('cv_file')
        })
        serializer.is_valid(raise_exception=True)
        application = serializer.save()

        return Response(
            serializers.JobApplicationSerializer(application).data,
            status=status.HTTP_201_CREATED
        )


class PaymentView(viewsets.ViewSet, generics.ListCreateAPIView):
    serializer_class = serializers.PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

class ApplicationReviewView(viewsets.ViewSet, generics.CreateAPIView):
    serializer_class = serializers.ApplicationReviewSerializer
    permission_classes = [permissions.IsAuthenticated, perms.IsEmployer]


    def create(self, request):
        s = serializers.ApplicationReviewSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        review = s.save(employer=request.user.employerprofile)

        return Response(
            serializers.ApplicationReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )

class UserView(viewsets.ViewSet, generics.CreateAPIView):

    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    parser_classes = [parsers.MultiPartParser]

    def get_permissions(self):
        if self.action == 'current_user':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    @action(
        methods=['get', 'patch'],
        detail=False,
        url_path='current-user'
    )
    def current_user(self, request):
        user = request.user

        if request.method == 'PATCH':
            serializer = UserSerializer(
                user,
                data=request.data,
                partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(
            UserSerializer(user).data,
            status=status.HTTP_200_OK
        )

    @action(
        methods=['get'],
        detail=False,
        permission_classes=[perms.IsEmployer]
    )
    def employer_only(self, request):
        return Response({'msg': 'EMPLOYER OK'})

class EmployerStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employer = request.user.employerprofile

        applications = JobApplication.objects.filter(
            job__employer=employer
        )

        total_applications = applications.count()

        applications_by_month = (
            applications
            .annotate(month=TruncMonth('created_date'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        )

        job_effectiveness = (
            JobPost.objects
            .filter(employer=employer)
            .annotate(application_count=Count('jobapplication'))
            .values('title', 'application_count')
        )

        return Response({
            'total_applications': total_applications,
            'applications_by_month': applications_by_month,
            'job_effectiveness': job_effectiveness
        })