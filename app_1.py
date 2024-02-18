from flask import Flask, request, render_template, redirect, url_for, jsonify, flash, session  
import psycopg2
import psycopg2.extras
import folium
from pyproj import Transformer
import xml.etree.ElementTree as ET
from lxml import etree
from psycopg2.extras import execute_batch, NamedTupleCursor
from tqdm import tqdm
import threading
import time
from flask_socketio import SocketIO
import secrets
import uuid
import math

app = Flask(__name__)
app.secret_key = str(uuid.uuid4()) 
socketio = SocketIO(app)
#connection (change this based on your db)

db_config = {
    'dbname': 'TransportationEvents',
    'user': 'postgres',
    'password': '.',
    'host': 'localhost',
    'port': '5432'
}
@socketio.on('connect', namespace='/progress')
def connect():
    print('Client connected to progress updates')
    
class NodeSetting():
    def __init__(self, activity, icon_name, icon_color="blue"):
        self.activity = activity
        self.icon_name = icon_name
        self.icon_color = icon_color

# Define node settings
s1 = NodeSetting("Home", "home", "red")
s2 = NodeSetting("Work", "briefcase", "green")
# s3 = NodeSetting("actstart", "play", "orange") 
# s4 = NodeSetting("actend", "stop", "purple")     
# s5 = NodeSetting("arrival", "arrow-up", "blue") 
# s6 = NodeSetting("departure", "arrow-down", "gray")
s3 = NodeSetting("Services (e.g. Bank, post office)", "building", "green")
s4 = NodeSetting("Eat/ Get take-out", "cutlery", "green")
s5 = NodeSetting("Shopping- Grocery", "shopping-basket", "green")
s6 = NodeSetting("Shopping- Retail", "shopping-cart", "green")
s7 = NodeSetting("pt interaction", "bus", "blue")
s8 = NodeSetting("h", "home", "red")
s9 = NodeSetting("taxi interaction", "fa-taxi", "yellow")
s10 = NodeSetting("Uber_Source_Act", "fa-car", "green")
# Map activity names to settings
activity_to_settings = {
    s1.activity: s1,
    s2.activity: s2,
    s3.activity: s3,
    s4.activity: s4,
    s5.activity: s5,
    s6.activity: s6,
    s7.activity: s7,
    s8.activity: s8,
    s9.activity: s9,
    s10.activity: s10

}


