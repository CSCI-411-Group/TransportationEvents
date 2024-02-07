from flask import (
    Flask,
    request,
    render_template,
    redirect,
    url_for,
    jsonify,
    flash,
    session,
)
import psycopg2
import psycopg2.extras
import folium
from pyproj import Transformer
import time
import networkx as nx
import requests


app = Flask(__name__)

# connection (change this based on your db)
db_config = {
    "dbname": "TransportationEvents",
    "user": "postgres",
    "password": ".",
    "host": "localhost",
    "port": "5432",
}


def time_to_seconds(time_str):
    hours, minutes = map(int, time_str.split(":"))
    return hours * 3600 + minutes * 60

@app.route("/", methods=["GET", "POST"])
def create():
    return render_template("index.html")

@app.route("/search", methods=["GET"])
def search():
    person_id = request.args.get("personId")
    event_link_id = request.args.get("linkId")
    link_id_table = request.args.get("linkIdLinkTable")
    start_time = request.args.get("startTime")
    end_time = request.args.get("endTime")
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(**db_config)
        # Open a cursor to perform database operations
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        results_list = []

        if person_id:
            cur.execute(
                "SELECT * FROM Events WHERE Person = %s ORDER BY Time ASC", (person_id,)
            )
            results = cur.fetchall()
            results_list.extend([dict(event) for event in results])

        if event_link_id:
            # Check if start_time and end_time are provided
            if start_time and end_time:
                start_seconds = time_to_seconds(start_time)
                end_seconds = time_to_seconds(end_time)
                cur.execute(
                    "SELECT * FROM Events WHERE Link = %s AND Time BETWEEN %s AND %s ORDER BY Time ASC",
                    (event_link_id, start_seconds, end_seconds),
                )
            else:
                cur.execute(
                    "SELECT * FROM Events WHERE Link = %s ORDER BY Time ASC",
                    (event_link_id,),
                )
            results = cur.fetchall()
            results_list.extend([dict(event) for event in results])

        if link_id_table:
            cur.execute("SELECT * FROM Links WHERE LinkID = %s", (link_id_table,))
            results = cur.fetchall()
            results_list.extend([dict(link) for link in results])

    except Exception as e:
        return jsonify({"error": "Database operation failed", "details": str(e)}), 500
    finally:
        # Close communication with the database if open
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

    return jsonify(results_list)

def calculate_distance(coord1, coord2):
    # Simple function to calculate Euclidean distance between two points
    return ((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)**0.5

@app.route("/visualize", methods=["GET"])
def visualize():
    person_id = request.args.get("personId")
    start_time = request.args.get("startTime") or None
    end_time = request.args.get("endTime") or None

    if not person_id:
        return "person_id is required!"
    if start_time:
        start_time = time_to_seconds(start_time)
    if end_time:
        end_time = time_to_seconds(end_time)
    
    print(person_id, start_time, end_time)

    conn = None
    cur = None
    try:
        # Connect to your postgres DB
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Prepare the query to fetch events associated with the links
        event_query = """
        SELECT DISTINCT  e.link, e.time, e.type, e.acttype,
            from_node.x AS from_node_x, from_node.y AS from_node_y,
            to_node.x AS to_node_x, to_node.y AS to_node_y
        FROM events AS e
        JOIN links AS l ON e.link = l.linkid
        JOIN nodes AS from_node ON from_node.nodeid = l.fromnode
        JOIN nodes AS to_node ON to_node.nodeid = l.tonode
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
        print(events)
        
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

            m = folium.Map(location=[avg_midpoint_coords[1], avg_midpoint_coords[0]], zoom_start=10)

            # Add nodes and edges to the graph
            path_coordinates = []
            for i, event in enumerate(events):
                # Calculate the midpoint between from_node and to_node
                midpoint_x = (event['from_node_x'] + event['to_node_x']) / 2
                midpoint_y = (event['from_node_y'] + event['to_node_y']) / 2

                # Transform the midpoint coordinates to WGS84
                midpoint_coords = transformer.transform(midpoint_x, midpoint_y)

                # last location is Home and should be added again
                if (midpoint_coords[1], midpoint_coords[0]) in path_coordinates and event['acttype'] != "Home":
                    continue

                folium.Marker(
                    location= [midpoint_coords[1], midpoint_coords[0]],  # Correct order (lat, lon)
                    icon=folium.Icon(color="green"),
                    popup=f"Activity: {event['acttype']}<br>Time: {event['time']}<br>Type: {event['type']}",
                    tooltip="click for details",
                ).add_to(m)

                path_coordinates.append((midpoint_coords[1], midpoint_coords[0]))
            
            print("path_coordinates", len(path_coordinates), path_coordinates)

            # Create a PolyLine for the shortest path
            folium.PolyLine(
                locations=path_coordinates,
                color="red",
                weight=3,
                opacity=1,
            ).add_to(m)

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


if __name__ == "__main__":
    app.run(debug=True)
