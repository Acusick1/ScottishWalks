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

popup_callback = (
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

# def handle_click(map_handle, data, **kwargs):
#     route = gpx.parse(data["GPX"])
#     route = gpx.positive_long(route)
#     latlon = list(zip(route.lat, route.lon))
#     path = AntPath(locations=latlon)

#     # try:
#     #    map_handle.substitute_layer(handle_click.current, path)
#     # except (AttributeError, LayerException):
#     map_handle.add_layer(path)

#     handle_click.current = path

#     map_handle.center = kwargs["coordinates"]
#     map_handle.zoom = 11
#     # map_handle.fit_bounds = get_lat_lon_bounds(route)

#     display(data)


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
    return pd.read_parquet(settings.processed_path), pd.read_parquet(settings.display_path)


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

    df, latlon = load_data()

    unique_regions = ["All"] + sorted(df["Region"].unique().tolist())
    st.selectbox("Region", unique_regions, key="region_selector")

    if "zoom" not in st.session_state or st.session_state.region_selector.lower() == "all":
        st.session_state["zoom"] = zoom_start

    get_sidebar_filters()
    df = filter_walks(df)

    m = folium.Map(center=center_start)
    fg = folium.FeatureGroup(name="walks")

    if df.shape[0]:

        latlon = latlon.loc[df.index]
        st.session_state["center"] = (latlon["lat"].mean(), latlon["lon"].mean())
        marker_cluster = fg.add_child(FastMarkerCluster(latlon[["lat", "lon", "Popup"]].values.tolist(), callback=popup_callback))
    else:
        st.write("No walks found!")
        st.session_state["center"] = center_start
        st.session_state["zoom"] = zoom_start

    df = df[["Name", "Region", "Distance", "Ascent", "Time", "Start Grid Ref", "Rating", "Votes", "Grade", "Bog", "Munros Climbed", "Munro", "Corbett", "Graham", "Donald", "Sub 2000"]]
    df = df.rename(columns={"Distance": "Distance (km)", "Ascent": "Ascent (m)", "Time": "Time (avg hrs)"})

    # Display
    st_folium(
        m, 
        feature_group_to_add=fg, 
        center=st.session_state["center"], 
        zoom=st.session_state["zoom"], 
        width=map_width,
        height=map_height
    )

    st.write(f"Total Walks: {df.shape[0]}")
    st.dataframe(df)
