import folium
import pandas as pd
import streamlit as st
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium
from utils.streamlit import DirectionalSlider
from config import settings

map_width, map_height = 700, 600
zoom_start = 6.25
center_start = (56.5, 355.5)
auto_include_routes = 500

marker_callback = (
    """
    function (row) {
        var marker = L.marker(new L.LatLng(row[0], row[1]), {color: "red"});
        var icon = L.AwesomeMarkers.icon({
            icon: 'info-sign',
            iconColor: 'white',
            markerColor: 'green',
            prefix: 'glyphicon',
            extraClasses: 'fa-rotate-0'
        });
        marker.setIcon(icon);
        var popupContent = `<div class='display_text' style='width: 100%; height: 100%;'>${row[2]}</div>`;
        marker.bindPopup(popupContent, {maxWidth: '300'});

        return marker;
    };
    """
)

marker_route_callback = (
    """
    function (row) {
        var marker = L.marker(new L.LatLng(row[0], row[1]), {color: "red"});
        var icon = L.AwesomeMarkers.icon({
            icon: 'info-sign',
            iconColor: 'white',
            markerColor: 'green',
            prefix: 'glyphicon',
            extraClasses: 'fa-rotate-0'
        });
        marker.setIcon(icon);
        var popupContent = `<div class='display_text' style='width: 100%; height: 100%;'>${row[2]}</div>`;
        marker.bindPopup(popupContent, {maxWidth: '300'});

        marker.on('click', function() {
            if (window.lastClickedMarker == marker) {
                if (window.lastPath) {
                    window.lastPath.remove();
                    window.lastPath = null;
                }
                window.lastClickedMarker = null;
            } else {
                if (window.lastPath) {
                    window.lastPath.remove();
                }
                var path = row[3];
                window.lastPath = L.polyline.antPath(path, {color: 'blue', delay: 1500, weight: 5}).addTo(map);
                window.lastClickedMarker = marker;
            }
        });

        return marker;
    };
    """
)

# Static filters
MAX_VALUES = {
    "munro": 5,
    "grade": 5,
    "bog": 5,
    "votes": 100,
    "time": 10.0,
    "distance": 25.0
}


