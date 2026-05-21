from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import streamlit as st


@contextmanager
def section(title: str, caption: str = "") -> Iterator[None]:
    import html

    with st.container(border=True):
        st.markdown(
            f'<div class="section-title">{html.escape(title)}</div>',
            unsafe_allow_html=True,
        )
        if caption:
            st.markdown(
                f'<p class="section-caption">{html.escape(caption)}</p>',
                unsafe_allow_html=True,
            )
        yield


def show_plotly_chart(fig, *, key: str) -> None:
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key=key)
