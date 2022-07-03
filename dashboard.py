import streamlit as st
import leafmap.foliumap as leafmap
from src import sandbox
from utils.streamlit import DirectionalSlider


@st.cache
def load_data():
    return sandbox.main()


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

    latlon = df[["lat", "lon", "Link"]]
    latlon.reset_index(drop=True, inplace=True)

    m = leafmap.Map()
    if latlon.shape[0]:

        center = (latlon["lat"].mean(), latlon["lon"].mean())

        m.add_points_from_xy(latlon, x="lon", y="lat")

        padding = 0.05
        min_bounds = (latlon["lat"].min() - padding, latlon["lon"].min() - padding)
        max_bounds = (latlon["lat"].max() + padding, latlon["lon"].max() + padding)

        m.fit_bounds([min_bounds, max_bounds])
    else:
        m.set_center(lat=56.5, lon=355.5, zoom=6.25)

    # Display
    st.write("Scottish Walks Filter")
    m.to_streamlit()
    st.write(f"Total Walks: {len(df)}")
    st.dataframe(df)