def time_to_seconds(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60

def insertEventsFromXml(xml_file, conn, linkid2id):
    # Parse the XML file

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_file, parser=parser)
    cursor = conn.cursor(cursor_factory=NamedTupleCursor)

    # Connect to the PostgreSQL database
    cursor = conn.cursor()

    total_records = len(root.findall('.//event'))
    half_point = total_records // 2
    processed_records = 0
    try:
        # Iterate through event elements and insert them into the "Events" table
        events = []
        for event_data in tqdm(root.findall('.//event'), desc='Processing', position=0, leave=True):


            processed_records += 1
            progress_percentage = int(processed_records / total_records * 100)

            time = float(event_data.get('time'))
            event_type = event_data.get('type')
            
            # Extract other optional fields (replace None with NULL)
            departure_id = event_data.get('departureId', None)
            transit_line_id = event_data.get('transitLineId', None)
            request = event_data.get('request', None)
            act_type = event_data.get('actType', None)
            purpose = event_data.get('purpose', None)
            vehicle = event_data.get('vehicle', None)
            amount = float(event_data.get('amount', None)) if event_data.get('amount') is not None else None
            transaction_partner = event_data.get('transactionPartner', None)
            transit_route_id = event_data.get('transitRouteId', None)
            relative_position = float(event_data.get('relativePosition', None)) if event_data.get('relative_position') is not None else None
            vehicle_id = event_data.get('vehicleId', None)
            task_index = float(event_data.get('taskIndex', None)) if event_data.get('task_index') is not None else None
            network_mode = event_data.get('networkMode', None)
            mode = event_data.get('mode', None)
            distance = float(event_data.get('distance', None)) if event_data.get('distance') is not None else None
            driver_id = event_data.get('driverId', None)
            x = float(event_data.get('x', None)) if event_data.get('x') is not None else None
            y = float(event_data.get('y', None)) if event_data.get('y') is not None else None
            agent = event_data.get('agent', None)
            destination_stop = event_data.get('destinationStop', None)
            dvrp_mode = event_data.get('dvrpMode', None)
            facility = event_data.get('facility', None)
            task_type = event_data.get('taskType', None)
            leg_mode = event_data.get('legMode', None)
            person = event_data.get('person', None)
            delay = float(event_data.get('delay', None)) if event_data.get('delay') is not None else None
            at_stop = event_data.get('atStop', None)
            link = event_data.get('link', None) # original linkid from the xml file
            dvrp_vehicle = event_data.get('dvrpVehicle', None)
            if link:
                link_id = float(linkid2id.get(link, None))
            else:
                link_id = None

            events.append((time, event_type, departure_id, transit_line_id, request, act_type, purpose, vehicle, amount, transaction_partner, transit_route_id, relative_position, vehicle_id, task_index, 
                          network_mode, mode, distance, driver_id, x, y, agent, destination_stop, dvrp_mode, facility, task_type, leg_mode, person, delay, at_stop, link, link_id, dvrp_vehicle))
            
        
            if progress_percentage % 40 == 0:
                progress_thread = threading.Thread(target=update_progress, args=(progress_percentage, 3))
                progress_thread.start()
                
                execute_batch(cursor, "INSERT INTO Events (Time, Type, DepartureID, TransitLineID, Request, ActType, Purpose, Vehicle, Amount, TransactionPartner, TransitRouteID, RelativePosition, VehicleID, TaskIndex, NetworkMode, Mode, Distance, DriverID, X, Y, Agent, DestinationStop, DvrpMode, Facility, TaskType, LegMode, Person, Delay, AtStop, Link, LinkID,  DvrpVehicle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", events)

                events=[]

        if events:
            execute_batch(cursor, "INSERT INTO Events (Time, Type, DepartureID, TransitLineID, Request, ActType, Purpose, Vehicle, Amount, TransactionPartner, TransitRouteID, RelativePosition, VehicleID, TaskIndex, NetworkMode, Mode, Distance, DriverID, X, Y, Agent, DestinationStop, DvrpMode, Facility, TaskType, LegMode, Person, Delay, AtStop, Link, LinkID, DvrpVehicle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", events)


        # Commit the changes to the database
        conn.commit()
        update_progress(100,3)

    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def insertLinksFromXml(xml_data, conn, nodeid2id):
    # Parse the XML file
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_data, parser=parser)
    cursor = conn.cursor(cursor_factory=NamedTupleCursor)
    total_records = len(root.findall('.//link'))
    half_point = total_records // 2
    processed_records = 0
    try:
        # Iterate through link elements and insert them into the "Links" table
        links = []
        id = 1
        linkid2id = {} # used when insert events to map original linkid to the new id
        for link_data in tqdm(root.findall('.//link'), desc='Processing', position=0, leave=True):
            processed_records += 1
            progress_percentage = int(processed_records / total_records * 100)

            link_id = link_data.get('id')
            from_node_id = link_data.get('from')
            to_node_id = link_data.get('to')
            length = float(link_data.get('length'))
            freespeed = float(link_data.get('freespeed'))
            capacity = float(link_data.get('capacity'))
            permlanes = float(link_data.get('permlanes'))
            oneway = int(link_data.get('oneway'))
            modes = link_data.get('modes')
            linkid2id[link_id] = id
            links.append((id, link_id, nodeid2id[from_node_id], nodeid2id[to_node_id], length, freespeed, capacity, permlanes, oneway, modes))
            id += 1
            
    
            if progress_percentage % 40 == 0:
                progress_thread = threading.Thread(target=update_progress, args=(progress_percentage, 1))
                progress_thread.start()

  
                execute_batch(cursor, "INSERT INTO Links (ID, LinkID, FromNode, ToNode, Length, FreeSpeed, Capacity, PermLanes, OneWay, Mode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", links)
                links=[]
            
        if links:
            execute_batch(cursor, "INSERT INTO Links (ID, LinkID, FromNode, ToNode, Length, FreeSpeed, Capacity, PermLanes, OneWay, Mode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", links)



        # Commit the changes to the database
        conn.commit()
            
        update_progress(100,2)


        return linkid2id
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()

