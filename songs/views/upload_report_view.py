from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class UploadReportView(LoginRequiredMixin, TemplateView):
    template_name="upload_report.html"