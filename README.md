# django-multiple-file-chunked-upload
Upload plugin for Django which support multiple file chunked upload simultaneously.

Modified from [django-chunked-upload](https://github.com/juliomalegria/django-chunked-upload) which only support single file chunked upload. Because of the async chunked upload, remove django-chunked-upload's upload_id attribute.

This app works with [jQuery File Upload Plugin](https://github.com/blueimp/jQuery-File-Upload) and [SparkMD5](https://github.com/satazor/js-spark-md5)

# Requirement
My environment:

Python==3.5.1

Django==1.9.1
 
jQuery==2.2.0

P.S. for unknown reason, only the Django 1.9+ will support modifying file field's upload_to by assign to `YourOwnModel._meta.get_field('file').upload_to`

# License
MIT