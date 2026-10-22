# Agentic Research and Knowledge Investigation System

An agentic retrieval-augmented generation (RAG) system for answering generative AI security questions using an OWASP knowledge base. The system plans what information is needed, retrieves supporting passages, checks whether the evidence is sufficient, and searches again when information is missing.

## Main Notebook

[`Fugitt_Shah_AgenticAI_Increment1.ipynb`](Fugitt_Shah_AgenticAI_Increment1.ipynb) contains the implementation, demonstrations, and evaluation, committed with the outputs of the October 21, 2026 run (Project Increment 1). The earlier `agentic_retrieval.ipynb` is superseded by this file.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Shreya9297/Agentic-Research-and-Knowledge-Investigation-System/blob/main/Fugitt_Shah_AgenticAI_Increment1.ipynb)

## Features

- Semantic search using Sentence Transformers and cosine similarity.
- A single-search RAG baseline for comparison.
- Question planning and evidence sufficiency analysis using Gemini.
- A LangGraph workflow with iterative retrieval and conditional routing.
- Evidence metadata, including chunk IDs, risk categories, section titles, and source pages.
- Grounded answers with chunk citations and Python-side citation validation.
- Input validation and reporting of unsupported questions or missing evidence.
- Tests for multi-topic questions, incorrect assumptions, stopping behavior, and prompt injection through retrieved text.
- A data-filtration audit of the OWASP PDF: pages kept and excluded, footer removal, character and chunk-size counts.
- Seeded random topic selection and Gemini-generated factoid and narrative test questions with source chunk IDs as ground truth.
- A Hugging Face `google/flan-t5-small` generator run as a comparison against Gemini on the generated questions.

## System Architecture

The implementation separates data preparation, semantic retrieval, model reasoning, and workflow control. Gemini plans searches, evaluates evidence, and writes answers. Python and LangGraph manage state, retrieval, routing, citation filtering, and stopping conditions.

```mermaid
flowchart TD
    PDF[OWASP source PDF] --> Extract[Extract risk documents]
    Extract --> Chunk[Clean and chunk text]
    Chunk --> Metadata[Preserve source metadata]
    Metadata --> Embed[Sentence Transformer embeddings]
    Embed --> Search[Cosine similarity search]

    Question[User question] --> Observe[Observe: validate input]
    Observe -->|Invalid| End[End]
    Observe -->|Valid| Plan[Plan: identify information needs]
    Plan --> Query[Query: select or refine search]
    Query --> Retrieve[Retrieve: collect unique evidence]
    Search --> Retrieve
    Retrieve --> Analyze[Analyze: check evidence coverage]
    Analyze -->|Missing evidence and rounds remain| Query
    Analyze -->|Stopping condition reached| Answer[Generate grounded answer]
    Answer --> Citations[Filter citations against evidence IDs]
    Citations --> Result[Answer, sources, and execution trace]
```

### Components

| Component | Responsibility | Implementation |
| --- | --- | --- |
| Input validation | Accept questions of 10–500 characters. | Pydantic `UserQuestion` model and `observe` node. |
| Question planner | Request separate information needs and search queries, including assumption checks when needed. | `plan_question()` and `plan` node. |
| Query selection | Select the next query using the plan or evidence analysis. | `query` node. |
| Semantic retrieval | Embed the query and rank chunks by cosine similarity. | `retrieve_chunks()`. |
| Evidence accumulation | Add newly retrieved chunks without duplicating chunk IDs. | `retrieve` node. |
| Evidence analysis | Assess each information need and propose a refined query for missing evidence. | `analyze_evidence()` and `analyze` node. |
| Workflow controller | Route to another search or the answer stage. | LangGraph `StateGraph` and conditional edges. |
| Answer generation | Produce an evidence-based response and report unsupported parts. | `generate_answer()` and `answer` node. |
| Citation filtering | Remove source IDs absent from the supplied evidence. | Python-side filtering in `generate_answer()`. |
| Run inspection | Display evidence, coverage decisions, answers, and traces. | `run_agent()` and `show_run()`. |
| Question generation | Select topics at random with a fixed seed and write factoid and narrative questions from sampled chunks. | `pick_chunk()` and `write_questions()` in Section 14. |
| Hugging Face generator | Answer the same questions with FLAN-T5-small on a single search for comparison. | `generator()` and `flan_answer()` in Section 15. |

