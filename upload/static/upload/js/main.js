function calculate_md5(file, chunkSize){
    var blobSlice = File.prototype.slice || File.prototype.mozSlice || File.prototype.webkitSlice,
        chunks = Math.ceil(file.size / chunkSize),
        currentChunk = 0,
        spark = new SparkMD5.ArrayBuffer(),
        fileReader = new FileReader();
    fileReader.onload = function (e) {
        spark.append(e.target.result);                   // Append array buffer
        currentChunk++;
        if (currentChunk < chunks) {
            loadNext();
        } else {
            console.log('finished loading');
            $.ajax({
                type: 'POST',
                url: '/upload/md5/',
                data: {
                    file_name: file.name,
                    total_size: file.size,
                    md5: spark.end(),
                    dataset_name: $("#dataset_name").val()
                },
                success: function(data) {
                        console.log('success');
                    },
                error:function(){
                        console.log('error');
                }
            })
        }
    };

    fileReader.onerror = function () {
        console.warn('oops, something went wrong.');
    };

    function loadNext() {
        var start = currentChunk * chunkSize,
            end = ((start + chunkSize) >= file.size) ? file.size : start + chunkSize;
        fileReader.readAsArrayBuffer(blobSlice.call(file, start, end));
    }

    loadNext();
}
var form_data = [];
$("#fileupload")
        .bind('fileuploadchange', function (e, data) {
            console.log('Call the change');
            $("#fileupload").empty();
        })
        .bind('fileuploadadd', function (e, data) {
            if (form_data.length == 0){
                form_data.push(
                    {"name": "dataset_name", "value": $("#dataset_name").val()}
                )
            }
            $.each(data.files, function (index, file) {
                console.log('calculate md5 of '+file.name);
                calculate_md5(file, 1000000); // 1 MB
            });
            $("#submit").click(function () {data.submit()});
        })
        .bind('fileuploadsubmit', function (e, data) {
            console.log('submit: '+data.files[0].name)
        })
        .bind('fileuploadsend', function (e, data) {
            console.log('send  : '+data.files[0].name)
        })
        .bind('fileuploaddone', function (e, data) {
            var thisFile = data.files[0];
                console.log(thisFile.name+' done');
                $.ajax({
                    type: "POST",
                    url: "/upload/complete/",
                    data: {
                        file_name: thisFile.name,
                        total_size: thisFile.size,
                        dataset_name: $("#dataset_name").val()
                    },
                    statusCode: {
                        204: function () {
                            console.log('Successfully upload.')
                        }
                    },
                    success: function() {
                        console.log('success check the uploaded file\'s md5');
                    },
                    error:function(){
                        console.log('error');
                    }
        })})
        .fileupload({
            url: "/upload/chunk/",
            maxChunkSize: 1000000, // 1 MB
            formData: form_data,
            autoUpload: false
        })
        .on('fileuploadchunksend', function (e, data) {
            console.log('c_send: '+data.files[0].name)
        })
        .on('fileuploadchunkdone', function (e, data) {
            console.log('c_done: '+data.files[0].name+'; '+data.result['content_range'])
        });