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
      var status_style = (data.status == 'failed') ? '<i class="fa fa-times-circle-o" style="color:#A00;font-size:16px"></i> Failed' : '<i class="fa fa-check-circle-o" style="color:#0A0"></i> Passed';
      //var status_html = '<div class="mb-3"><b>File check:</b> '+status_style+'</div>';
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
