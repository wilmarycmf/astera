"""ASTERA photo studio."""
from datetime import date
import base64

import numpy as np
import streamlit as st
import streamlit.components.v1 as components

from core import (annotate, demo_photo, detect_highlights, enhance, load_photo,
                  png_bytes, recover_photo, transparent_light_layer)

st.set_page_config(page_title="ASTERA | Your sky. Your story.", page_icon="📷", layout="wide")
st.markdown('''<style>
.stApp {background:#202020;color:#e0e0e0;font-family:Arial,sans-serif}
.block-container {max-width:1500px;padding-top:3.8rem;padding-bottom:1rem}
[data-testid="stHeader"] {background:#202020}
h1,h2,h3 {font-family:Arial,sans-serif;letter-spacing:0}
[data-testid="stSidebar"] {background:#282828;border-right:1px solid #3c3c3c}
[data-testid="stSidebar"] .block-container {padding-top:1rem}
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {gap:.65rem}
[data-testid="stImage"] img {border-radius:0}
[data-testid="stDownloadButton"] button {border-radius:3px;min-height:2.3rem}
[data-testid="stMetric"] {padding:4px 0;background:none;border:0}
[data-testid="stMetricValue"] {font-size:1.3rem}
[data-testid="stFileUploaderDropzone"] {border:1px solid #4b4b4b;border-radius:3px;background:#303030}
[data-testid="stExpander"] {border-color:#444;border-radius:3px}
.brand {font-size:1.15rem;letter-spacing:.06em;font-weight:600;color:#eee;margin-bottom:.7rem}
.section-label {font-size:.8rem;font-weight:600;color:#bbb;border-top:1px solid #444;padding-top:1rem;margin-top:.5rem}
.editor-bar {display:flex;align-items:baseline;justify-content:space-between;border-bottom:1px solid #444;padding:0 0 12px;margin-bottom:10px}
.editor-name {font-size:1rem;font-weight:600;color:#e7e7e7}
.editor-mode {font-size:.75rem;color:#aaa}
.foot {color:#999;font-size:.7rem;border-top:1px solid #3c3c3c;padding-top:.7rem;margin-top:1rem}
</style>''', unsafe_allow_html=True)

@st.cache_data(show_spinner=False, max_entries=3)
def read_image(data):
    return load_photo(data)

@st.cache_data(show_spinner=False, max_entries=3)
def recover_image(data, shadows, noise):
    return recover_photo(read_image(data), shadows, noise)

with st.sidebar:
    st.markdown('<div class="brand">ASTERA</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Your photograph", type=["jpg", "jpeg", "png"], key="upload",
                               help="JPG or PNG, up to 20 MB. Processing fits the photo within 2,000 pixels.")
    use_demo = st.toggle("Try a sample", value=True, help="A synthetic night scene for trying the tools. Your upload replaces it.")
    st.markdown('<div class="section-label">Adjustments</div>', unsafe_allow_html=True)
    shadows = st.slider("Recover shadows", 0, 100, 25, step=5,
                        help="Lift dark detail without adding the same brightness to every pixel. Can also reveal noise.")
    noise = st.slider("Reduce color noise", 0, 15, 0,
                     help="Smooth colored grain. Higher values may soften faint lights. Start around 3–5.")
    brightness = st.slider("Brightness", -70, 90, 0, step=2,
                          help="Make the whole image lighter or darker. Too much can wash out the sky.")
    contrast = st.slider("Contrast", .7, 1.7, 1.0, step=.05,
                        help="Scale pixel intensity. Values above 1 deepen the difference between dark and bright areas.")
    with st.expander("Explore bright points"):
        st.caption("This tool measures bright regions; it does not improve exposure or identify stars.")
        threshold = st.slider("Detection threshold", 100, 250, 202, step=2,
                              help="Keep pixels brighter than this value after grayscale conversion and smoothing.")
        show_markers = st.toggle("Highlight detected light points", value=False)
        st.caption("Lower values include more light regions. Regions can merge or split, so counts may vary.")
    with st.expander("Photo stamp", expanded=True):
        stamp = st.toggle("Add date & location", value=True)
        observed_on = st.date_input("Photo date", value=date.today())
        location = st.text_input("Location", placeholder="e.g. Key Largo, Florida", max_chars=65)
    st.caption("Session only. No photo archive or account required.")

st.markdown('<div class="editor-bar"><span class="editor-name">Photo editor</span><span class="editor-mode">ASTERA / Night photography</span></div>', unsafe_allow_html=True)

if uploaded is None and not use_demo:
    st.info("Upload your photo in the sidebar, or turn on Try a sample to explore the studio.")
    st.stop()

