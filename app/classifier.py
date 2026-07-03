import os
import pickle
import warnings
from sklearn.exceptions import InconsistentVersionWarning
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "topic_model.pkl")

LABELS = ["Tech", "Science", "Business", "Education", "Entertainment", "General"]

TRAINING_DATA = [
    ("python programming language code function variable loop class object", "Tech"),
    ("javascript react node api web frontend backend database server deploy", "Tech"),
    ("machine learning neural network deep learning training model accuracy", "Tech"),
    ("algorithm data structure array linked list tree graph sorting search", "Tech"),
    ("docker container kubernetes cloud devops infrastructure deployment ci", "Tech"),
    ("linux terminal command shell bash git version control repository", "Tech"),
    ("software engineering system design architecture microservices scaling", "Tech"),
    ("cybersecurity encryption hacking vulnerability firewall network attack", "Tech"),

    ("biology cell dna gene protein evolution organism species mutation", "Science"),
    ("physics quantum mechanics gravity relativity particle wave energy atom", "Science"),
    ("chemistry molecule reaction element compound bond organic acid base", "Science"),
    ("mathematics calculus algebra equation theorem proof integral derivative", "Science"),
    ("space universe star planet galaxy black hole telescope nasa astronomy", "Science"),
    ("climate change environment carbon emission global warming temperature", "Science"),
    ("neuroscience brain cognition memory neuron synapse perception stimulus", "Science"),

    ("startup company investor funding venture capital valuation revenue profit", "Business"),
    ("marketing sales growth strategy customer acquisition brand awareness", "Business"),
    ("stock market trading investment portfolio finance economy inflation", "Business"),
    ("management leadership team hiring culture organization productivity", "Business"),
    ("cryptocurrency blockchain bitcoin ethereum token decentralized exchange", "Business"),
    ("product launch market fit pricing competition analysis customer feedback", "Business"),

    ("student learning study course exam grade university college school", "Education"),
    ("tutorial beginner guide introduction basics fundamentals concept", "Education"),
    ("lecture class teacher professor lesson explain understand knowledge", "Education"),
    ("math problem solving practice exercise homework assignment test", "Education"),
    ("history civilization war empire kingdom ancient medieval modern era", "Education"),
    ("language grammar vocabulary reading writing speaking communication", "Education"),

    ("music song artist album concert band genre rhythm melody beat", "Entertainment"),
    ("movie film actor director scene plot story character drama comedy", "Entertainment"),
    ("game gaming esports streaming player level score challenge quest", "Entertainment"),
    ("sports football basketball cricket tennis athlete team match score", "Entertainment"),
    ("comedy funny joke laugh humor stand up sketch meme viral prank", "Entertainment"),

    ("life experience travel food cooking recipe culture tradition people", "General"),
    ("health fitness exercise diet nutrition wellness mental health yoga", "General"),
    ("news current events politics government policy society discussion", "General"),
    ("motivation inspiration success goal dream mindset habit discipline", "General"),
]

texts = [t for t, _ in TRAINING_DATA]
labels = [l for _, l in TRAINING_DATA]


def _build_model():
    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("nb", MultinomialNB(alpha=0.1)),
    ])
    pipe.fit(texts, labels)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(pipe, f)
    return pipe


def _load_model():
    if os.path.exists(MODEL_PATH):
        try:
            # Treat a scikit-learn version mismatch as fatal: an incompatible
            # pickle can silently produce wrong predictions, so rebuild instead.
            with warnings.catch_warnings():
                warnings.simplefilter("error", InconsistentVersionWarning)
                with open(MODEL_PATH, "rb") as f:
                    return pickle.load(f)
        except Exception:
            pass  # Missing/corrupt/stale cache — rebuild from TRAINING_DATA below.
    return _build_model()


_model = None

def classify_chunk(text):
    global _model
    if _model is None:
        _model = _load_model()
    prediction = _model.predict([text])[0]
    probas = _model.predict_proba([text])[0]
    confidence = float(max(probas))
    return {"topic": str(prediction), "confidence": round(confidence, 3)}


def classify_video(chunks):
    """Classify each chunk and return the dominant topic for the whole video."""
    topic_counts = {}
    chunk_topics = []
    for chunk in chunks:
        result = classify_chunk(chunk["text"])
        chunk_topics.append(result)
        t = result["topic"]
        topic_counts[t] = topic_counts.get(t, 0) + 1

    dominant = max(topic_counts, key=topic_counts.get)
    return {
        "dominant_topic": dominant,
        "topic_distribution": topic_counts,
        "per_chunk": chunk_topics,
    }
