import xml.etree.ElementTree as ET
import time
import psycopg2
from lxml import etree
from psycopg2.extras import execute_batch, NamedTupleCursor
import os

db_config = {
    'dbname': 'TransportationEvents',
    'user': 'postgres',
    'password': '.',
    'host': 'localhost',
    'port': '5432'
}


def insertNodesFromXml(xml_file, db_config):
    # Parse the XML file
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_file, parser=parser)
    root = tree.getroot()
    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=NamedTupleCursor)

    try:
        # Iterate through nodes and insert them into the "Nodes" table
        nodes = []
        for node in root.findall('.//node'):
            node_id = node.get('id')
            x = float(node.get('x'))
            y = float(node.get('y'))
            nodes.append((node_id, x, y))
        
        # Insert the node into the database
        execute_batch(cursor, "INSERT INTO Nodes (NodeID, X, Y) VALUES (%s, %s, %s)", nodes)
        
        # Commit the changes to the database
        conn.commit()
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()


def insertLinksFromXml(xml_file, db_config):
    # Parse the XML file
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_file, parser=parser)
    root = tree.getroot()

    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor(cursor_factory=NamedTupleCursor)

    try:
        # Iterate through link elements and insert them into the "Links" table
        links = []
        for link_data in root.findall('.//link'):
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
        
        execute_batch(cursor, "INSERT INTO Links (LinkID, FromNode, ToNode, Length, FreeSpeed, Capacity, PermLanes, OneWay, Mode) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", links)
        
        # Commit the changes to the database
        conn.commit()
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()


def insertEventsFromXml(xml_file, db_config):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Connect to the PostgreSQL database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()

    try:
        # Iterate through event elements and insert them into the "Events" table
        events = []
        for event_data in root.findall('.//event'):
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

        execute_batch(cursor, "INSERT INTO Events (Time, Type, DepartureID, TransitLineID, Request, ActType, Purpose, Vehicle, Amount, TransactionPartner, TransitRouteID, RelativePosition, VehicleID, TaskIndex, NetworkMode, Mode, Distance, DriverID, X, Y, Agent, DestinationStop, DvrpMode, Facility, TaskType, LegMode, Person, Delay, AtStop, Link, DvrpVehicle) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", events)

        # Commit the changes to the database
        conn.commit()
    
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()


nodesLinksXmlFile = os.path.join("data", "network.xml")
eventsXmlFile = os.path.join("data", "output_events.xml")

start_time = time.perf_counter()
insertNodesFromXml(nodesLinksXmlFile, db_config)
insertLinksFromXml(nodesLinksXmlFile, db_config)
insertEventsFromXml(eventsXmlFile, db_config)
end_time = time.perf_counter()

time_taken = end_time - start_time
minutes, seconds = divmod(time_taken, 60)
print(f"Database loaded!\nTime taken: {int(minutes)} min {int(seconds)} sec")