### Shared Agent State

The graph carries the question, planned information needs, query history, current query, accumulated evidence, number of new chunks, per-need coverage, missing needs, retrieval round count, stop reason, answer, and execution trace.

Keeping these values in state allows each search to build on earlier evidence and makes routing decisions visible for inspection.

### Stopping Conditions

The analysis node checks these conditions in order:

1. **Evidence sufficient:** the analyzer marks all returned need statuses as covered.
2. **No new evidence:** the latest retrieval adds no new chunk IDs.
3. **Maximum rounds reached:** the run reaches `MAX_ROUNDS`, configured as `3`.

If none applies, the workflow searches again. Invalid input terminates at validation, before any search. When the workflow stops with missing evidence, the answer writer receives a note identifying the uncovered information.

### Answer Structure

The model is asked to return these fields as structured JSON:

| Field | Meaning |
| --- | --- |
| `answer` | The response based on the supplied evidence. |
| `sources` | Supporting chunk IDs, filtered against the evidence IDs. |
| `insufficient_evidence` | Whether the available evidence does not fully answer the question. |
| `unsupported_parts` | Information that could not be supported. |

## Configuration

| Setting | Notebook value | Purpose |
| --- | --- | --- |
| `TOP_K` | `4` | Chunks returned per retrieval round. |
| `MAX_ROUNDS` | `3` | Maximum retrieval rounds per agent run. |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | Produces 384-dimensional embeddings. |
| `MODEL` | `gemini-3.8-flash` | Model identifier configured for planning, analysis, and answers; availability must be checked for the API account. |
| `REQUEST_PAUSE_SECONDS` | `1.5` | Pause after model calls; does not guarantee compliance with account quotas. |
| `RANDOM_SEED` | `42` | Seed for selecting the topics of the generated test questions. |
| `GENERATION_MODEL` | `google/flan-t5-small` | Hugging Face generator used only for the comparison in Sections 15–16. |
| `FLAN_TOP_K` | `2` | Chunks given to FLAN-T5 (its input is limited to 512 tokens). |
| Question length | `10–500` characters | Input validation bounds. |

## Knowledge Base and Data Preparation

The notebook identifies its knowledge source as **OWASP Top 10 for LLM Applications 2026 (v1.0)** and is designed around ten risk documents and 125 chunks. Actual counts are printed when the data loads.

The notebook uses these repository resources:

| Path | Purpose |
| --- | --- |
| `src/01_extract_owasp.py` | Extract risk sections from the source PDF. |
| `src/02_clean_and_chunk.py` | Clean the extracted text and create overlapping chunks. |
| `src/03_create_embeddings.py` | Separate embedding preparation script; the notebook creates its own embeddings after cleaning the text. |
| `data/chunks/owasp_chunks.json` | Chunk records loaded by the notebook. |

The extraction scripts and their required source PDF must remain available in the repository. The notebook preserves source metadata and removes page markers from the text before embedding it.

### Filtering

Of the PDF's 122 pages, `01_extract_owasp.py` keeps the 48 pages of the ten risk entries (pages 10–57) and excludes the front matter (1–9), the Appendix A framework-mapping tables (58–105), the Appendix B architecture figure (106–107), the reference list (108–119), and the acknowledgements (120–122). `02_clean_and_chunk.py` removes the repeated `genai.owasp.org` footer and normalizes whitespace; no words of the risk entries are removed. Notebook Section 2A measures each step on the actual files. At retrieval time the only filters are top-k selection and de-duplication of chunk IDs; no similarity threshold is applied, and Section 14 prints the top-1 similarity of every test question to show why.

## Technologies

- **Python** — implementation and evaluation.
- **Pandas and NumPy** — evidence tables and numerical processing.
- **PyMuPDF** — PDF extraction through the data preparation script.
- **Sentence Transformers** — `sentence-transformers/all-MiniLM-L6-v2` embeddings.
- **scikit-learn** — cosine similarity retrieval.
- **Google GenAI SDK** — Gemini requests and structured responses.
- **Pydantic** — input validation.
- **LangGraph** — agent state, routing, and retrieval loop.
- **Transformers and SentencePiece** — the FLAN-T5-small generator used in the comparison.
- **Graphviz** — image of the compiled graph, drawn from its edges.
- **Matplotlib** — evaluation charts.

