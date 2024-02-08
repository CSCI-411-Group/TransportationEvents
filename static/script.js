var existingFiles = [];

$(document).ready(function() {
    var searchForm = $('#search-form');

    function updateRequiredAttributes() {
        document.getElementById('events').innerHTML = '';
        document.getElementById('mapid').innerHTML = '';

        // Enable the appropriate input based on the selected search type
        var searchType = $('input[name="searchType"]:checked').val();
        
        // Disable all inputs first
        $('#personId, #linkId').prop('disabled', true).val('');

        switch(searchType) {
            case 'personId':
                $('#personId').prop('disabled', false);
                $('#timeRange').show();
                $('#search').show();
                $('#events').show();
                $('#mapid').show();

                break;
            case 'linkId':
                $('#mapid').hide();
                $('#events').show();
                $('#linkId').prop('disabled', false);
                $('#timeRange').show();
                $('#search').show();
                break;
           
        }
    }

    // Initialize the form state
    updateRequiredAttributes();
    $('input[name="searchType"]').change(updateRequiredAttributes);

    searchForm.on('submit', function(e) {
        e.preventDefault();
        var searchType = $('input[name="searchType"]:checked').val();
        var searchId = $('#' + searchType).val();
        var startTime = $('#startTime').val();
        var endTime = $('#endTime').val();
        
        
        searchEvents(searchType, searchId, startTime, endTime);
        
    });
});
function searchEvents(searchType, searchId, startTime, endTime) {
    var queryParam = searchType + '=' + encodeURIComponent(searchId);
    
    // Ensure startTime and endTime are only appended for linkId searchType
    if (startTime && endTime) {
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
    
    if(searchType == 'personId'){

    fetch('/visualize?' + queryParam.toString())
    .then(response => response.text())  // Get the response text (HTML)
    .then(data => {
        const mapContainer = document.getElementById('mapid');
        mapContainer.innerHTML = data;  // Insert the map HTML into the container
        const mapElements = mapContainer.getElementsByClassName('leaflet-container'); // Assuming Leaflet is used by Folium
        if (mapElements.length > 0) {
            const mapElement = mapElements[0]; // Assuming only one map element
            mapElement.style.width = '100%'; // Example style, adjust as needed
            mapElement.style.height = '100%'; // Example style, adjust as needed
            // Add more styles as needed
        }
    })
    .catch(error => {
        console.error('Error fetching the map:', error);
    }); 
}
}

function handleFiles(files) {
    // Display file names
    let fileList = document.getElementById('file-list');

    existingFiles = existingFiles.concat(Array.from(files));

    let numberOfFiles = fileList.querySelectorAll('p').length;
    if(numberOfFiles==2){
        fileList.innerHTML = "";
    }

    for (const file of files) {
        fileList.innerHTML += `<p>${file.name}</p>`;
    }
}

function handleDrop(event) {
    event.preventDefault();
    let files = event.dataTransfer.files;
    document.getElementById('file-input').files = files;
    handleFiles(files);
}

function handleDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
}

function browseFiles() {
    document.getElementById('file-input').click();
}

function processFiles(){
    const formData = new FormData();
    let fileList = document.getElementById('file-list');

    var progressBarContainers = document.getElementById('progress-bar-container');

    for (const file of existingFiles) {
        formData.append('files', file);
    }
    
    if(existingFiles.length < 2 || existingFiles.length>2){
        alert("Error: Upload 2 Files");
        existingFiles.length=0
        fileList.innerHTML = "";

        return;
    }
    progressBarContainers.style.display = 'block';

    fetch('/importData', {
        method: 'POST',
        body: formData,
    })
    .catch(error => console.error('Error:', error));


}