def insertNodesFromXml(xml_data, conn):
    # Parse the XML file
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_data, parser=parser)
    cursor = conn.cursor(cursor_factory=NamedTupleCursor)

    try:
        nodes = []
        id = 1 # this is the primary key in the nodes table
        nodeid2id = {} # used when insert links to map original linkid to the new id
        total_records = len(root.findall('.//node'))
        half_point = total_records // 2
        processed_records = 0

        for record in tqdm(root.findall('.//node'), desc='Processing', position=0, leave=True):
            # Process the record (replace this with your logic)
            processed_records += 1
            progress_percentage = int(processed_records / total_records * 100)
            node_id = record.get('id')
            x = float(record.get('x'))
            y = float(record.get('y'))
            nodeid2id[node_id] = id
            nodes.append((id, node_id, x, y))
            id += 1

            if progress_percentage % 40 == 0:
                progress_thread = threading.Thread(target=update_progress, args=(progress_percentage, 1))
                progress_thread.start()
                execute_batch(cursor, "INSERT INTO Nodes (id, NodeID, X, Y) VALUES (%s, %s, %s, %s)", nodes)
                nodes=[]

        if nodes:
            execute_batch(cursor, "INSERT INTO Nodes (id, NodeID, X, Y) VALUES (%s, %s, %s, %s)", nodes)

        
        # Commit the changes to the database
        conn.commit()
        
        update_progress(100,1)

        return nodeid2id
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()

def insertToDb(events, cursor):
    execute_batch(cursor, "INSERT INTO Events (Time, Type, DepartureID, TransitLineID, Request, ActType, Purpose, Vehicle, Amount, TransactionPartner, TransitRouteID, RelativePosition, VehicleID, TaskIndex, NetworkMode, Mode, Distance, DriverID, X, Y, Agent, DestinationStop, DvrpMode, Facility, TaskType, LegMode, Person, Delay, AtStop, Link, LinkID, DvrpVehicle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", events)

@app.route('/importData', methods=['POST'])
def import_data():
    try:
        conn = psycopg2.connect(**db_config)

        files = request.files.getlist('files')


        for xml_file in files:
            if xml_file.filename == 'network.xml':
                xml_data = xml_file.read()
                nodeid2id = insertNodesFromXml(xml_data, conn)
                progress_thread = threading.Thread(target=update_progress, args=(0,1))
                progress_thread.start()
                linkid2id = insertLinksFromXml(xml_data, conn, nodeid2id)

        progress_thread = threading.Thread(target=update_progress, args=(0,1))
        progress_thread.start()
        for xml_file in files:
            if xml_file.filename != 'network.xml':
                xml_data = xml_file.read()
                insertEventsFromXml(xml_data, conn, linkid2id)


        return jsonify({'success': True}), 200
        conn.close()

    except Exception as e:
        print('Error processing files:', str(e))
        return jsonify({'error': 'Error processing files'}), 500

def update_progress(value, fileFlag):
    with app.app_context():
        socketio.emit('update_progress', {'value': value, 'flag':fileFlag}, namespace='/progress')

@app.route('/import', methods=['GET', 'POST'])
def importRender():
    return render_template('import.html')

@app.route('/')
def render_another_page():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    person_id = request.args.get('personId')
    event_link_id = request.args.get('linkId')
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(**db_config)
        # Open a cursor to perform database operations
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        results_list = []

        if person_id:
            if start_time and end_time:
                start_seconds = time_to_seconds(start_time)
                end_seconds = time_to_seconds(end_time)

                cur.execute("SELECT * FROM Events WHERE Person = %s AND Time BETWEEN %s AND %s AND acttype is not NULL ORDER BY Time ASC", (person_id,start_seconds,end_seconds))
            
            else:
                cur.execute("SELECT * FROM Events WHERE Person = %s AND acttype is not NULL ORDER BY Time ASC", (person_id,))
            results = cur.fetchall()
            results_list.extend([dict(event) for event in results])

        if event_link_id:
            # Check if start_time and end_time are provided
            if start_time and end_time:
                start_seconds = time_to_seconds(start_time)
                end_seconds = time_to_seconds(end_time)
                cur.execute(
                    "SELECT * FROM Events WHERE Link = %s AND Time BETWEEN %s AND %s ORDER BY Time ASC",
                    (event_link_id, start_seconds, end_seconds)
                )
            else:
                cur.execute("SELECT * FROM Events WHERE Link = %s ORDER BY Time ASC", (event_link_id,))
            results = cur.fetchall()
            results_list.extend([dict(event) for event in results])

      
    except Exception as e:
        return jsonify({'error': 'Database operation failed', 'details': str(e)}), 500
    finally:
        # Close communication with the database if open
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return jsonify(results_list)

