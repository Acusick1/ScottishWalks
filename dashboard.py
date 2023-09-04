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
max_munro_cutoff = 5
max_grade_cutoff = 5
max_bog_cutoff = 5
max_votes_cutoff = 100
max_time_cutoff = 10.
max_dist = 25.


@st.cache
def load_data():
    return pd.read_parquet(DATASET_PATH)


def sidebar_filters(df: pd.DataFrame):

    df = df.loc[df["Munros Climbed"] >= st.session_state.munro_slider[0]]
    df = df.loc[df["Rating"] >= st.session_state.rating_slider]
    df = df.loc[df["Votes"] >= st.session_state.vote_slider]
    df = df.loc[df["Time"] >= st.session_state.time_slider[0]]
    df = df.loc[(df["Distance"] >= st.session_state.distance_slider[0]) & (df["Distance"] <= st.session_state.distance_slider[1])]
    
    if st.session_state.munro_slider[1] < max_munro_cutoff:
        df = df.loc[df["Munros Climbed"] <= st.session_state.munro_slider[1]]

    if st.session_state.grade_slider < max_grade_cutoff:
        df = df.loc[df["Grade"] <= st.session_state.grade_slider]

    if st.session_state.bog_slider < max_bog_cutoff:
        df = df.loc[df["Bog"] <= st.session_state.bog_slider]
    
    if st.session_state.time_slider[1] < max_time_cutoff:
        df = df.loc[df["Time"] <= st.session_state.time_slider[1]]

    return df


def get_sliders(df: pd.DataFrame):

    # Dynamic filters
    if df.shape[0]:
        max_votes = min(round(int(df["Votes"].max()), -1), max_votes_cutoff)
    else:
        max_votes = 1
    
    st.sidebar.slider("Munros Climbed",
                      min_value=0,
                      max_value=max_munro_cutoff,
                      value=(0, max_munro_cutoff),
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
                      max_value=max(max_votes, 5),
                      step=5,
                      key="vote_slider")

    st.sidebar.slider("Time (avg hours)",
                      min_value=0.,
                      max_value=max_time_cutoff,
                      value=(0., max_time_cutoff),
                      step=0.5,
                      key="time_slider")

    st.sidebar.slider("Distance (km)",
                    min_value=0.,
                    max_value=max_dist,
                    value=(0., max_dist),
                    step=1.,
                    key="distance_slider")

if __name__ == "__main__":

    st.write("Scottish Walks")

    df = load_data()

    unique_regions = sorted(df['Area0'].unique().tolist())
    unique_regions.insert(0, 'All')

    st.selectbox('Region', unique_regions, key="region_selector")

    # Filter based on the selected_region
    if st.session_state.region_selector != 'All':
        df = df[df['Area0'] == st.session_state.region_selector]

    try:
        if "time_slider" in st.session_state:
            df = sidebar_filters(df)

    except Exception as e:
        print(e)


    st.sidebar.title("Filters")
    get_sliders(df)

    st.sidebar.title("Quick Summit Filters")
    # Sidebar with checkboxes
    corbett_check = st.sidebar.checkbox('Corbett')
    graham_check = st.sidebar.checkbox('Graham')
    donald_check = st.sidebar.checkbox('Donald')
    sub_2000_check = st.sidebar.checkbox('Sub 2000')

    # Filter DataFrame based on selected checkboxes
    if corbett_check and df.shape[0]:
        df = df[(df['Corbett'].notna()) & (df['Corbett'] != '')]

    if graham_check and df.shape[0]:
        df = df[(df['Graham'].notna()) & (df['Graham'] != '')]

    if donald_check and df.shape[0]:
        df = df[(df['Donald'].notna()) & (df['Donald'] != '')]

    if sub_2000_check and df.shape[0]:
        df = df[(df['Sub 2000'].notna()) & (df['Sub 2000'] != '')]

    m = leafmap.Map()
    if df.shape[0]:

        latlon = df[["lat", "lon", "Name", "Distance", "Time", "Ascent", "Rating", "Link", "GPX"]].copy()
        latlon["Distance"] = latlon["Distance"].apply(lambda x: f"{x}km")
        latlon["Ascent"] = latlon["Ascent"].apply(lambda x: f"{x}m")
        latlon = latlon.dropna(subset=["lat", "lon"]).reset_index(drop=True)

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
    display_df = display_df[["Name", "Area0", "Distance", "Ascent", "Time", "Start Grid Ref", "Rating", "Votes", "Grade", "Bog", "Munros Climbed", "Munro", "Corbett", "Graham", "Donald", "Sub 2000"]]
    display_df = display_df.rename(columns={"Area0": "Region", "Distance": "Distance (km)", "Ascent": "Ascent (m)", "Time": "Time (avg hrs)"})

    # Display
    m.to_streamlit()
    st.write(f"Total Walks: {len(df)}")
    st.dataframe(display_df)
