from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


@contextmanager
def section(title: str, caption: str = "") -> Iterator[None]:
    with st.container(border=True):
        st.subheader(title)
        if caption:
            st.caption(caption)
        yield


def show_plotly_chart(fig, *, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