@app.route('/visualize', methods=['GET'])
def visualize():

    person_id = request.args.get('personId')
    event_link_id = request.args.get('linkId')
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')
    
    if start_time and end_time:
        start_time = time_to_seconds(start_time)
        end_time = time_to_seconds(end_time)
    else:
        start_time = None if start_time == '' else start_time
        end_time = None if end_time == '' else end_time
    

    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Prepare the query to fetch events associated with the links
        event_query = """
        SELECT DISTINCT  e.linkid, e.time, e.type, e.acttype,
            from_node.x AS from_node_x, from_node.y AS from_node_y,
            to_node.x AS to_node_x, to_node.y AS to_node_y
        FROM events AS e
        JOIN links AS l ON e.linkid = l.id
        JOIN nodes AS from_node ON from_node.id = l.fromnode
        JOIN nodes AS to_node ON to_node.id = l.tonode
        WHERE (%s IS NULL OR e.person = %s)
        AND (%s IS NULL OR e.time >= %s)
        AND (%s IS NULL OR e.time <= %s)
        AND e.acttype is not NULL
        order by e.time;
        """

        # Execute the event query with parameters
        cur.execute(
            event_query,
            (person_id, person_id, start_time, start_time, end_time, end_time),
        )

        print(cur.query.decode('utf-8'))
        
        events = cur.fetchall()
        print("events:", events)
        
        if events:
            # Calculate the average midpoint for each line
            midpoints = [
                (
                    (event['from_node_x'] + event['to_node_x']) / 2,
                    (event['from_node_y'] + event['to_node_y']) / 2
                )
                for event in events
            ]

            # Set up projection conversion from UTM to WGS84
            transformer = Transformer.from_crs("epsg:32616", "epsg:4326", always_xy=True)

            # Calculate the average location of all midpoints and transform to WGS84
            avg_midpoint_x = sum(midpoint[0] for midpoint in midpoints) / len(midpoints)
            avg_midpoint_y = sum(midpoint[1] for midpoint in midpoints) / len(midpoints)
            avg_midpoint_coords = transformer.transform(avg_midpoint_x, avg_midpoint_y)

            avg_midpoint_coords = [avg_midpoint_coords[1], avg_midpoint_coords[0]]
            m = folium.Map(
                location=avg_midpoint_coords, 
                zoom_start=10,
                height='100%',  # Set the width to 80% of the container
            )
                        # m = folium.Map(width=50000,height=50000,location=[avg_midpoint_coords[1],
            #                           avg_midpoint_coords[0]], 
            #                           zoom_start=10
            #                           )

            # Add nodes and edges to the graph
            path_coordinates = []
            source_link = None
            target_link = None
            previous_link = None
            for i, event in enumerate(events):
                # Calculate the midpoint between from_node and to_node
                midpoint_x = (event['from_node_x'] + event['to_node_x']) / 2
                midpoint_y = (event['from_node_y'] + event['to_node_y']) / 2
                # Transform the midpoint coordinates to WGS84
                midpoint_coords = transformer.transform(midpoint_x, midpoint_y)
                if i == 0: # source
                    source_link = event['linkid']
                elif i == len(events) - 1: # target
                    target_link = event['linkid']
                    # avoid the case where source_link is the same as target_link (in case of Home)
                    if target_link == source_link:
                        target_link = previous_link

                # last location is Home and should be added again
                if (midpoint_coords[1], midpoint_coords[0]) in path_coordinates: #and event['acttype'] != "Home":
                    continue

                previous_link = event['linkid']
                
                # Determine the icon settings based on the activity type
                print("event['acttype']: ", event['acttype'])
                if event['acttype'] in activity_to_settings:
                    setting = activity_to_settings[event['acttype']]
                    icon = folium.Icon(icon=setting.icon_name, color=setting.icon_color)
                else:
                    # If the activity type is not found in the mappings, use a default grey icon
                    icon = folium.Icon(icon='info-sign', color='gray')

                folium.Marker(
                    location=[midpoint_coords[1], midpoint_coords[0]],  # Correct order (lat, lon)
                    icon=icon,
                    popup=f"Activity: {event['acttype']}<br>Time: {event['time']}<br>Type: {event['type']}",
                    tooltip="click for details",
                ).add_to(m)


                path_coordinates.append((midpoint_coords[1], midpoint_coords[0]))
            
            # print("path_coordinates", len(path_coordinates), path_coordinates)

            # Create a PolyLine for the shortest path
            folium.PolyLine(
                locations=path_coordinates,
                color="red",
                weight=3,
                opacity=1,
            ).add_to(m)

            # calculate the shortest path betwee two nodes and show the path
            m = calc_shortest_path(source_link, target_link, cur, m)
            # Add markers for midpoints along the shortest path
            for i in range(len(path_coordinates) - 1):
                # Calculate the midpoint between two consecutive points
                midpoint_lat = (path_coordinates[i][0] + path_coordinates[i + 1][0]) / 2
                midpoint_lon = (path_coordinates[i][1] + path_coordinates[i + 1][1]) / 2

                # Add marker for the midpoint with a label
                folium.Marker(
                    location=[midpoint_lat, midpoint_lon],  # Correct order (lat, lon)
                    icon=folium.DivIcon(
                        icon_size=(150, 36),
                        icon_anchor=(7, 20),
                        html=f'<div style="font-size: 12pt; color: blue; font-weight: bold;">{i + 1}</div>'
                    ),
                    popup=f"Link: {i + 1}",
                ).add_to(m)

            # Save the map to an HTML file
            map_html = m._repr_html_()  # Get HTML representation of the map
            return map_html  # Directly return the HTML content
        
        else:
            return "No results!"

    except Exception as e:
        app.logger.error("Unhandled exception", exc_info=e)
        return f"An error occurred: {e}", 500
    finally:
        # Close the database connection
        if cur:
            cur.close()
        if conn:
            conn.close()

