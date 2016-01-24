import hashlib
import os

from django.db import models


class UploadFileBase(models.Model):
    file = models.FileField(blank=True)
    file_name = models.CharField(max_length=255)
    total_size = models.BigIntegerField(default=0)
    recorded_md5 = models.CharField(max_length=32, blank=True)


    @property
    def current_size(self):
        return self.file.size

    @property
    def md5(self):
        md5 = hashlib.md5()
        for chunk in self.file.chunks():
            md5.update(chunk)
        return md5.hexdigest()

    @property
    def is_finished(self):
        return self.md5 == self.recorded_md5

    class Meta:
        abstract = True

    def __str__(self):
        return 'name: {file_name}; size: {total_size}; md5: {recorded_md5}'.format(
            file_name=self.file_name,
            total_size=self.total_size,
            recorded_md5=self.recorded_md5,
        )

    def close_file(self):
        """
        Bug in django 1.4: FieldFile `close` method is not reaching all the
        way to the actual python file.
        Fix: we had to loop all inner files and close them manually.
        """
        file_ = self.file
        while file_ is not None:
            file_.close()
            file_ = getattr(file_, 'file', None)

    def append_chunk(self, chunk, mode='ab'):
        self.close_file()
        self.file.open(mode=mode)
        self.file.write(chunk.read())
        self.close_file()


class DataSet(models.Model):
    name = models.CharField(max_length=255, unique=True)


def generate_file_path(instance, filename):
    return os.path.join(instance.dataset.name, filename)


class UploadFile(UploadFileBase):
    dataset = models.ForeignKey(DataSet)

UploadFile._meta.get_field('file').upload_to = generate_file_path
