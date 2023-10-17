import folium
import pandas as pd
import streamlit as st
from folium.plugins import FastMarkerCluster
from streamlit_folium import st_folium
from utils.streamlit import DirectionalSlider
from config import settings

map_width, map_height = 700, 700
zoom_start = 6.25
center_start = (56.5, 355.5)

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
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    
    return pd.read_parquet(settings.processed_gpx_path, engine="fastparquet")


def filter_walks(df: pd.DataFrame) -> pd.DataFrame:

    filters = [
        (df["Region"] == st.session_state.region_selector) if st.session_state.region_selector.lower() != "all" else True,
        df["Munros Climbed"].between(*st.session_state.munro_slider),
        df["Rating"] >= st.session_state.rating_slider,
        df["Votes"] >= st.session_state.vote_slider,
        df["Time"].between(*st.session_state.time_slider),
        df["Distance"].between(*st.session_state.distance_slider),
        df["Grade"] <= st.session_state.grade_slider if st.session_state.grade_slider < MAX_VALUES["grade"] else True,
        df["Bog"] <= st.session_state.bog_slider if st.session_state.bog_slider < MAX_VALUES["bog"] else True,
        (df["Corbett"].notna() & (df["Corbett"] != "")) if st.session_state.corbett_check else True,
        (df["Graham"].notna() & (df["Graham"] != "")) if st.session_state.graham_check else True,
        (df["Donald"].notna() & (df["Donald"] != "")) if st.session_state.donald_check else True,
        (df["Sub 2000"].notna() & (df["Sub 2000"] != "")) if st.session_state.sub_2000_check else True
    ]
    
    final_condition = filters[0]
    for condition in filters[1:]:
        final_condition &= condition

    return df[final_condition]


def get_sidebar_filters() -> None:

    st.sidebar.title("Filters")
    
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
    st.sidebar.title("Quick Summit Filters")
    st.sidebar.checkbox("Corbett", key="corbett_check")
    st.sidebar.checkbox("Graham", key="graham_check")
    st.sidebar.checkbox("Donald", key="donald_check")
    st.sidebar.checkbox("Sub 2000",key="sub_2000_check")


if __name__ == "__main__":

    st.write("Scottish Walks")

    df = load_data()

    unique_regions = ["All"] + sorted(df["Region"].unique().tolist())
    st.selectbox("Region", unique_regions, key="region_selector")

    if "zoom" not in st.session_state or st.session_state.region_selector.lower() == "all":
        st.session_state["zoom"] = zoom_start

    get_sidebar_filters()
    df = filter_walks(df)

    m = folium.Map(center=center_start)
    fg = folium.FeatureGroup(name="walks")

    if "marker_cluster" not in st.session_state or set(df.index) != set(st.session_state["displayed_walks"]):

        marker_cluster = fg.add_child(FastMarkerCluster(df[["lat", "lon", "Popup", "path"]].values.tolist(), callback=marker_callback))
        st.session_state["displayed_walks"] = df.index
        st.session_state["marker_cluster"] = fg
        st.session_state["center"] = (df["lat"].mean(), df["lon"].mean())

    if not df.shape[0]:

        st.write("No walks found!")
        st.session_state["center"] = center_start
        st.session_state["zoom"] = zoom_start

    df = df[["Name", "Region", "Distance", "Ascent", "Time", "Start Grid Ref", "Rating", "Votes", "Grade", "Bog", "Munros Climbed", "Munro", "Corbett", "Graham", "Donald", "Sub 2000"]]
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

    st.write(f"Total Walks: {df.shape[0]}")
    st.dataframe(df)
