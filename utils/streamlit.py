import pandas as pd
import streamlit as st
from typing import Union


class DirectionalSlider:

    reverse = False
    key = ""

    def __init__(self,
                 name: str,
                 min_value: Union[int, float],
                 max_value: Union[int, float],
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

        self.key = key

    def on_change(self, df: pd.DataFrame, col: str):
        """
        if self.reverse:

            df = df.loc[df[col] <= st.session_state[self.key]]
        else:
            df = df.loc[df[col] >= st.session_state[self.key]]

        return df
        """
        raise NotImplementedError()

