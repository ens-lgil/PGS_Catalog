//var validation_service_url = 'http://127.0.0.1:5000/validate';
var validation_service_url = 'https://validator-dot-pgs-catalog.appspot.com/validate';

$(document).ready(function() {
  var filename = $('#uploaded_filename').attr('data-value');
  console.log('filename: '+filename);
  if (filename) {
    console.log('validation_service_url: '+validation_service_url);
    $.ajax({
        url: validation_service_url,
        method: "POST",
        contentType: "application/json",
        dataType: 'json',
        data: JSON.stringify({"filename": filename})
    })
    .done(function (data) {
      console.log("SUCCESS");
      var status_style = (data.status == 'failed') ? '<i class="fa fa-times-circle-o" style="color:#A00;font-size:16px"></i> Failed' : '<i class="fa fa-check-circle-o" style="color:#0A0"></i> Passed';
      var status_html = '<table class="table table-bordered table_pgs_h mb-4"><tbody>'+
                        '  <tr><td>File check</td><td>'+status_style+'</td></tr>'+
                        '</tbody></table>';
      $('#check_status').html(status_html);
      // Error messages
      if (data.error) {
        var report = '<h5 class="mt-4" style="color:#A00">Error report</h5>'+
                     '<table class="table table-bordered" style="width:auto"><thead class="thead-light">'+
                     '<tr><th>Spreadsheet</th><th>Error message(s)</th></tr>'+
                     '</thead><tbody>';
        $.each(data.error, function(spreadsheet, errors_list){
          report += "<tr><td><b>"+spreadsheet+"</b></td><td>";
          report += report_items_2_html(errors_list);
          report += '</td></tr>';
        });
        report += '</tbody></table>';
        $('#report_error').html(report);
      }
      else {
        $('#report_error').html('');
      }
      // Warning messages
      if (data.warning) {
        var report = '<h5 class="mt-4" style="color:orange">Warning report</h5>'+
                     '<table class="table table-bordered" style="width:auto"><thead class="thead-light">'+
                     '<tr><th>Spreadsheet</th><th>Warning message(s)</th></tr>'+
                     '</thead><tbody>';
        $.each(data.warning, function(spreadsheet, warnings_list){
          report += "<tr><td><b>"+spreadsheet+"</b></td><td>";
          report += report_items_2_html(warnings_list);
          report += '</td></tr>';
        });
        report += '</tbody></table>';
        $('#report_warning').html(report);
      }
      else {
        $('#report_warning').html('');
      }
    })
    .fail(function (xhRequest, ErrorText, thrownError) {
      var status_html = '<div><b>File check:</b> <i class="fa fa-times-circle-o" style="color:#A00"></i> Failed</div>';
      $('#check_status').html(status_html);
      error_msg = (thrownError && thrownError != '') ? thrownError : 'Internal error';
      var error_html = '<div class="clearfix">'+
                        '  <div class="mt-3 float_left pgs_note pgs_note_2">'+
                        '    <div><b>Error:</b> '+error_msg+'</div>'+
                        '  </div>'+
                        '</div>';
      $('#report_error').html(error_html);
    });
  }
  else {
    var error_html = '<div class="clearfix">'+
                      '  <div class="mt-3 float_left pgs_note pgs_note_2">'+
                      '    <div><b>Error:</b> The upload of the file "'+filename+'" failed.</div>'+
                      '  </div>'+
                      '</div>';
    $('#check_status').html('');
    $('#report_error').html(error_html);
  }


  // Display the reports in an HTML bullet point
  function report_items_2_html(reports_list) {
    var report = '<ul>';
    $.each(reports_list, function(index, report_item){
      var lines = (report_item.lines) ? "Line(s): "+report_item.lines.join(',')+ ' &rarr; ' : '';
      report += "<li>"+lines+report_item.message+"</li>";
    });
    report += '</ul>';
    return report;
  }
});
