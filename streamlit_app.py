import streamlit as st
from app.ingest import ingest_video
from app.search import answer

st.set_page_config(page_title="YapBack", page_icon="🎙️", layout="wide")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "videos" not in st.session_state:
    st.session_state.videos = {}
if "video_topics" not in st.session_state:
    st.session_state.video_topics = {}


def ask_question(question):
    selected = st.session_state.get("selected_video", "All videos")
    video_id = None
    if selected != "All videos":
        for vid, title in st.session_state.videos.items():
            if title == selected:
                video_id = vid
                break

    st.session_state.chat_history.append({"role": "user", "content": question})
    result = answer(question, video_id=video_id)
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": result["answer_text"],
        "sources": result["sources"],
    })


with st.sidebar:
    st.title("🎙️ YapBack")
    st.caption("Ask anything about any YouTube video")
    st.divider()

    st.subheader("Add a Video")
    url_input = st.text_input("YouTube URL", placeholder="https://youtube.com/watch?v=...")
    title_input = st.text_input("Video title (optional)", placeholder="e.g. Karpathy LLM Talk")

    if st.button("Ingest Video", type="primary", use_container_width=True):
        if not url_input.strip():
            st.warning("Please paste a YouTube URL.")
        else:
            with st.spinner("Fetching transcript & embedding into Endee..."):
                try:
                    result = ingest_video(url_input.strip(), title_input.strip())
                    st.session_state.videos[result["video_id"]] = result["video_title"]
                    st.session_state.selected_video = result["video_title"]
                    st.session_state.chat_history = []
                    topic = result.get("dominant_topic", "General")
                    dist = result.get("topic_distribution", {})
                    st.session_state.video_topics[result["video_id"]] = {"topic": topic, "distribution": dist}
                    st.success(
                        f"Indexed **{result['chunk_count']} chunks** from "
                        f"*{result['video_title']}*"
                    )
                    st.info(f"🏷️ Topic: **{topic}**")
                    if dist:
                        st.caption(f"Distribution: {dist}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed: {e}")

    st.divider()

    st.subheader("Search Within")
    video_options = ["All videos"] + list(st.session_state.videos.values())
    st.selectbox("Select video:", options=video_options, key="selected_video", label_visibility="collapsed")

    st.divider()

    st.subheader("Indexed Videos")
    if st.session_state.videos:
        for vid_id, vid_title in st.session_state.videos.items():
            st.image(f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg", width=320)
            st.markdown(f"**{vid_title}**  \n[▶ Watch on YouTube](https://youtube.com/watch?v={vid_id})")
            topic_info = st.session_state.video_topics.get(vid_id)
            if topic_info:
                st.markdown(f"🏷️ **{topic_info['topic']}**")
            st.caption(f"`{vid_id}`")
    else:
        st.info("No videos yet — add one above.")

    st.divider()

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()


st.header("Ask a Question")

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            with st.expander("📹 View Sources"):
                for src in msg["sources"]:
                    st.markdown(
                        f"**{src['video_title']}** @ `{src['timestamp_label']}`  \n"
                        f"{src['text'][:200]}...  \n"
                        f"[▶ Watch this moment]({src['yt_url']})"
                    )
                    st.divider()

if not st.session_state.chat_history:
    st.markdown("**Try one of these:**")
    cols = st.columns(3)
    starters = ["What is this video about?", "Summarize the key points", "What topics are covered?"]
    for col, q in zip(cols, starters):
        with col:
            if st.button(q, use_container_width=True):
                if st.session_state.videos:
                    with st.spinner("Thinking..."):
                        ask_question(q)
                    st.rerun()
                else:
                    st.warning("Ingest a video first!")

if prompt := st.chat_input("Ask anything about your videos..."):
    if not st.session_state.videos:
        st.warning("Please ingest at least one video first using the sidebar.")
    else:
        with st.spinner("Searching Endee & generating answer..."):
            try:
                ask_question(prompt)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
