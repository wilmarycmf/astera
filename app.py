"""Astera — minimalist night-sky observation image generator.

No login, no cloud database, no permanent uploaded-photo storage.
"""
from datetime import date

import streamlit as st

from core import annotate, detect_highlights, enhance, load_photo, png_bytes, transparent_light_layer

st.set_page_config(page_title="Astera | Your sky, your story", page_icon="🌌", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'DM Sans', sans-serif;}
.stApp {background:radial-gradient(ellipse at 82% 0%,#192541 0%,#0b1120 35%,#080c16 78%);color:#e9edf7;}
.block-container {max-width:1190px;padding-top:2.1rem;padding-bottom:3rem;}
h1,h2,h3 {font-family:'Manrope',sans-serif!important;letter-spacing:-.025em;}
[data-testid="stFileUploader"] {border-radius:12px;}
[data-testid="stFileUploaderDropzone"] {background:#111b2c;border:1px dashed #5d6c87;border-radius:12px;}
[data-testid="stFileUploaderDropzone"] * {color:#e9edf7!important;}
[data-testid="stImage"] img {border-radius:12px;}
.stButton button, [data-testid="stDownloadButton"] button {border-radius:9px!important;min-height:2.8rem;}
[data-testid="stDownloadButton"] button {background:#dbdedf!important;border:0!important;color:#101729!important;font-weight:700;}
[data-testid="stSlider"] [role="slider"] {background:#d7c7a1;}
[data-testid="stWidgetLabel"] p {font-weight:600;color:#cdd5e6;}
[data-testid="stTextInput"] input, [data-testid="stDateInput"] input {background:#121c30;color:#e9edf7;}
hr {border-color:#2a3449;}
.astera-eyebrow {color:#bbc3d4;font-size:.68rem;font-weight:700;letter-spacing:.26em;margin-bottom:.8rem;}
.astera-title {font-size:clamp(3.5rem,8vw,6rem);font-weight:700;letter-spacing:.16em;line-height:1;color:#f4f2ee;margin:0 0 .8rem 0;}
.astera-tagline {color:#bbc5d7;font-size:1.06rem;letter-spacing:.03em;}
.astera-rule {height:1px;background:linear-gradient(90deg,#b4a175,transparent);margin:1.7rem 0 2rem;}
.astera-mini {color:#cbb98e;font-size:.67rem;letter-spacing:.18em;font-weight:700;margin:0 0 .55rem;}
.astera-note {color:#aab5c9;font-size:.87rem;line-height:1.6;}
.astera-footer {font-size:.79rem;color:#9ca9c3;margin-top:2.2rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="astera-eyebrow">✦ &nbsp; NIGHT SKY IMAGE GENERATOR</div>', unsafe_allow_html=True)
st.markdown('<div class="astera-title">ASTERA</div>', unsafe_allow_html=True)
st.markdown('<div class="astera-tagline">Your sky. Your story. A moment worth keeping.</div>', unsafe_allow_html=True)
st.markdown('<div class="astera-rule"></div>', unsafe_allow_html=True)

control, previews = st.columns([0.92, 1.75], gap="large")
with control:
    st.markdown('<div class="astera-mini">01 / YOUR PHOTOGRAPH</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload a night-sky photo", type=["png","jpg","jpeg"],
                                help="JPG or PNG, up to 20 MB. Taken with your phone is fine.")
    st.markdown('<div class="astera-mini" style="margin-top:1.5rem">02 / REVEAL THE SKY</div>', unsafe_allow_html=True)
    brightness = st.slider("Brightness", -70, 90, 18, step=2)
    contrast = st.slider("Contrast", 0.7, 1.7, 1.1, step=0.05)
    threshold = st.slider("Detection threshold", 100, 250, 202, step=2,
                          help="Lower threshold = more light points; higher = fewer points.")
    st.caption("Lower threshold reveals more bright regions. Counts can change as regions merge.")
    show_markers = st.toggle("Highlight detected light points", value=False,
                             help="Optional circles only — no made-up constellations.")
    st.markdown('<div class="astera-mini" style="margin-top:1.6rem">03 / KEEP THE MOMENT</div>', unsafe_allow_html=True)
    observed_on = st.date_input("Photo date", value=date.today(), max_value=date.today())
    location = st.text_input("Location", value="", placeholder="e.g. Key Largo, Florida", max_chars=65)
    st.markdown('<p class="astera-note">Your photo is processed for this session. Astera does not create an online account or save a photo archive.</p>', unsafe_allow_html=True)

with previews:
    if uploaded is None:
        st.markdown('<div class="astera-mini">YOUR NIGHT BEGINS HERE</div>', unsafe_allow_html=True)
        st.markdown("### Upload a photo to begin ✦")
        st.markdown("Astera gently enhances the sky, finds small bright regions, and adds a subtle date and location stamp. Then you download the finished image.")
        st.info("Choose a night-sky JPG or PNG on the left. You can use your phone photo.", icon="🌌")
        st.markdown('<p class="astera-note">OpenCV concepts used: image arithmetic · global thresholding · drawing / annotation · alpha-channel transparency.</p>', unsafe_allow_html=True)
    else:
        try:
            original = load_photo(uploaded.getvalue())
            st.caption("Images are fitted within 2,000 px for responsive processing. Downloads match the processed preview.")
            edited = enhance(original, brightness, contrast)
            detection = detect_highlights(edited, threshold)
            final = annotate(edited, observed_on, location,
                             len(detection.points), detection.points, mark_points=show_markers)
            st.markdown('<div class="astera-mini">LIVE PREVIEW / BEFORE & AFTER</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2, gap="medium")
            with c1:
                st.image(original, caption="Original photograph", width="stretch")
            with c2:
                st.image(final, caption="Astera • Your finished photograph", width="stretch")
            if show_markers and len(detection.points) > 200:
                st.caption("Showing markers for the first 200 candidates to keep your photo clear.")
            st.metric("Bright-point candidates", f"{len(detection.points)}")
            st.caption("Estimated from light regions in your image. They may include stars, noise, lamps or other objects; this is not astronomical identification.")
            st.download_button("↓ Download your Astera image · PNG", png_bytes(final),
                               file_name=f"Astera_{observed_on.isoformat()}.png",
                               mime="image/png", type="primary", width="stretch")
            with st.expander("Explore the image-processing mask (optional)"):
                st.image(detection.mask, caption="Global-threshold light mask", clamp=True, width="stretch")
                layer = transparent_light_layer(edited, detection.mask)
                st.download_button("Download transparent light layer · PNG", png_bytes(layer),
                                   file_name=f"Astera_LightLayer_{observed_on.isoformat()}.png",
                                   mime="image/png", width="stretch")
        except ValueError as exc:
            st.error(str(exc))

st.markdown('<div class="astera-footer">ASTERA  /  A LITTLE PIECE OF THE NIGHT.  ·  Made with Python, OpenCV & Streamlit.</div>', unsafe_allow_html=True)
