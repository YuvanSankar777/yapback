"""
Retrieval evaluation for YapBack.

Runs 10 test queries against a seeded video, measures hit accuracy,
keyword recall, and similarity scores. Also compares different top_k
values to find the best retrieval setting.
"""

from app.search import search
from app.ingest import ingest_video, fetch_title

DEMO_VIDEO = "x7X9w_GIm1s"

TEST_CASES = [
    {"query": "What is Python used for?",                       "expected_video": DEMO_VIDEO, "expected_keywords": ["python", "language", "popular", "learn", "projects"]},
    {"query": "What makes Python popular?",                     "expected_video": DEMO_VIDEO, "expected_keywords": ["popular", "easy", "learn", "practical", "world"]},
    {"query": "What is the Zen of Python?",                     "expected_video": DEMO_VIDEO, "expected_keywords": ["zen", "beautiful", "ugly", "readability"]},
    {"query": "How do you declare a variable in Python?",       "expected_video": DEMO_VIDEO, "expected_keywords": ["variable", "type", "dynamic"]},
    {"query": "Does Python support object oriented programming?","expected_video": DEMO_VIDEO, "expected_keywords": ["object", "class", "abstraction"]},
    {"query": "What are Python data structures?",               "expected_video": DEMO_VIDEO, "expected_keywords": ["list", "dictionary"]},
    {"query": "Who created Python?",                            "expected_video": DEMO_VIDEO, "expected_keywords": ["guido", "1991"]},
    {"query": "What frameworks does Python have?",              "expected_video": DEMO_VIDEO, "expected_keywords": ["django", "flask", "framework"]},
    {"query": "Is Python used for machine learning?",           "expected_video": DEMO_VIDEO, "expected_keywords": ["machine", "learning", "tensorflow"]},
    {"query": "How does Python handle functions?",              "expected_video": DEMO_VIDEO, "expected_keywords": ["function", "def", "indentation"]},
]


def evaluate_at_k(test_cases, top_k):
    total_hits = 0
    total_kw_recall = 0.0
    total_sim = 0.0
    per_query = []

    for tc in test_cases:
        hits = search(tc["query"], top_k=top_k)

        retrieved_vids = [h.get("video_id", "") for h in hits]
        hit = tc["expected_video"] in retrieved_vids
        total_hits += int(hit)

        all_text = " ".join(h.get("text", "") for h in hits).lower()
        kw_found = sum(1 for kw in tc["expected_keywords"] if kw.lower() in all_text)
        kw_recall = kw_found / len(tc["expected_keywords"])
        total_kw_recall += kw_recall

        top_score = hits[0].get("score", 0) if hits else 0
        total_sim += top_score

        per_query.append({
            "query": tc["query"], "hit": hit,
            "kw_recall": kw_recall, "kw_found": kw_found,
            "kw_total": len(tc["expected_keywords"]), "top_score": top_score,
        })

    n = len(test_cases)
    return {
        "top_k": top_k,
        "hit_accuracy": total_hits / n,
        "avg_kw_recall": total_kw_recall / n,
        "avg_similarity": total_sim / n,
        "per_query": per_query,
    }


def run_evaluation():
    print(f"Seeding demo video: {DEMO_VIDEO}")
    title = fetch_title(DEMO_VIDEO)
    try:
        res = ingest_video(DEMO_VIDEO, title)
        print(f"  {res['chunk_count']} chunks indexed for '{title}'")
    except Exception as e:
        print(f"  Skipped (already indexed or error): {e}")
    print()

    # detailed results at k=5
    print("=" * 90)
    print("RETRIEVAL EVALUATION (top_k=5)")
    print("=" * 90)

    result = evaluate_at_k(TEST_CASES, top_k=5)

    print(f"{'Query':<45} | {'Hit@5':>5} | {'Keyword Recall':>15} | {'Score':>6}")
    print("-" * 90)
    for r in result["per_query"]:
        hit_str = "  YES" if r["hit"] else "   NO"
        kw_str = f"{r['kw_found']}/{r['kw_total']} ({r['kw_recall']:.0%})"
        score_str = f"{r['top_score']:.4f}" if r["top_score"] else "  N/A"
        print(f"{r['query']:<45} | {hit_str} | {kw_str:>15} | {score_str:>6}")
    print("-" * 90)
    print(f"{'OVERALL':<45} | {result['hit_accuracy']:>4.0%}  | {result['avg_kw_recall']:>14.0%}  | {result['avg_similarity']:>6.4f}")
    print("=" * 90)
    print()

    # compare different k values
    print("=" * 90)
    print("TOP_K COMPARISON")
    print("=" * 90)
    print()

    k_values = [1, 3, 5, 10]
    comparison = []
    for k in k_values:
        r = evaluate_at_k(TEST_CASES, top_k=k)
        comparison.append(r)
        print(f"  K={k:<3} | Hit: {r['hit_accuracy']:.0%}  | Recall: {r['avg_kw_recall']:.0%}  | Similarity: {r['avg_similarity']:.4f}")

    print()
    best = max(comparison, key=lambda x: x["hit_accuracy"] + x["avg_kw_recall"])
    print(f"  Selected: K={best['top_k']} (best accuracy + recall trade-off)")
    print()

    # summary
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)
    print(f"  Embedding:  gemini-embedding-001 (3072-dim)")
    print(f"  Vector DB:  Endee (cosine, int8, HNSW M=16)")
    print(f"  Chunking:   sentence-aware, ~150 words, 5-entry overlap")
    print(f"  Best K:     {best['top_k']}")
    print(f"  Hit@{best['top_k']}:      {best['hit_accuracy']:.0%}")
    print(f"  Recall:     {best['avg_kw_recall']:.0%}")
    print(f"  Similarity: {best['avg_similarity']:.4f}")
    print()
    verdict = "GOOD" if best["hit_accuracy"] >= 0.8 else "NEEDS IMPROVEMENT"
    print(f"  Verdict: {verdict}")


if __name__ == "__main__":
    run_evaluation()