def calc_shortest_path(source_link, target_link, cur, map):

    query = """
    SELECT node FROM pgr_dijkstra(
        'SELECT id, fromnode as source, tonode as target, length as cost FROM links',
        (SELECT fromnode FROM links WHERE id = %s),
        (SELECT fromnode FROM links WHERE id = %s)
    );
    """
    cur.execute(
        query,
        (source_link, target_link),
    )

    print(cur.query.decode('utf-8'))
    shortest_path_nodes = cur.fetchall()
    # Combine all nodes together
    shortest_path_nodes_list = [n["node"] for n in shortest_path_nodes]
    print("shortest_path_nodes_list: ", shortest_path_nodes_list)

    if shortest_path_nodes_list:
        # Define a new query to get x and y columns from nodes table using combined node IDs
        node_query = """
            SELECT id, x, y FROM nodes WHERE id IN %s; 
        """
        # Execute the node query with combined node IDs
        cur.execute(node_query, (tuple(shortest_path_nodes_list),))
        print(cur.query.decode('utf-8'))

        # Fetch all node coordinates
        shortest_path_nodes_x_y = cur.fetchall()
        print("shortest_path_nodes_x_y: ", shortest_path_nodes_x_y)

        # convert coordinates
        nodeid2coordinates = {}
        transformer = Transformer.from_crs("epsg:32616", "epsg:4326", always_xy=True)
        for node in shortest_path_nodes_x_y:
            node_latlon = transformer.transform(node["x"], node["y"])
            nodeid2coordinates[node["id"]] = (node_latlon[1], node_latlon[0]) # reverse direction for x and y need for Folium

        print("nodeid2coordinates: ", nodeid2coordinates)

        sorted_nodes = []
        for node in shortest_path_nodes_list: # contains sorted nodes by shortest path
            sorted_nodes.append(nodeid2coordinates[node])
        
        print("sorted_nodes: ", sorted_nodes)
        # Plot points and connect them with lines
        for coord in sorted_nodes:
            folium.CircleMarker(
            coord, color='black', radius=2).add_to(map)
        
        folium.PolyLine(sorted_nodes, color='green').add_to(map)

    return map


if __name__ == '__main__':
    socketio.run(app, debug=True)
