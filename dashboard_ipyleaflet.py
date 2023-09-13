import folium
import leafmap.foliumap as leafmap
import streamlit as st
from ipyleaflet import AntPath, LayerException
from src import etl, gpx
from utils.streamlit import DirectionalSlider
import folium.plugins as plugins


@st.cache
def load_data():
    return etl.main()


def get_lat_lon_bounds(df, padding=0.5):
    north = df["lat"].max() + padding
    south = df["lat"].min() - padding
    east = df["lon"].max() + padding
    west = df["lon"].min() - padding

    return [(south, west), (north, east)]


def handle_click(map_handle, data, **kwargs):
    route = gpx.parse(data["GPX"])
    route = gpx.positive_long(route)
    latlon = list(zip(route.lat, route.lon))
    path = AntPath(locations=latlon)

    try:
        map_handle.substitute_layer(handle_click.current, path)
    except (AttributeError, LayerException):
        map_handle.add_layer(path)

    handle_click.current = path

    map_handle.center = kwargs["coordinates"]
    map_handle.zoom = 11


if __name__ == "__main__":

    df = load_data()

    max_munros = df["Munros Climbed"].max()
    max_votes = round(df["Votes"].max(), -1)

    max_grade_cutoff = 5
    max_bog_cutoff = 5

    DirectionalSlider("Munros Climbed",
                      min_value=0,
                      max_value=int(max_munros),
                      key="munro_slider")

    DirectionalSlider("Difficulty",
                      min_value=0,
                      max_value=max_grade_cutoff,
                      key="grade_slider",
                      reverse=True)

    DirectionalSlider("Bog Factor",
                      min_value=0,
                      max_value=max_bog_cutoff,
                      key="bog_slider",
                      reverse=True)

    DirectionalSlider("User Rating",
                      min_value=0.,
                      max_value=5.,
                      step=0.5,
                      key="rating_slider")

    DirectionalSlider("No. of Votes",
                      min_value=0,
                      max_value=int(max_votes),
                      step=5,
                      key="vote_slider")

    df = df.loc[df["Munros Climbed"] >= st.session_state.munro_slider]
    df = df.loc[df["Rating"] >= st.session_state.rating_slider]
    df = df.loc[df["Votes"] >= st.session_state.vote_slider]
    df = df.loc[df["Grade"] <= st.session_state.grade_slider]
    df = df.loc[df["Bog"] <= st.session_state.bog_slider]

    max_time_cutoff = float(min(10, df["Time"].max()))

    st.sidebar.slider("Time",
                      min_value=0.,
                      max_value=max_time_cutoff,
                      value=(0., max_time_cutoff),
                      step=0.5,
                      key="time_slider")

    if st.session_state.grade_slider < max_grade_cutoff:
        df = df.loc[df["Grade"] <= st.session_state.grade_slider]

    if st.session_state.bog_slider < max_bog_cutoff:
        df = df.loc[df["Bog"] <= st.session_state.bog_slider]

    df = df.loc[df["Time"] >= st.session_state.time_slider[0]]
    if st.session_state.time_slider[1] < max_time_cutoff:
        df = df.loc[df["Time"] <= st.session_state.time_slider[1]]

    latlon = df[["lat", "lon", "Link", "Name"]]
    latlon.reset_index(drop=True, inplace=True)

    m = leafmap.Map(center=(56, 355.5))
    marker_cluster = plugins.MarkerCluster(
        locations=list(zip(latlon["lat"], latlon["lon"])),
        popups=list(latlon["Link"]),
        name="walks",
    ).add_to(m)

    # TODO: Add this back on if we can specify clickable events
    # for _, p in latlon.iterrows():
    #    mark = folium.Marker(location=(p["lat"], p["lon"]), popup=p["Link"], title=p["Name"]).add_to(marker_cluster)

    bounds = get_lat_lon_bounds(latlon)
    m.fit_bounds(bounds)

    # Display
    st.write("Scottish Walks Filter")
    m.to_streamlit()
    st.write(f"Total Walks: {len(df)}")
    st.dataframe(df)
