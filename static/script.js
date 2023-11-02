$(document).ready(function() {
    var searchForm = $('#search-form');
    searchForm.on('submit', function(e) {
        e.preventDefault();
        var personId = $('#personId').val();
        searchEvents(personId);
    });
});

function searchEvents(personId) {
    fetch('/search?personId=' + encodeURIComponent(personId))
        .then(response => response.json())
        .then(events => {
            // Construct the table if not already present
            if ($.fn.DataTable.isDataTable('#eventsTable')) {
                $('#eventsTable').DataTable().destroy();
            }
            $('#events').empty();

            let tableHtml = `
                <table id="eventsTable" class="display">
                    <thead>
                        <tr>
                            <th>Event ID</th>
                            <th>Type</th>
                            <th>Time</th>
                            <th>Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${events.map(event => `
                            <tr>
                                <td>${event.eventid}</td>
                                <td>${event.type}</td>
                                <td>${event.time}</td>
                                <td>${event.link}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;

            $('#events').html(tableHtml);
            // Initialize DataTables
            $('#eventsTable').DataTable({
                "order": [[2, "asc"]] // Assuming the third column is 'Time' and we want to sort by it
            });
        })
        .catch(error => {
            console.error('Error:', error);
            $('#events').html('Error fetching events.');
        });
}
