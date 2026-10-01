"""
Retrieval & grounding evaluation for the RAG system.

Measures the two properties the project claims:
  * context relevance      — does retrieval surface the passage that actually
                             holds the answer?  (hit-rate @k over a gold labelling)
  * grounded-response rate — for answerable questions, is the answer supported by
                             the retrieved context; for out-of-scope questions,
                             does the system correctly ABSTAIN instead of guessing?

By default it runs fully offline on the local MiniLM fallback embeddings (no API
key needed), scoring the answer side with a retrieval-grounding proxy: an answer
is "grounded" iff the gold fact is present in the retrieved context, and an
out-of-scope question is handled correctly iff retrieval finds nothing strongly
relevant (so the model will abstain).

Pass --generate with a valid GEMINI_API_KEY to instead score faithfulness on the
model's actual answers (does it state the fact, stay close to the context, and
abstain when it should).

Usage:
    python -m eval.run_eval [--k 4] [--threshold 0.7] [--abstain-threshold 0.35] [--generate]

Exits non-zero when context relevance or grounded-response rate is below the
threshold, so it can gate CI.
"""
import argparse
import sys

from dotenv import load_dotenv

from eval.corpus import CORPUS
from eval.dataset import GOLD
from eval.metrics import (
    InMemoryRetriever,
    context_scores,
    is_abstention,
    substring_in_contexts,
    answer_faithfulness,
)


def run(k=4, threshold=0.7, abstain_threshold=0.35, generate=False):
    from services.embedding_fallback import FallbackEmbeddings

    embeddings = FallbackEmbeddings()
    retriever = InMemoryRetriever(embeddings, CORPUS)

    gen = None
    if generate:
        try:
            gen = _make_generator()
        except Exception as e:
            print(f"[warn] --generate unavailable ({e}); falling back to retrieval-grounding proxy")

    rows = []
    ctx_hits = []           # context relevance over answerable questions
    grounded_flags = []     # grounded-response rate over all questions
    faithfulness_vals = []  # only populated when generating real answers

    for item in GOLD:
        retrieved = retriever.retrieve(item["question"], k=k)
        contexts = [r[1] for r in retrieved]
        cs = context_scores(retrieved, item["relevant_ids"])

        if item["answerable"]:
            ctx_hits.append(cs["hit"])

        answer = gen(item["question"], contexts) if gen is not None else None

        if item["answerable"]:
            if answer is not None:
                faith = answer_faithfulness(answer, contexts, embeddings)
                faithfulness_vals.append(faith)
                grounded = (
                    not is_abstention(answer)
                    and substring_in_contexts(item["answer_substring"], [answer])
                    and faith >= 0.4
                )
            else:
                # proxy: a grounded answer is producible iff the gold fact is retrieved
                grounded = substring_in_contexts(item["answer_substring"], contexts)
        else:
            if answer is not None:
                grounded = is_abstention(answer)  # correct behaviour = abstain
            else:
                grounded = cs["top_score"] < abstain_threshold  # nothing strong => will abstain

        grounded_flags.append(1.0 if grounded else 0.0)
        rows.append((item, cs, grounded, answer))

    context_relevance = sum(ctx_hits) / len(ctx_hits) if ctx_hits else 0.0
    grounded_rate = sum(grounded_flags) / len(grounded_flags) if grounded_flags else 0.0
    mean_faith = (sum(faithfulness_vals) / len(faithfulness_vals)) if faithfulness_vals else None

    _print_report(rows, k, context_relevance, grounded_rate, mean_faith)
    ok = context_relevance >= threshold and grounded_rate >= threshold
    return ok, context_relevance, grounded_rate


def _print_report(rows, k, context_relevance, grounded_rate, mean_faith):
    print(f"\nRAG retrieval & grounding eval   (k={k}, {len(rows)} questions)")
    print("-" * 78)
    for item, cs, grounded, _answer in rows:
        kind = "ANSW" if item["answerable"] else "OOS "
        mark = "PASS" if grounded else "FAIL"
        print(f"  [{mark}] {kind}  hit@k={cs['hit']:.0f}  prec={cs['precision']:.2f}  "
              f"top={cs['top_score']:.2f}   {item['question'][:42]}")
    print("-" * 78)
    print(f"  context relevance (answerable hit@k) : {context_relevance:.1%}")
    print(f"  grounded-response rate               : {grounded_rate:.1%}")
    if mean_faith is not None:
        print(f"  mean answer faithfulness (generated) : {mean_faith:.1%}")
    print()


def _make_generator():
    """Return f(question, contexts) -> answer using Gemini + the RAG prompt.
    Raises if no usable key so the caller can fall back to the proxy."""
    import os
    from langchain_google_genai import ChatGoogleGenerativeAI
    from agents.prompt_templates import RAG_PROMPT_TEMPLATE
    from agents.rag_agent import CHAT_MODEL

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    llm = ChatGoogleGenerativeAI(  # type: ignore[call-arg]
        model=CHAT_MODEL, temperature=0.0, google_api_key=key
    )

    def _gen(question, contexts):
        prompt = RAG_PROMPT_TEMPLATE.format(context="\n\n".join(contexts), question=question)
        return llm.invoke(prompt).content

    return _gen


def main():
    load_dotenv()
    ap = argparse.ArgumentParser(description="RAG retrieval & grounding eval")
    ap.add_argument("--k", type=int, default=4)
    ap.add_argument("--threshold", type=float, default=0.7)
    ap.add_argument("--abstain-threshold", type=float, default=0.35)
    ap.add_argument("--generate", action="store_true",
                    help="score faithfulness on real Gemini answers (needs a valid GEMINI_API_KEY)")
    args = ap.parse_args()

    ok, cr, gr = run(
        k=args.k, threshold=args.threshold,
        abstain_threshold=args.abstain_threshold, generate=args.generate,
    )
    if not ok:
        print(f"FAIL: below threshold {args.threshold:.0%}  (context={cr:.0%}, grounded={gr:.0%})")
        sys.exit(1)
    print(f"PASS: context={cr:.0%}, grounded={gr:.0%}  (threshold {args.threshold:.0%})")


if __name__ == "__main__":
    main()