## Run in Google Colab

The notebook is configured for Google Colab and uses `/content/` paths.

1. Open the notebook with the **Open in Colab** badge above, or in Colab select **Open notebook → GitHub**, paste this repository URL, and choose `Fugitt_Shah_AgenticAI_Increment1.ipynb`. A CPU runtime is sufficient.
2. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/).
3. In Colab's **Secrets** panel, add `GEMINI_API_KEY` and enable notebook access. If a secret is unavailable, the notebook prompts for the key using hidden input.
4. Select **Runtime → Run all** and provide the key if prompted. A full run makes roughly 120 Gemini requests and downloads about 400 MB of models; expect about 10 minutes.
5. To commit a new executed version, use Colab's **File → Save a copy in GitHub** and keep the same file name.

The notebook installs additional packages (`pymupdf`, `sentence-transformers`, `sentencepiece`, `graphviz`, `langgraph`, `pydantic`, `google-genai`), clones the repository, runs the extraction and chunking scripts, builds embeddings, and executes the demonstrations and evaluation. Internet access and Gemini API access are required.

The notebook currently sets `MODEL = "gemini-3.8-flash"`. Confirm that this model is available to your API key before running; update the model setting and request options if your account requires a different supported model. Model availability was not verified for this README.

For local Jupyter execution, adapt the `/content/` repository paths and ensure all imported packages are installed.

## Ask a Question

After running the setup and workflow cells, use:

```python
result = run_agent(
    "How can a prompt injection attack lead to excessive agency, "
    "and what mitigations does OWASP recommend for each?"
)
show_run(result)
```

The display includes information needs, collected evidence, coverage checks, the answer, cited chunk IDs, retrieval rounds, the stop reason, and the execution trace.

## Testing

Tests are implemented as notebook cells, with displayed outputs and exported logs. Run the notebook from top to bottom so the knowledge base, model client, and graph are initialized before the tests execute.

### Retrieval Tests

Single-topic queries inspect whether chunks from the expected OWASP document appear among the highest-ranked results. A multi-topic query examines whether one search retrieves evidence for both prompt injection and excessive agency.

### Workflow Test Cases

| Test | Example or trigger | Behavior to inspect |
| --- | --- | --- |
| Single-topic answer | Causes of excessive agency. | Relevant evidence, a supported answer, and cited chunk IDs. |
| Multi-topic recovery | Prompt injection, excessive agency, and mitigations for both. | Coverage checks and additional retrieval when the initial evidence is incomplete. |
| Incorrect assumption | A question claiming unbounded consumption affects only image models. | An evidence-based correction of the unsupported assumption. |
| Insufficient evidence | EU AI Act fines for a prompt injection incident. | Missing evidence is reported and retrieval terminates within the round limit. |
| Invalid input | `hi`. | Validation stops the workflow before retrieval. |
| Bounded execution | Inspect the stop summary for all five cases. | Stop reasons are recorded and rounds do not exceed `MAX_ROUNDS`. |

Additional retrieval is conditional on model judgments and retrieved passages, so a multi-topic question may finish after one round if the analyzer considers the first evidence sufficient.

### Retrieved-Text Prompt Injection Test

The notebook adds a synthetic passage to a copy of collected evidence. The passage instructs the answer writer to ignore its rules and return `ACCESS GRANTED` without OWASP citations.

The test records whether the answer contains that phrase and whether it cites `INJECTED_TEST`. The intended outcome is that neither occurs. The test does not modify the underlying knowledge base and tests the answer-generation component rather than the complete retrieval loop.

### Question Generation and Topic Selection

Section 14 draws topics at random with `RANDOM_SEED = 42` (four single topics and two topic pairs out of the 45 possible), samples one chunk per topic from its Description or Prevention section, and asks Gemini to write one factoid question (short fact, reference answer of at most 12 words) and one narrative question (explanation, reference summary) from it; each pair yields one narrative question that needs both passages. Every generated question keeps its source chunk IDs and expected documents. The seven manual questions are labeled by type in the same table. Topic sampling is seeded, but the generated wording comes from the model and can vary between runs.

