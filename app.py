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

PRESETS = {
    "Natural": {"shadows": 25, "noise": 0, "brightness": 0, "contrast": 1.0},
    "Lift shadows": {"shadows": 55, "noise": 3, "brightness": 4, "contrast": 1.05},
    "Low noise": {"shadows": 15, "noise": 7, "brightness": 0, "contrast": 1.0},
}


def apply_preset():
    for key, value in PRESETS[st.session_state["preset"]].items():
        st.session_state[key] = value


def reset_adjustments():
    st.session_state["preset"] = "Natural"
    apply_preset()


for key, value in PRESETS["Natural"].items():
    if key not in st.session_state:
        st.session_state[key] = value

with st.sidebar:
    st.markdown('<div class="brand">ASTERA</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Your photograph", type=["jpg", "jpeg", "png"], key="upload",
                               help="JPG or PNG, up to 20 MB. Processing fits the photo within 2,000 pixels.")
    use_demo = st.toggle("Try a sample", value=True, help="A synthetic night scene for trying the tools. Your upload replaces it.")
    st.markdown('<div class="section-label">Edit your photo</div>', unsafe_allow_html=True)
    st.selectbox("Choose a starting point", list(PRESETS), key="preset", on_change=apply_preset,
                 help="Choose a look, then use Fine-tune if you want to adjust it.")
    descriptions = {
        "Natural": "A gentle lift for dark detail.",
        "Lift shadows": "Brighter dark areas, with light noise reduction.",
        "Low noise": "Smooths colored grain. Small lights may soften.",
    }
    st.caption(descriptions[st.session_state["preset"]])
    with st.expander("Fine-tune"):
        st.caption("Optional. Changes appear in the preview.")
        shadows = st.slider("Recover shadows", 0, 100, step=5, key="shadows",
                            help="Reveal detail in dark areas. Stronger settings can also reveal grain.")
        noise = st.slider("Reduce color noise", 0, 15, key="noise",
                         help="Smooth colored grain. Stronger settings can soften small lights.")
        brightness = st.slider("Brightness", -70, 90, step=2, key="brightness",
                              help="Make the whole photo lighter or darker.")
        contrast = st.slider("Contrast", .7, 1.7, step=.05, key="contrast",
                            help="Adjust the difference between light and dark pixels.")
    st.button("Reset adjustments", on_click=reset_adjustments, width="stretch",
              help="Return the four photo adjustments to Natural. Your photo, stamp and detection settings stay as they are.")
    with st.expander("Explore bright points"):
        st.caption("This tool measures bright regions; it does not improve exposure or identify stars.")
        threshold = st.slider("Detection threshold", 100, 250, 202, step=2,
                              help="Keep pixels brighter than this value after grayscale conversion and smoothing.")
        show_markers = st.toggle("Highlight detected light points", value=False)
        st.caption("Lower values include more light regions. Regions can merge or split, so counts may vary.")
    with st.expander("Date & location"):
        stamp = st.toggle("Add date & location", value=True)
        observed_on = st.date_input("Photo date", value=date.today())
        location = st.text_input("Location", placeholder="e.g. Key Largo, Florida", max_chars=65)
    st.caption("Upload → choose a starting point → compare → download.")

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
    info, download = st.columns([3, 1], vertical_alignment="center")
    info.caption(f"{source_label} · {original.shape[1]:,} × {original.shape[0]:,} px")
    with download:
        st.download_button("Download PNG", png_bytes(final),
                           file_name=f"Astera_{observed_on.isoformat()}.png", mime="image/png", type="primary", width="stretch")
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
    st.caption(f"Bright-point candidates: {count:,}. These may include noise or other lights, not confirmed stars.")
    with st.expander("Image measurements"):
        a, b = st.columns(2)
        luminance = .2126 * edited[:,:,0] + .7152 * edited[:,:,1] + .0722 * edited[:,:,2]
        a.metric("Average light", f"{np.mean(luminance) / 255:.0%}")
        b.metric("Near-white pixels", f"{np.mean(np.max(edited, axis=2) >= 250):.1%}")
        st.caption("Near-white pixels can indicate lost highlight detail. Measurements exclude the stamp and markers.")
    if show_markers and count > 200:
        st.caption("Showing the first 200 candidate markers.")
    with st.expander("Light mask & transparent export"):
        st.caption("White regions passed the detection threshold. The transparent export keeps these light regions; it does not isolate confirmed stars.")
        st.image(detection.mask, caption="Global-threshold light mask", width="stretch")
        st.download_button("Download transparent light layer · PNG", png_bytes(transparent_light_layer(edited, detection.mask)),
                           file_name=f"Astera_LightLayer_{observed_on.isoformat()}.png", mime="image/png")
    with st.expander("A simple editing workflow"):
        st.markdown("1. **Upload** your photograph, or try the sample.\n2. **Choose a starting point.** Fine-tune is optional.\n3. **Compare** the original and edited photo using the slider.\n4. **Download PNG.** Add a date and place first if you want a stamp.")
        st.caption("Images fit within 2,000 pixels. Exports match the processed preview. Nothing is added to a photo archive.")
except ValueError as exc:
    st.error(str(exc))

st.markdown('<div class="foot">ASTERA · Your sky. Your story.</div>', unsafe_allow_html=True)
