from django.conf.urls import url

from .views import UploadView, UploadCompleteView, Md5View

urlpatterns = [
    url(r'^chunk/$', UploadView.as_view()),
    url(r'^complete/$', UploadCompleteView.as_view()),
    url(r'^md5/$', Md5View.as_view())
]