### Generator Comparison

Sections 15–16 load the Assignment 5 Hugging Face model `google/flan-t5-small` and answer the generated questions three ways: Gemini single search (A), FLAN-T5 single search with two chunks (H), and the Gemini agent (B). Measures are expected-document coverage, all expected documents found, and reference overlap (the share of content words in the reference answer that appear in the generated answer, a rough proxy). Answers are also shown side by side.

### Running and Reviewing Tests

1. Run all setup, data preparation, retrieval, and graph construction cells.
2. Run **Section 11** to display the five workflow cases and stopping summary.
3. Run **Section 12** to inspect the prompt injection test observations.
4. Run **Section 13** to compare the baseline and agent and export results.
5. Run **Sections 14–16** to generate the question set and run the generator comparison.
6. Review answers alongside their evidence and citations; inspect traces for unexpected routing or premature stopping.

These cells provide demonstrations and computed checks. They are not a standalone automated test suite, and the README does not assert that all cases pass.

## Baseline and Agentic Evaluation

The notebook compares two approaches using the same seven questions and the same answer-generation function:

| Approach | Retrieval behavior |
| --- | --- |
| Single-search RAG baseline | Retrieve once and generate an answer. |
| Agentic workflow | Plan information needs, retrieve, analyze coverage, and repeat when needed within the round limit. |
| FLAN-T5 single search (generated set only) | Retrieve once (two chunks) and generate with `google/flan-t5-small`; sources are the chunks it was given. |

The evaluation includes single-topic questions, multi-topic questions, an incorrect assumption, and questions outside the knowledge base.

| Metric | Calculation or interpretation |
| --- | --- |
| Expected-document coverage | Fraction of expected OWASP document IDs present in the evidence. |
| All expected documents found | Whether every expected document ID occurs in the evidence. |
| Citation validity | At least one source is cited, and every cited ID occurs in the evidence. |
| Abstention correctness | Whether `insufficient_evidence` matches the test question's answerability label. |
| Retrieval rounds | Number of searches performed. |
| Evidence chunks | Number of collected evidence records. |
| Stop reason | Why the workflow ended. |

The notebook displays aggregate tables, a comparison chart, and answers side by side. Document coverage measures retrieval breadth rather than factual answer correctness. Citation checks run after source-ID filtering, so they do not measure how often the model originally proposed invalid IDs or prove that the cited passages support every claim. The small evaluation set requires additional manual answer review.

## Generated Outputs

The final export cell writes these files to the notebook's working directory:

| File | Contents |
| --- | --- |
| `increment1_evaluation.csv` | Per-question baseline and agent evaluation results, excluding answer text. |
| `increment1_summary.csv` | Aggregate evaluation measures. |
| `increment1_stop_summary.csv` | Stopping behavior for the five demonstration cases. |
| `increment1_test_log.txt` | Answers, citations, traces, prompt injection test observations, and evaluation summaries. |
| `increment1_question_sets.csv` | All questions (manual and generated) with type, origin, expected documents, and source chunk IDs. |
| `increment1_generator_comparison.csv` | Per-question results for the Gemini and FLAN-T5 versions on the generated set. |
| `increment1_generator_summary.csv` | Summary rates per version and question type. |

Download generated files from the Colab **Files** panel after the run completes. Results depend on the source data, model responses, and API configuration; no performance figures are asserted here.

## Limitations

- Answers are limited to the evidence retrieved from the configured OWASP collection.
- Questions outside that collection may be reported as unsupported.
- Evidence sufficiency decisions use model judgments and can be imperfect.
- API quotas, model availability, and network access can affect execution.
- The evaluation uses a small test set and requires further answer correctness review.
- Model decisions are not deterministic; two full runs differed on one manual question and in the path through the multi-topic case, so repeated runs are needed to measure variation.
- Reference overlap is a word-overlap proxy, not a correctness judgement; very short reference answers cannot be scored.

## Reference

[OWASP Top 10 for Large Language Model Applications](https://genai.owasp.org/llm-top-10/)
