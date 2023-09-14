import pandas as pd
import streamlit as st
import leafmap.foliumap as leafmap
from utils.streamlit import DirectionalSlider
from settings import DATASET_PATH


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


@st.cache
def load_data():
    return pd.read_parquet(DATASET_PATH)


def filter_walks(df: pd.DataFrame):

    filters = [
        (df["Region"] == st.session_state.region_selector) if st.session_state.region_selector != "All" else True,
        df["Munros Climbed"].between(*st.session_state.munro_slider),
        df["Rating"] >= st.session_state.rating_slider,
        df["Votes"] >= st.session_state.vote_slider,
        df["Time"].between(*st.session_state.time_slider),
        df["Distance"].between(*st.session_state.distance_slider),
        df["Grade"] <= st.session_state.grade_slider if st.session_state.grade_slider < MAX_VALUES["grade"] else True,
        df["Bog"] <= st.session_state.bog_slider if st.session_state.bog_slider < MAX_VALUES["bog"] else True,
        (df["Corbett"].notna() & df["Corbett"] != "") if st.session_state.corbett_check else True,
        (df["Graham"].notna() & df["Graham"] != "") if st.session_state.graham_check else True,
        (df["Donald"].notna() & df["Donald"] != "") if st.session_state.donald_check else True,
        (df["Sub 2000"].notna() & df["Sub 2000"] != "") if st.session_state.sub_2000_check else True
    ]
    
    final_condition = filters[0]
    for condition in filters[1:]:
        final_condition &= condition

    return df[final_condition]


def get_sidebar_filters():

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

    get_sidebar_filters()
    df = filter_walks(df)

    m = leafmap.Map()
    if df.shape[0]:

        latlon = df[["lat", "lon", "Name", "Distance", "Time", "Ascent", "Rating", "Link", "GPX"]].copy()
        latlon = latlon.dropna(subset=["lat", "lon"]).reset_index(drop=True)

        latlon["Distance"] = latlon["Distance"].apply(lambda x: f"{x}km")
        latlon["Ascent"] = latlon["Ascent"].apply(lambda x: f"{x}m")
        latlon["Rating"] = latlon["Rating"].apply(lambda x: f"{x:.2f}/5")
        latlon["Time"] = latlon["Time"].apply(lambda x: f"{x:.2f} hours (avg)")

        center = (latlon["lat"].mean(), latlon["lon"].mean())

        # for _, p in filtered_df.iterrows():
        #     mark = Marker(location=(p["lat"], p["lon"]), draggable=False, title=p["Name"])
        #     mark.on_click(functools.partial(handle_click, m, p))
        #     markers.append(mark)

        # marker_cluster = MarkerCluster(markers=markers)
        # m.add_layer(marker_cluster)

        m.add_points_from_xy(latlon, x="lon", y="lat", popup=latlon.columns[2:])

        padding = 0.05
        min_bounds = (latlon["lat"].min() - padding, latlon["lon"].min() - padding)
        max_bounds = (latlon["lat"].max() + padding, latlon["lon"].max() + padding)

        m.fit_bounds([min_bounds, max_bounds])
    else:
        m.set_center(lat=56.5, lon=355.5, zoom=6.25)

    display_df = df.copy()
    display_df = display_df[["Name", "Region", "Distance", "Ascent", "Time", "Start Grid Ref", "Rating", "Votes", "Grade", "Bog", "Munros Climbed", "Munro", "Corbett", "Graham", "Donald", "Sub 2000"]]
    display_df = display_df.rename(columns={"Distance": "Distance (km)", "Ascent": "Ascent (m)", "Time": "Time (avg hrs)"})

    # Display
    m.to_streamlit()
    st.write(f"Total Walks: {display_df.shape[0]}")
    st.dataframe(display_df)
