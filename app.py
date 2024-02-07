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

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem' 
app.secret_key = str(uuid.uuid4()) 
socketio = SocketIO(app)
#connection (change this based on your db)

db_config = {
    'dbname': 'TransportationEvents',
    'user': 'postgres',
    'password': 'shaheen1',
    'host': 'localhost',
    'port': '5432'
}
@socketio.on('connect', namespace='/progress')
def connect():
    print('Client connected to progress updates')

def time_to_seconds(time_str):
    hours, minutes = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60

def insertEventsFromXml(xml_file, conn):
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
            link_id = event_data.get('link', None)
            dvrp_vehicle = event_data.get('dvrpVehicle', None)

            events.append((time, event_type, departure_id, transit_line_id, request, act_type, purpose, vehicle, amount, transaction_partner, transit_route_id, relative_position, vehicle_id, task_index, 
                          network_mode, mode, distance, driver_id, x, y, agent, destination_stop, dvrp_mode, facility, task_type, leg_mode, person, delay, at_stop, link_id, dvrp_vehicle))
            
        
            if progress_percentage % 40 == 0:
                progress_thread = threading.Thread(target=update_progress, args=(progress_percentage, 3))
                progress_thread.start()
                
                execute_batch(cursor, "INSERT INTO Events (Time, Type, DepartureID, TransitLineID, Request, ActType, Purpose, Vehicle, Amount, TransactionPartner, TransitRouteID, RelativePosition, VehicleID, TaskIndex, NetworkMode, Mode, Distance, DriverID, X, Y, Agent, DestinationStop, DvrpMode, Facility, TaskType, LegMode, Person, Delay, AtStop, Link, DvrpVehicle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", events)

                events=[]

        if events:
            execute_batch(cursor, "INSERT INTO Events (Time, Type, DepartureID, TransitLineID, Request, ActType, Purpose, Vehicle, Amount, TransactionPartner, TransitRouteID, RelativePosition, VehicleID, TaskIndex, NetworkMode, Mode, Distance, DriverID, X, Y, Agent, DestinationStop, DvrpMode, Facility, TaskType, LegMode, Person, Delay, AtStop, Link, DvrpVehicle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", events)


        # Commit the changes to the database
        conn.commit()
        update_progress(100,3)

    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def insertLinksFromXml(xml_data, conn):
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

            links.append((link_id, from_node_id, to_node_id, length, freespeed, capacity, permlanes, oneway, modes))
            
    
            if progress_percentage % 40 == 0:
                progress_thread = threading.Thread(target=update_progress, args=(progress_percentage, 1))
                progress_thread.start()

  
                execute_batch(cursor, "INSERT INTO Links (LinkID, FromNode, ToNode, Length, FreeSpeed, Capacity, PermLanes, OneWay, Mode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", links)
                links=[]
            
        if links:
            execute_batch(cursor, "INSERT INTO Links (LinkID, FromNode, ToNode, Length, FreeSpeed, Capacity, PermLanes, OneWay, Mode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", links)



        # Commit the changes to the database
        conn.commit()
            
        update_progress(100,2)
        return 1
    
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
            nodes.append((node_id, x, y))

            if progress_percentage % 40 == 0:
                progress_thread = threading.Thread(target=update_progress, args=(progress_percentage, 1))
                progress_thread.start()
                execute_batch(cursor, "INSERT INTO Nodes (NodeID, X, Y) VALUES (%s, %s, %s)", nodes)
                nodes=[]

        if nodes:
            execute_batch(cursor, "INSERT INTO Nodes (NodeID, X, Y) VALUES (%s, %s, %s)", nodes)

        
        # Commit the changes to the database
        conn.commit()
        
        update_progress(100,1)

        return 1 
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()

@app.route('/importData', methods=['POST'])
def import_data():
    try:
        conn = psycopg2.connect(**db_config)

        files = request.files.getlist('files')


        for xml_file in files:
            if xml_file.filename == 'network.xml':
                xml_data = xml_file.read()
                insertNodesFromXml(xml_data, conn)
                progress_thread = threading.Thread(target=update_progress, args=(0,1))
                progress_thread.start()
                insertLinksFromXml(xml_data, conn)

        progress_thread = threading.Thread(target=update_progress, args=(0,1))
        progress_thread.start()
        for xml_file in files:
            if xml_file.filename != 'network.xml':
                xml_data = xml_file.read()
                insertEventsFromXml(xml_data, conn)

        session['file_imported'] = True

        return jsonify({'success': True}), 200
        conn.close()

    except Exception as e:
        print('Error processing files:', str(e))
        return jsonify({'error': 'Error processing files'}), 500

