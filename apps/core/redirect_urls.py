from django.urls import path

from .redirects import redirect_cta

urlpatterns = [
    path('<slug:route>', redirect_cta, name='redirect-cta'),
]
