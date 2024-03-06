$(document).ready(function() {
  $('.return-project-btn').click(function() {
    let projectId = $(this).data('id');
    $.ajax({
      url: "/hide_or_return_project/",
      method: "POST",
      data: JSON.stringify({'hidden': false, 'project_id': projectId}),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(response) {
        $('button.return-project-btn[data-id="' + projectId + '"]').closest('tr').remove();
        var $tableBody = $('table tbody');
        console.log($tableBody.children('tr').length)
        if ($tableBody.children('tr').length === 0) {
          $tableBody.append('<tr><td colspan="8">No hidden projects, woohoo...</tr>');
        }
      },
      error: function(xhr, status, error) {
          console.log('er')
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
        console.log($tableBody.children('tr').length)
        if ($tableBody.children('tr').length === 0) {
          $tableBody.append('<tr><td colspan="8">No hidden projects, woohoo...</tr>');
        }
      },
      error: function(xhr, status, error) {
          console.log('er')
          alert('Error: Could not hide project.');
      }
    });
  });

});