@st.cache_data
def load_data(include_routes: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    
    if include_routes:
        return pd.read_parquet(settings.processed_gpx_path, engine="fastparquet")
    else:
        return pd.read_parquet(settings.processed_path, engine="fastparquet")


@st.cache_resource
def add_walks_to_map(df, include_routes: bool = False):

    fg = folium.FeatureGroup(name="walks")

    if include_routes:
        return fg.add_child(FastMarkerCluster(df[["lat", "lon", "Popup", "path"]].values.tolist(), callback=marker_route_callback))
    else:
        return fg.add_child(FastMarkerCluster(df[["lat", "lon", "Popup"]].values.tolist(), callback=marker_callback))


def filter_walks(df: pd.DataFrame) -> pd.DataFrame:

    filters = [
        (df["Region"] == st.session_state.region_selector) if st.session_state.region_selector.lower() != "all" else True,
        df["Munros Climbed"] >= st.session_state.munro_slider[0],
        df["Munros Climbed"] <= st.session_state.munro_slider[1] if st.session_state.munro_slider[1] < MAX_VALUES["munro"] else True,
        df["Rating"] >= st.session_state.rating_slider,
        df["Votes"] >= st.session_state.vote_slider,
        df["Time"] >= st.session_state.time_slider[0],
        df["Time"] <= st.session_state.time_slider[1] if st.session_state.time_slider[1] < MAX_VALUES["time"] else True,
        df["Distance"] >= st.session_state.distance_slider[0],
        df["Distance"] <= st.session_state.distance_slider[1] if st.session_state.distance_slider[1] < MAX_VALUES["distance"] else True,
        df["Grade"] <= st.session_state.grade_slider if st.session_state.grade_slider < MAX_VALUES["grade"] else True,
        df["Bog"] <= st.session_state.bog_slider if st.session_state.bog_slider < MAX_VALUES["bog"] else True,
        (df["Corbett"].notna() & (df["Corbett"] != "")) if st.session_state.corbett_check else True,
        (df["Fiona"].notna() & (df["Fiona"] != "")) if st.session_state.fiona_check else True,
        (df["Donald"].notna() & (df["Donald"] != "")) if st.session_state.donald_check else True,
        (df["Sub 2000"].notna() & (df["Sub 2000"] != "")) if st.session_state.sub_2000_check else True
    ]
    
    final_condition = filters[0]
    for condition in filters[1:]:
        final_condition &= condition

    return df[final_condition]


def get_filters() -> None:

    st.sidebar.subheader("Walk Filters")
    
    st.sidebar.slider("Munros Climbed",
                      min_value=0,
                      max_value=MAX_VALUES["munro"],
                      value=(0, MAX_VALUES["munro"]),
                      key="munro_slider")

    DirectionalSlider("Difficulty",
                      min_value=0,
                      max_value=MAX_VALUES["grade"],
                      key="grade_slider",
                      reverse=True)

    DirectionalSlider("Bog Factor",
                      min_value=0,
                      max_value=MAX_VALUES["bog"],
                      key="bog_slider",
                      reverse=True)

    DirectionalSlider("User Rating",
                      min_value=0.,
                      max_value=5.,
                      step=0.5,
                      key="rating_slider")

    DirectionalSlider("No. of Votes",
                      min_value=0,
                      max_value=max(MAX_VALUES["votes"], 5),
                      step=5,
                      key="vote_slider")

    st.sidebar.slider("Time (avg hours)",
                      min_value=0.,
                      max_value=MAX_VALUES["time"],
                      value=(0., MAX_VALUES["time"]),
                      step=0.5,
                      key="time_slider")

    st.sidebar.slider("Distance (km)",
                    min_value=0.,
                    max_value=MAX_VALUES["distance"],
                    value=(0., MAX_VALUES["distance"]),
                    step=1.,
                    key="distance_slider")
    
    # Checkbox filters
    st.sidebar.subheader("Summit Filters")
    st.sidebar.checkbox("Corbett", key="corbett_check")
    st.sidebar.checkbox("Fiona", key="fiona_check")
    st.sidebar.checkbox("Donald", key="donald_check")
    st.sidebar.checkbox("Sub 2000",key="sub_2000_check")


if __name__ == "__main__":

    st.title("Scottish Walks")
    st.markdown(
        """
        Search for stunning walks in Scotland!\n 
        Use the map to search for walks and use the filters to narrow your search. Walks can also be viewed and sorted in the table below the map.\n
        **For mobile users:** click the top left arrow to view walk filters.\n
        The walk information provided comes from the wonderful [walkhighlands.co.uk](https://www.walkhighlands.co.uk).
        """
    )
    st.markdown("##### View GPS paths")
    st.markdown(f"The 'View routes' checkbox enables walking routes to be visualised when a walk is clicked, but may reduce app performance when there are a large number of walks on the map (automatically turned on for less than {auto_include_routes} walks).")
    
    st.sidebar.subheader("GPS paths")
    include_routes = "routes_check" in st.session_state and st.session_state["num_walks"] < auto_include_routes
    st.sidebar.checkbox("View routes", key="routes_check", value=include_routes)
    
    df = load_data(include_routes=st.session_state["routes_check"])

    unique_regions = ["All"] + sorted(df["Region"].unique().tolist())
    st.selectbox("Region", unique_regions, key="region_selector")

    if "zoom" not in st.session_state or st.session_state.region_selector.lower() == "all":
        st.session_state["zoom"] = zoom_start

    get_filters()
    df = filter_walks(df)

    m = folium.Map(center=center_start)
    st.session_state["marker_cluster"] = add_walks_to_map(df, include_routes=st.session_state["routes_check"])

    if df.shape[0]:
        st.session_state["center"] = (df["lat"].mean(), df["lon"].mean())
        st.session_state["num_walks"] = df.shape[0]
    else:
        # TODO: No walks found! Reset filters? [reset button]
        st.markdown("##### No walks found!")
        st.session_state["center"] = center_start
        st.session_state["zoom"] = zoom_start
        st.session_state["num_walks"] = 0

    df = df[["Name", "Region", "Distance", "Ascent", "Time", "Start Grid Ref", "Rating", "Votes", "Grade", "Bog", "Munros Climbed", "Munro", "Corbett", "Fiona", "Donald", "Sub 2000"]]
    df = df.rename(columns={"Distance": "Distance (km)", "Ascent": "Ascent (m)", "Time": "Time (avg hrs)"})

    # Display
    st_folium(
        m, 
        feature_group_to_add=st.session_state["marker_cluster"], 
        center=st.session_state["center"], 
        zoom=st.session_state["zoom"], 
        width=map_width,
        height=map_height
    )

    st.markdown(f"Total Walks: {df.shape[0]}")
    st.dataframe(df.reset_index(drop=True))
