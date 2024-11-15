$(document).ready(function() {
//  $(".checkButton").click(function() {
//    let projectId = $(this).data("project-id");
//    $.ajax({
//      url: `${window.location.protocol}//${window.location.host}/health/${projectId}`,
//      type: "GET",
//      success: function(response) {
//      },
//      error: function(xhr, status, error) {
//      }
//    });
//  });
  let heartbeatIntervalId = null;

  function getColumnIndexByName($table, columnName) {
    let columnIndex = $table.find('th').filter(function() {
      return $(this).text().trim() === columnName;
    }).index();
    return columnIndex;
  }

  if ($('#line-table tbody tr').length !== 1) {
    heartbeatIntervalId = setInterval(updateHeartbeat, 1000);
  }

  function updateHeartbeat() {
    let $table = $('#line-table');
    $.ajax({
      url: "/get_real_projects_heartbeat",
      method: "POST",
      success: function(response) {
        $table.find('tbody tr').each(function() {
          let $row = $(this);
          let project_name = $row.find('td:first').text().trim();
          let project_data = response.find(project => project.project_name === project_name);

          if (project_data) {
            let statusIndex = getColumnIndexByName($table, 'Status');

            let statusElement;
            if (project_data.status === 'ONLINE') {
              statusElement = '<img class="proj-status" src="/static/green_power.svg"/>';
            } else {
              statusElement = '<img class="proj-status" src="/static/red_power.svg"/>';
            }
            $row.children('td').eq(statusIndex).html(statusElement);

          let lastReadingsIndex = getColumnIndexByName($table, 'Last Readings');
          if (project_data.last_readings) {
            let readings = project_data.last_readings;
            let cpuUsage = readings.cpu;
            let usedMemory = readings.used_memory;
            let processMemory = readings.process_memory;

            let totalMemory = readings.total_memory;


            let cpuText = $row.find(`#reading-cpu-${project_data.project_id}`);
            let cpuInfo = `CPU: ${cpuUsage}%/100%`;
            let cpuBar = $row.find(`#cpu-usage-bar-${project_data.project_id}`);
            cpuText.html(cpuInfo);
            cpuBar.css('width', `${cpuUsage}%`).attr('aria-valuenow', cpuUsage);

            let memoryText = $row.find(`#reading-mem-${project_data.project_id}`);
            let memoryUsage = (parseFloat(usedMemory) / parseFloat(totalMemory) * 100).toFixed(2);
            let memoryInfo = `MEM: ${usedMemory} GB/${totalMemory} GB`;
            let memoryBar = $row.find(`#memory-usage-bar-${project_data.project_id}`);
            memoryText.html(memoryInfo);
            memoryBar.css('width', `${memoryUsage}%`).attr('aria-valuenow', memoryUsage);

            let processMemoryText = $row.find(`#reading-process-mem-${project_data.project_id}`);
            if (processMemoryText) {
              let processMemoryUsage = (parseFloat(processMemory) / parseFloat(totalMemory) * 100).toFixed(2);
              let processMemoryInfo = `PROC MEM: ${processMemory} GB/${totalMemory} GB`;
              let processMemoryBar = $row.find(`#process-memory-usage-bar-${project_data.project_id}`);
              processMemoryText.html(processMemoryInfo);
              processMemoryBar.css('width', `${processMemoryUsage}%`).attr('aria-valuenow', processMemoryUsage);
            }


          } else {
            $row.children('td').eq(lastReadingsIndex).html('-');
          }

          let lastHeartbeat = getColumnIndexByName($table, 'Last Heartbeat');
          $row.children('td').eq(lastHeartbeat).html(project_data.last_heartbeat);

          }
        });
      },
      error: function() {
        if (heartbeatIntervalId) {
          clearInterval(heartbeatIntervalId);
          heartbeatIntervalId = null;
        }

        alert('Error updating table. Please reload the page.');

      }
    });
  }

  function updateProgressBar(barId, value) {
    const bar = document.getElementById(barId);
    bar.style.width = value + '%';
    bar.setAttribute('aria-valuenow', value);

    if (value < 50) {
      bar.classList.remove('bg-warning', 'bg-danger');
      bar.classList.add('bg-custom');
    } else if (value >= 50 && value < 70) {
      bar.classList.remove('bg-warning', 'bg-danger', 'bg-custom');
      bar.classList.add('bg-success');
    } else if (value >= 70 && value < 90) {
      bar.classList.remove('bg-success', 'bg-danger', 'bg-custom');
      bar.classList.add('bg-warning');
    } else {
      bar.classList.remove('bg-success', 'bg-warning', 'bg-custom');
      bar.classList.add('bg-danger');
    }
  }


  $('.hide-project-btn').click(function() {
    let projectId = $(this).data('id');
    let projectName = $(this).data('name');
    $.ajax({
      url: "/hide_or_return_project/",
      method: "POST",
      data: JSON.stringify({'hidden': true, 'project_id': projectId, 'project_name': projectName}),
      contentType: "application/json; charset=utf-8",
      dataType: "json",
      success: function(response) {
        $('button.hide-project-btn[data-id="' + projectId + '"]').closest('tr').remove();

        let $table = $('#line-table');
        let $tableBody = $('#line-table tbody');
        let rowCount = $tableBody.find('tr').length - 1;
        let totalRow = $tableBody.find('tr.total');
        totalRow.find('td:first').text(`Total (${rowCount})`);


        if ($tableBody.children('tr').length === 1) {
          $tableBody.find('tr').remove();
          let welcomeHtml = $('.welcome').html();
          $tableBody.append(`<tr><td colspan="10">${welcomeHtml}</td></tr>`);
        } else {
          let total_exceptions = 0;
          let errorIndex = getColumnIndexByName($table, 'Error counter');
          $tableBody.find('tr').not('.total').each(function() {
            let count = parseInt($(this).find('td').eq(errorIndex).text());
            total_exceptions += count;
        });

        totalRow.find('td').eq(errorIndex).text(total_exceptions);
        }
      },
      error: function(xhr, status, error) {
          alert('Error: Could not hide project.');
      }
    });
  });
});