from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder


class UploadError(Exception):
    def __init__(self, status=500, **kwargs):
        self.status = status
        self.data = kwargs


class UploadResponse(HttpResponse):
    def __init__(self, content, status=200, *args, **kwargs):
        super(UploadResponse, self).__init__(
            content=DjangoJSONEncoder().encode(content),
            content_type='application/json',
            status=status,
            *args, **kwargs
        )
