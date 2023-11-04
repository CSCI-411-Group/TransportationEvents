$(document).ready(function() {
    var searchForm = $('#search-form');
    
    function updateRequiredAttributes() {
        // Enable the appropriate input based on the selected search type
        var searchType = $(this).val();
        if ($('#searchByPerson').is(':checked')) {
            $('#personId').prop('disabled', false).val('');
            $('#linkId').prop('disabled', true).val('');
            $('#linkIdLinkTable').prop('disabled', true).val('');
            $('#timeRange').hide().val('');


        } else if ($('#searchByLink').is(':checked')) {

            $('#personId').prop('disabled', true).val('');
            $('#linkId').prop('disabled', false).val('');
            $('#linkIdLinkTable').prop('disabled', true).val('');
            $('#timeRange').show().val('');
        }
        else{
            $('#personId').prop('disabled', true).val('');
            $('#linkId').prop('disabled', true).val('');
            $('#linkIdLinkTable').prop('disabled', false).val('');
            $('#timeRange').hide().val('');
        }
    }


    $('input[name="searchType"]').change(updateRequiredAttributes);


    searchForm.on('submit', function(e) {
        e.preventDefault();
        var searchType = $('input[name="searchType"]:checked').val();
        var searchId = $('#' + searchType).val();
        var startTime = searchType === 'linkId' ? $('#startTime').val() : null;
        var endTime = searchType === 'linkId' ? $('#endTime').val() : null;
        searchEvents(searchType, searchId, startTime, endTime);
    });
});

function searchEvents(searchType, searchId, startTime, endTime) {
    var queryParam = searchType + '=' + encodeURIComponent(searchId);
    
    // Ensure startTime and endTime are only appended for linkId searchType
    if (searchType === 'linkId' && startTime && endTime) {
        queryParam += '&startTime=' + encodeURIComponent(startTime);
        queryParam += '&endTime=' + encodeURIComponent(endTime);
    }
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
                autoWidth: false, // This can help with rendering issues in some cases
                language: {
                emptyTable: "No Data Found!" // Custom message for an empty table
                }
                
            });
          
        })
        .catch(error => {
            console.error('Error:', error);
            $('#events').html('Error fetching events.');
        });
}









