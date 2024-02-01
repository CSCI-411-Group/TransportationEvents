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
from openrouteservice import client, exceptions
import requests


app = Flask(__name__)

# connection (change this based on your db)
db_config = {
    "dbname": "TransportationEvents",
    "user": "postgres",
    "password": "user",
    "host": "localhost",
    "port": "5432",
}

api_key = "5b3ce3597851110001cf6248870bfb5c453e47d6956f27082a983fbd"  # Replace with your actual API key
client = client.Client(key=api_key)


def get_route(from_coord, to_coord):
    headers = {
        "Accept": "application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8",
    }

    try:
        url = "https://api.openrouteservice.org/v2/directions/driving-car"
        params = {
            "api_key": api_key,
            "start": f"{from_coord[0]},{from_coord[1]}",
            "end": f"{to_coord[0]},{to_coord[1]}",
            "format": "geojson",
        }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Raise HTTPError for bad responses

        data = response.json()
        features = data.get("features", [])

        if not features:
            raise ValueError("No features found in the OpenRouteService response")

        # Extracting the route geometry
        geometry = features[0]["geometry"]["coordinates"]
        return [(lat, lon) for lon, lat in geometry]

    except requests.exceptions.HTTPError as http_err:
        raise ValueError(f"HTTP error occurred: {http_err}")

    except ValueError as value_err:
        raise value_err  # Propagate the existing ValueError

    except Exception as e:
        raise ValueError(f"An error occurred: {e}")


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


@app.route("/visualize", methods=["GET"])
def visualize():
    person_id = request.args.get("personId")
    start_time = request.args.get("startTime")
    end_time = request.args.get("endTime")

    if start_time and end_time:
        start_time = time_to_seconds(start_time)
        end_time = time_to_seconds(end_time)
    else:
        start_time = None if start_time == "" else start_time
        end_time = None if end_time == "" else end_time

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
        cur.execute(
            node_query,
            (person_id, person_id, start_time, start_time, end_time, end_time),
        )
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
        cur.execute(
            link_query,
            (person_id, person_id, start_time, start_time, end_time, end_time),
        )
        links = cur.fetchall()

        # Prepare the query to fetch events associated with the links
        event_query = """
        SELECT E.Time, L.FromNode, L.ToNode
        FROM Events E
        JOIN Links L ON E.Link = L.LinkID
        WHERE (%s IS NULL OR E.Person = %s)
        AND (%s IS NULL OR E.Time >= %s)
        AND (%s IS NULL OR E.Time <= %s);
        """

        # Execute the event query with parameters
        cur.execute(
            event_query,
            (person_id, person_id, start_time, start_time, end_time, end_time),
        )
        events = cur.fetchall()

        # Set up projection conversion from UTM to WGS84
        transformer = Transformer.from_crs("epsg:32616", "epsg:4326", always_xy=True)

        # Convert node coordinates from UTM to WGS84 and calculate the average location to center the map
        converted_nodes = [
            (transformer.transform(float(node["x"]), float(node["y"])), node["nodeid"])
            for node in nodes
        ]
        if converted_nodes:
            avg_lon = sum(coord[0][0] for coord in converted_nodes) / len(
                converted_nodes
            )
            avg_lat = sum(coord[0][1] for coord in converted_nodes) / len(
                converted_nodes
            )
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
        else:
            m = folium.Map(location=[0, 0], zoom_start=2)

        # Initialize variables to store route start and end nodes
        route_start = None
        route_end = None

        for i, ((lon, lat), node_id) in enumerate(converted_nodes):
            popup_content = f"Node ID: {node_id}"

            # Check if the node is associated with any taxi fare
            associated_events = [
                event
                for event in events
                if node_id in (event["fromnode"], event["tonode"])
            ]

            # Save the first fare start node as route start
            if i == 0 and not route_start:
                route_start = {"location": [lat, lon], "popup": popup_content}

            # Save the last fare end node as route end
            if i == len(converted_nodes) - 1:
                route_end = {"location": [lat, lon], "popup": popup_content}

            # Check if the node is associated with any taxi fare
            if any(event["fromnode"] == node_id for event in associated_events):
                folium.Marker(
                    location=[lat, lon],
                    popup=popup_content,
                    icon=folium.Icon(color="green"),
                    tooltip="Taxi Fare Start",
                ).add_to(m)

            # Check if the node is the end of any taxi fare
            if any(event["tonode"] == node_id for event in associated_events):
                folium.Marker(
                    location=[lat, lon],
                    popup=popup_content,
                    icon=folium.Icon(color="red"),
                    tooltip="Taxi Fare End",
                ).add_to(m)

            # Add markers for route start and end with adjusted popup anchor
            if route_start:
                folium.Marker(
                    location=route_start["location"],
                    popup=route_start["popup"],
                    icon=folium.Icon(color="blue"),
                    tooltip="Route Start",
                ).add_to(m)

            if route_end:
                folium.Marker(
                    location=route_end["location"],
                    popup=route_end["popup"],
                    icon=folium.Icon(color="purple"),
                    tooltip="Route End",
                ).add_to(m)


        """
        # Convert link coordinates from UTM to WGS84 and add to the map
        for link in links:
            from_coord_utm = [float(link["fromx"]), float(link["fromy"])]
            to_coord_utm = [float(link["tox"]), float(link["toy"])]

            from_coord_utm_2 = [float(link["fromx"]), float(link["fromy"])]
            to_coord_utm_2 = [float(link["tox"]), float(link["toy"])]

            from_coord_wgs84 = transformer.transform(*from_coord_utm)
            to_coord_wgs84 = transformer.transform(*to_coord_utm)

            from_coord_wgs84_2 = transformer.transform(*from_coord_utm_2)
            to_coord_wgs84_2 = transformer.transform(*to_coord_utm_2)

            # Get route geometry from OpenRouteService
            route_geometry = get_route(from_coord_wgs84, to_coord_wgs84)
            route_geometry2 = get_route(to_coord_wgs84_2, from_coord_wgs84)

            # Add PolyLine to the map
            folium.PolyLine(
                locations=route_geometry,
                color="blue",
                weight=2.5,
                opacity=1,
            ).add_to(m).add_child(folium.Popup(f"Link ID: {link['linkid']}"))

            folium.PolyLine(
                locations=route_geometry2,
                color="red",
                weight=2.5,
                opacity=1,
            ).add_to(m).add_child(folium.Popup(f"Link ID: {link['linkid']}"))
            time.sleep(1)
        """
        for link in links:
            from_coord = transformer.transform(
                float(link["fromx"]), float(link["fromy"])
            )
            to_coord = transformer.transform(float(link["tox"]), float(link["toy"]))
            folium.PolyLine(
                locations=[
                    from_coord[::-1],
                    to_coord[::-1],
                ],  # Flip coords because folium uses (lat, lon)
                color="blue",
                weight=2.5,
                opacity=1,
            ).add_to(m).add_child(folium.Popup(f"Link ID: {link['linkid']}"))

        # Generate and return map HTML
        map_html = m._repr_html_()  # Get HTML representation of the map
        return map_html  # Directly return the HTML content
    except Exception as e:
        app.logger.error("Unhandled exception", exc_info=e)
        return f"An error occurred: {e}", 500
    finally:
        print("Visual called.")


if __name__ == "__main__":
    app.run(debug=True)
