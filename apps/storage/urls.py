from django.urls import path
from .views import FileUploadView, FileListView, FileDownloadView, FileDeleteView

urlpatterns = [
    path('upload', FileUploadView.as_view(), name='storage-upload'),
    path('files', FileListView.as_view(), name='storage-list'),
    path('files/<uuid:file_id>', FileDownloadView.as_view(), name='storage-download'),
    path('files/<uuid:file_id>/delete', FileDeleteView.as_view(), name='storage-delete'),
]