def update_progress(value, fileFlag):
    with app.app_context():
        socketio.emit('update_progress', {'value': value, 'flag':fileFlag}, namespace='/progress')

@app.route('/', methods=['GET', 'POST'])
def importRender():
    if 'file_imported' in session and session['file_imported']:
        return render_template('index.html')

    return render_template('import.html')

@app.route('/Home')
def render_another_page():
    if 'file_imported' in session and session['file_imported']:
        return render_template('index.html')
    return render_template('import.html')

@app.route('/search', methods=['GET'])
def search():
    person_id = request.args.get('personId')
    event_link_id = request.args.get('linkId')
    link_id_table = request.args.get('linkIdLinkTable')
    start_time = request.args.get('startTime')
    end_time = request.args.get('endTime')
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(**db_config)
        # Open a cursor to perform database operations
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        results_list = []

        if person_id:
            cur.execute("SELECT * FROM Events WHERE Person = %s ORDER BY Time ASC", (person_id,))
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

        if link_id_table:
            cur.execute("SELECT * FROM Links WHERE LinkID = %s", (link_id_table,))
            results = cur.fetchall()
            results_list.extend([dict(link) for link in results])

      

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

        # Prepare the query to fetch nodes with optional time filtering
        node_query = """
        SELECT DISTINCT Nodes.NodeID, Nodes.X, Nodes.Y
        FROM Nodes
        JOIN Links ON Nodes.NodeID = Links.FromNode OR Nodes.NodeID = Links.ToNode
        LEFT JOIN Events ON Links.LinkID = Events.Link
        WHERE (%s IS NULL OR Events.Person = %s)
        AND (%s IS NULL OR Events.Time >= %s)
        AND (%s IS NULL OR Events.Time <= %s);
        """

        # Execute the node query with parameters
        cur.execute(node_query, (person_id, person_id, start_time, start_time, end_time, end_time))
        nodes = cur.fetchall()

        # Prepare the query to fetch links with optional time filtering
        link_query = """
        SELECT DISTINCT L.LinkID, FN.X AS FromX, FN.Y AS FromY, TN.X AS ToX, TN.Y AS ToY
        FROM Links L
        JOIN Nodes FN ON L.FromNode = FN.NodeID
        JOIN Nodes TN ON L.ToNode = TN.NodeID
        LEFT JOIN Events E ON L.LinkID = E.Link
        WHERE (%s IS NULL OR E.Person = %s)
        AND (%s IS NULL OR E.Time >= %s)
        AND (%s IS NULL OR E.Time <= %s);
        """

        # Execute the link query with parameters
        cur.execute(link_query, (person_id, person_id, start_time, start_time, end_time, end_time))
        links = cur.fetchall()

        
        # Set up projection conversion from UTM to WGS84
        transformer = Transformer.from_crs('epsg:32616', 'epsg:4326', always_xy=True)

        # Convert node coordinates from UTM to WGS84 and calculate the average location to center the map
        converted_nodes = [(transformer.transform(float(node['x']), float(node['y'])), node['nodeid']) for node in nodes]
        if converted_nodes:
            avg_lon = sum(coord[0][0] for coord in converted_nodes) / len(converted_nodes)
            avg_lat = sum(coord[0][1] for coord in converted_nodes) / len(converted_nodes)
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
        else:
            m = folium.Map(location=[0, 0], zoom_start=2)
        
        # Add nodes to the map
        for (lon, lat), node_id in converted_nodes:
            folium.Marker(
                location=[lat, lon], 
                popup=f"Node ID: {node_id}",
            ).add_to(m)
        
        # Convert link coordinates from UTM to WGS84 and add to the map
        for link in links:
            from_coord = transformer.transform(float(link['fromx']), float(link['fromy']))
            to_coord = transformer.transform(float(link['tox']), float(link['toy']))
            folium.PolyLine(
                locations=[from_coord[::-1], to_coord[::-1]],  # Flip coords because folium uses (lat, lon)
                color="blue",
                weight=2.5,
                opacity=1,
            ).add_to(m).add_child(folium.Popup(f"Link ID: {link['linkid']}"))
        
        
        # Generate and return map HTML
        map_html = m._repr_html_()  # Get HTML representation of the map
        return map_html  # Directly return the HTML content
    except Exception as e:
        app.logger.error('Unhandled exception', exc_info=e)
        return f"An error occurred: {e}", 500
    finally:
        print("Visual called.")


if __name__ == '__main__':
    socketio.run(app, debug=True)
