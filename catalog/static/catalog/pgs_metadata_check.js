var check_url = 'http://127.0.0.1:5000/validate';
//var storage_url = 'https://validator-dot-pgs-catalog.appspot.com/validate';

$(document).ready(function() {
  var filename = $('#uploaded_filename').attr('data-value');
  console.log('filename: '+filename);
  if (filename) {
    console.log('check_url: '+check_url);
    $.ajax({
        url: check_url,
        method: "POST",
        contentType: "application/json",
        dataType: 'json',
        data: JSON.stringify({"filename": filename})
    })
    .done(function (data) {
      console.log("SUCCESS");
      var status_style = (data.status == 'failed') ? '<i class="fa fa-times-circle-o" style="color:#A00"></i> Failed' : '<i class="fa fa-check-circle-o" style="color:#0A0"></i> Passed';
      var status_html = '<div class="mb-3"><b>File check:</b> '+status_style+'</div>';
      $('#check_status').html(status_html);
      if (data.error) {
        var report = '';
        $.each(data.error, function(spreadsheet, errors_list){
            report += "<div><b>Report:</b></div>";
            report += "<h5>"+spreadsheet+"</h5><ul>";
            $.each(errors_list, function(index, error_item){
              var lines = (error_item.lines) ? "Line(s): "+error_item.lines.join(',')+ ' | ' : '';
              report += "<li>"+lines+error_item.message+"</li>";
            });
            report += '</ul>';
        });
        $('#check_report').html(report);
      }

    })
    .fail(function (xhRequest, ErrorText, thrownError) {
      var status_html = '<div><b>File check:</b> <i class="fa fa-times-circle-o" style="color:#A00"></i> Failed</div>';
      $('#check_status').html(status_html);
      $('#check_report').html(thrownError);
    });
  }
  else {
    var status_html = '<div class="clearfix">'+
                      '  <div class="mt-3 float_left pgs_note pgs_note_2">'+
                      '    <div><span>Error:</span> The upload of the file "'+filename+'" failed.</div>'+
                      '  </div>'+
                      '</div>';
    $('#check_status').html(status_html);
  }
});
