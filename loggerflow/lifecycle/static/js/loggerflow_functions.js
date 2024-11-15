$(document).ready(function() {
  $('.return-project-btn').click(function() {
    let projectId = $(this).data('id');
    let projectName = $(this).data('name');
    $.ajax({
      url: "/hide_or_return_project/",
      method: "POST",
      data: JSON.stringify({'hidden': false, 'project_id': projectId, 'project_name': projectName}),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(response) {
        $('button.return-project-btn[data-id="' + projectId + '"]').closest('tr').remove();
        var $tableBody = $('table tbody');
        if ($tableBody.children('tr').length === 0) {
          let welcomeHiddenHtml = $('.welcome-hidden').html();
          $tableBody.append(`<tr><td colspan="8">${welcomeHiddenHtml}</td></tr>`);
        }
      },
      error: function(xhr, status, error) {
          alert('Error: Could not hide project.');
      }
    });
  });

  $('.delete-project-btn').click(function() {
    let projectId = $(this).data('id');
    $.ajax({
      url: "/delete_project/",
      method: "DELETE",
      data: JSON.stringify({'project_id': projectId}),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(response) {
        $('button.return-project-btn[data-id="' + projectId + '"]').closest('tr').remove();
        var $tableBody = $('table tbody');
        if ($tableBody.children('tr').length === 0) {
          let welcomeHiddenHtml = $('.welcome-hidden').html();
          $tableBody.append(`<tr><td colspan="8">${welcomeHiddenHtml}</td></tr>`);
        }
      },
      error: function(xhr, status, error) {
          console.log('er')
          alert('Error: Could not hide project.');
      }
    });
  });

});