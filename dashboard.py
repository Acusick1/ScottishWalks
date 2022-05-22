import pandas as pd
import streamlit as st
from src import sandbox
import leafmap.foliumap as leafmap

numeric = (int, float)


@st.cache
def load_data():
    return sandbox.main()


class directional_slider():

    reverse = False
    key = ""

    def __init__(self,
                 name: str,
                 min_value: numeric,
                 max_value: numeric,
                 key: str,
                 reverse: bool = False,
                 sidebar: bool = True,
                 **kwargs):

        """Abstraction layer for st.slider, sets slider initial value based on whether slider values are omitted in an
                ascending or descending fashion. Also defines method to omit values as such."""

        # TODO: Ensure kwargs are not duplicated by args (or vice versa)

        value = max_value if reverse else min_value

        # TODO: How to pass args as single variable
        if sidebar:
            st.sidebar.slider(name,
                              min_value=min_value,
                              max_value=max_value,
                              value=value,
                              key=key,
                              **kwargs)
        else:
            st.slider(name,
                      min_value=min_value,
                      max_value=max_value,
                      value=value,
                      key=key,
                      **kwargs)

    def on_change(self, df: pd.DataFrame, col: str):

        if self.reverse:

            df = df.loc[df[col] <= st.session_state[self.key]]
        else:
            df = df.loc[df[col] >= st.session_state[self.key]]

        return df


if __name__ == "__main__":

    df = load_data()

    max_munros = df["Munros Climbed"].max()
    max_votes = round(df["Votes"].max(), -1)

    max_grade_cutoff = 5
    max_bog_cutoff = 5

    munro_slider = directional_slider("Munros Climbed",
                                      min_value=0,
                                      max_value=int(max_munros),
                                      key="munro_slider")

    directional_slider("Difficulty",
                       min_value=0,
                       max_value=max_grade_cutoff,
                       key="grade_slider",
                       reverse=True)

    directional_slider("Bog Factor",
                       min_value=0,
                       max_value=max_bog_cutoff,
                       key="bog_slider",
                       reverse=True)

    directional_slider("User Rating",
                       min_value=0.,
                       max_value=5.,
                       step=0.5,
                       key="rating_slider")

    directional_slider("No. of Votes",
                       min_value=0,
                       max_value=int(max_votes),
                       step=5,
                       key="vote_slider")

    df = munro_slider.on_change(df, "Munros Climbed")
    # df = df.loc[df["Munros Climbed"] >= st.session_state.munro_slider]
    df = df.loc[df["Rating"] >= st.session_state.rating_slider]
    df = df.loc[df["Votes"] >= st.session_state.vote_slider]
    df = df.loc[df["Grade"] <= st.session_state.grade_slider]
    df = df.loc[df["Bog"] <= st.session_state.bog_slider]

    max_time_cutoff = float(min(10, df["Time"].max()))

    st.sidebar.slider("Time",
                      min_value=0.,
                      max_value=max_time_cutoff,
                      value=(0., max_time_cutoff),
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

    m = leafmap.Map(center=(56, 355), zoom=6)
    m.add_points_from_xy(latlon, x="lon", y="lat")

    # Display
    st.write("Scottish Walks Filter")
    m.to_streamlit()

    # st.map(latlon)
    st.write(f"Total Walks: {len(df)}")
    st.dataframe(df)
