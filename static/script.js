$(document).ready(function() {
    var searchForm = $('#search-form');
    
    $('input[name="searchType"]').change(function() {
        // Enable the appropriate input based on the selected search type
        var searchType = $(this).val();
        if(searchType === 'personId') {
            $('#personId').prop('disabled', false);
            $('#linkId').prop('disabled', true);
            $('#linkIdLinkTable').prop('disabled', true);

        } else if (searchType === 'linkId') {
            $('#personId').prop('disabled', true);
            $('#linkId').prop('disabled', false);
            $('#linkIdLinkTable').prop('disabled', true);
        }
        else{
            $('#personId').prop('disabled', true);
            $('#linkId').prop('disabled', true);
            $('#linkIdLinkTable').prop('disabled', false);
        }
    });

    searchForm.on('submit', function(e) {
        e.preventDefault();
        var searchType = $('input[name="searchType"]:checked').val();
        var searchId = $('#' + searchType).val();
        searchEvents(searchType, searchId);
    });
});

function searchEvents(searchType, searchId) {
    var queryParam = searchType + '=' + encodeURIComponent(searchId);
    fetch('/search?' + queryParam)
        .then(response => response.json())
        .then(events => {
               // Construct the table if not already present
            if ($.fn.DataTable.isDataTable('#eventsTable')) {
                $('#eventsTable').DataTable().destroy();
            }
            $('#events').empty();
            var tableHtml;
            if(searchType == 'personId' || searchType == 'linkId'){
                tableHtml = `
                <table id="eventsTable" class="display centered-table">
                    <thead>
                        <tr>
                            <th>Event ID</th>
                            <th>Type</th>
                            <th>Time</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => `
                            <tr>
                                <td>${event.eventid}</td>
                                <td>${event.type}</td>
                                <td>${event.time}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            }             
            else{
                tableHtml = `
                <table id="eventsTable" class="display centered-table">
                    <thead>
                        <tr>
                            <th>FreeSpeed</th>
                            <th>Capacity</th>
                            <th>Mode</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => `
                            <tr>
                                <td>${event.freespeed}</td>
                                <td>${event.capacity}</td>
                                <td>${event.mode}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            }

            $('#events').html(tableHtml);
            // Initialize DataTables
            $('#eventsTable').DataTable({
                // DataTables initialization options
                destroy: true, // This option allows re-initialization on the same table
                autoWidth: false // This can help with rendering issues in some cases
                
            });
          
        })
        .catch(error => {
            console.error('Error:', error);
            $('#events').html('Error fetching events.');
        });
}









