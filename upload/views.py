# -*- encoding: utf-8 -*-
import re

from django.core.files.base import ContentFile
from django.views.generic import View, TemplateView

from . import UploadError, UploadResponse
from .models import DataSet, UploadFile


class IndexView(TemplateView):
    template_name = 'demo.html'


class UploadBaseView(View):
    model = UploadFile
    field_name = 'files'
    content_range_header = 'HTTP_CONTENT_RANGE'
    content_range_pattern = re.compile(
        r'^bytes (?P<start>\d+)-(?P<end>\d+)/(?P<total>\d+)$'
    )

    def get_content_range(self, request, chunk):
        content_range = request.META.get(self.content_range_header)
        if content_range is not None:
            match = self.content_range_pattern.match(content_range)
            if match:
                start = int(match.group('start'))
                end = int(match.group('end'))
                total = int(match.group('total'))
            else:
                raise UploadError(message='The Content Range header seems wrong.', status=400)
            if end - start + 1 != chunk.size:
                raise UploadFile(message='The chunk size don\'t match the header.', status=400)
        else:
            start = 0
            end = chunk.size - 1
            total = chunk.size
        return start, end, total

    @staticmethod
    def get_or_create_dataset(name):
        try:
            dataset = DataSet.objects.get(name=name)
        except DataSet.DoesNotExist:
            dataset = DataSet(name=name)
            dataset.save()
        return dataset

    def get_or_create_chunked_upload(self, chunk, total_size, dataset):
        try:
            chunked_upload = self.model.objects.get(file_name=chunk.name, total_size=total_size, dataset=dataset)
        except self.model.DoesNotExist:
            chunked_upload = self.model(file_name=chunk.name, total_size=total_size, dataset=dataset)
        except self.model.MultipleObjectsReturned:
            chunked_uploads = self.model.objects.filter(file_name=chunk.name, total_size=total_size, dataset=dataset)
            map(lambda x: x.delete(), chunked_uploads[1:])
            chunked_upload = chunked_uploads[0]
        return chunked_upload

    def _post(self, request):
        raise NotImplementedError("You have to define this method in children View class")

    def post(self, request):
        try:
            return self._post(request)
        except UploadError as error:
            return UploadResponse(error.data, status=error.status)
        except Exception as error:
            return UploadResponse({'message': error.__str__()}, status=500)


class UploadView(UploadBaseView):

    def _post(self, request):
        chunk = request.FILES.get(self.field_name)
        start, end, total = self.get_content_range(request, chunk)
        dataset = self.get_or_create_dataset(request.POST.get('dataset_name'))
        chunked_upload = self.get_or_create_chunked_upload(chunk, total, dataset)
        if chunked_upload.is_finished:
            pass
        else:
            if start == 0:
                chunked_upload.append_chunk(chunk, mode='wb')
            else:
                if chunked_upload.current_size == start:
                    chunked_upload.append_chunk(chunk)
                else:
                    raise UploadError(
                        message='Upload content\'s start don\'t '
                                'equal to the file current size',
                        status=400
                    )
            chunked_upload.save()
        return UploadResponse({'status': 'success'}, status=202)


class UploadCompleteView(UploadBaseView):
    def _post(self, request):
        filename = request.POST.get('file_name')
        size = request.POST.get('total_size')
        dataset_name = request.POST.get('dataset_name')
        dataset = DataSet.objects.get(name=dataset_name)
        chunked_upload = self.model.objects.get(file_name=filename, total_size=size, dataset=dataset)
        if chunked_upload.is_finished:
            if all(map(lambda cu: cu.is_finished, dataset.chunkedupload_set.all())):
                return UploadResponse({'status': 'success'}, status=204)
            return UploadResponse({'status': 'success'}, status=200)
        else:
            raise UploadError(status=409, message='File {} MD5 not match, please upload it again.'.format(filename))


class Md5View(UploadBaseView):
    def get_or_create_chunked_upload(self, chunk, total_size, dataset):
        try:
            chunked_upload = self.model.objects.get(file_name=chunk.name, total_size=total_size, dataset=dataset)
        except self.model.DoesNotExist:
            chunked_upload = self.model(file=chunk, file_name=chunk.name, total_size=total_size, dataset=dataset)
        except self.model.MultipleObjectsReturned:
            chunked_uploads = self.model.objects.filter(file_name=chunk.name, total_size=total_size, dataset=dataset)
            map(lambda x: x.delete(), chunked_uploads[1:])
            chunked_upload = chunked_uploads[0]
        return chunked_upload

    def _post(self, request):
        file_name = request.POST.get('file_name')
        total_size = request.POST.get('total_size')
        md5 = request.POST.get('md5')
        dataset_name = request.POST.get('dataset_name')
        print(file_name, total_size, md5, dataset_name)
        if all((file_name, total_size, md5, dataset_name)):
            dataset = self.get_or_create_dataset(name=dataset_name)
            chunk = ContentFile(name=file_name, content='')
            chunked_upload = self.get_or_create_chunked_upload(chunk, int(total_size), dataset)
            chunked_upload.recorded_md5 = md5
            chunked_upload.save()
            return UploadResponse({'status': 'OK'}, status=201)
        else:
            raise UploadError(status=400, message='Required file name, total size and md5 arguments.')