try:
    if uploaded is not None:
        data = uploaded.getvalue()
        original = read_image(data)
        with st.spinner("Recovering photo detail…"):
            recovered = recover_image(data, shadows, noise)
        source_label = uploaded.name
    else:
        original = demo_photo()
        with st.spinner("Recovering photo detail…"):
            recovered = recover_photo(original, shadows, noise)
        source_label = "Sample image"
    edited = enhance(recovered, brightness, contrast)
    detection = detect_highlights(edited, threshold)
    count = len(detection.points)
    if stamp:
        final = annotate(edited, observed_on, location, count, detection.points, show_markers)
    else:
        # Keep marker drawing available even when the photo stamp is off.
        import cv2
        final = edited.copy()
        if show_markers:
            for x, y, radius in detection.points[:200]:
                cv2.circle(final, (x, y), radius, (125, 195, 230), 1, cv2.LINE_AA)
    st.caption(f"{source_label} · {original.shape[1]:,} × {original.shape[0]:,} px · PNG export")
    if uploaded is None:
        st.caption("Synthetic sample. Upload a photograph to edit your own image.")
    compare, sides = st.tabs(["Compare", "Side by side"])
    with compare:
        before = base64.b64encode(png_bytes(original)).decode()
        after = base64.b64encode(png_bytes(final)).decode()
        # The comparison control runs locally in this frame; it does not send photos elsewhere.
        height = min(650, max(340, round(1000 * original.shape[0] / original.shape[1]) + 95))
        components.html(f'''<!doctype html><html lang="en"><head><style>
        *{{box-sizing:border-box}}body{{margin:0;background:#202020;color:#ddd;font:13px system-ui}}
        .stage{{position:relative;width:100%;height:{height-75}px;overflow:hidden;border:1px solid #444;border-radius:0;background:#171717}}
        .stage img{{position:absolute;width:100%;height:100%;object-fit:contain}}
        #after{{clip-path:inset(0 0 0 50%)}}#line{{position:absolute;left:50%;top:0;height:100%;width:2px;background:#ddd;pointer-events:none}}
        .tag{{position:absolute;top:14px;padding:7px 10px;background:#222d;border-radius:2px;font-size:10px;letter-spacing:.15em}}
        .before{{left:14px}}.after{{right:14px}}label{{display:flex;align-items:center;gap:16px;margin-top:15px;color:#aaa}}input{{flex:1;accent-color:#aaa;cursor:ew-resize;min-width:80px}}
        </style></head><body><div class="stage">
        <img src="data:image/png;base64,{before}" alt="Original photograph">
        <img id="after" src="data:image/png;base64,{after}" alt="Processed photograph">
        <div id="line"></div><span class="tag before">ORIGINAL</span><span class="tag after">ASTERA</span>
        </div><label>Before<input aria-label="Before and after comparison" type="range" min="0" max="100" value="50" oninput="document.getElementById('after').style.clipPath='inset(0 0 0 '+this.value+'%)';document.getElementById('line').style.left=this.value+'%'">After</label></body></html>''', height=height)
        st.caption("Drag the comparison control to reveal the original or your edit. Both views use the same scale.")
    with sides:
        left, right = st.columns(2)
        left.image(original, caption="Original photograph", width="stretch")
        right.image(final, caption="Edited photograph", width="stretch")
    a, b, c = st.columns(3)
    a.metric("Bright-point candidates", str(count))
    luminance = .2126 * edited[:,:,0] + .7152 * edited[:,:,1] + .0722 * edited[:,:,2]
    b.metric("Average light", f"{np.mean(luminance) / 255:.0%}")
    c.metric("Near-white pixels", f"{np.mean(np.max(edited, axis=2) >= 250):.1%}")
    st.caption("Candidates may include noise, lamps or other objects—not confirmed stars. Near-white pixels can indicate lost highlight detail; these measurements exclude the stamp and markers.")
    if show_markers and count > 200:
        st.caption("Showing the first 200 candidate markers.")
    st.download_button("Download PNG", png_bytes(final),
                       file_name=f"Astera_{observed_on.isoformat()}.png", mime="image/png", type="primary", width="stretch")
    with st.expander("Light mask & transparent export"):
        st.caption("White regions passed the detection threshold. The transparent export keeps these light regions; it does not isolate confirmed stars.")
        st.image(detection.mask, caption="Global-threshold light mask", width="stretch")
        st.download_button("Download transparent light layer · PNG", png_bytes(transparent_light_layer(edited, detection.mask)),
                           file_name=f"Astera_LightLayer_{observed_on.isoformat()}.png", mime="image/png")
    with st.expander("A simple editing workflow"):
        st.markdown("1. **Reveal:** lift shadows until dark detail becomes visible.\n2. **Refine:** add a little noise reduction if grain becomes distracting. Faint lights may soften.\n3. **Balance:** adjust brightness and contrast while checking the original.\n4. **Keep:** add your stamp and download the result.")
        st.caption("Images fit within 2,000 pixels. Exports match the processed preview. Nothing is added to a photo archive.")
except ValueError as exc:
    st.error(str(exc))

st.markdown('<div class="foot">ASTERA · Your sky. Your story.</div>', unsafe_allow_html=True)
