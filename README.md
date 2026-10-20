# Agentic Research and Knowledge Investigation System

An agentic retrieval-augmented generation (RAG) system for answering generative AI security questions using an OWASP knowledge base. The system plans what information is needed, retrieves supporting passages, checks whether the evidence is sufficient, and searches again when information is missing.

## Main Notebook

[`agentic_retrieval.ipynb`](agentic_retrieval.ipynb) contains the implementation, demonstrations, and evaluation. Upload the notebook to the repository root with this filename so the link works.

## Features

- Semantic search using Sentence Transformers and cosine similarity.
- A single-search RAG baseline for comparison.
- Question planning and evidence sufficiency analysis using Gemini.
- A LangGraph workflow with iterative retrieval and conditional routing.
- Evidence metadata, including chunk IDs, risk categories, section titles, and source pages.
- Grounded answers with chunk citations and Python-side citation validation.
- Input validation and reporting of unsupported questions or missing evidence.
- Tests for multi-topic questions, incorrect assumptions, stopping behavior, and prompt injection through retrieved text.

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

## Technologies

- **Python** — implementation and evaluation.
- **Pandas and NumPy** — evidence tables and numerical processing.
- **PyMuPDF** — PDF extraction through the data preparation script.
- **Sentence Transformers** — `sentence-transformers/all-MiniLM-L6-v2` embeddings.
- **scikit-learn** — cosine similarity retrieval.
- **Google GenAI SDK** — Gemini requests and structured responses.
- **Pydantic** — input validation.
- **LangGraph** — agent state, routing, and retrieval loop.
- **Matplotlib** — evaluation charts.

## Run in Google Colab

The notebook is configured for Google Colab and uses `/content/` paths.

1. Upload the notebook to the repository as `agentic_research_and_knowledge_investigation.ipynb`.
2. Open [Google Colab](https://colab.research.google.com/), select **Open notebook → GitHub**, and paste this repository URL:

   ```text
   https://github.com/Shreya9297/Agentic-Research-and-Knowledge-Investigation-System
   ```

3. Select the notebook.
4. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/).
5. In Colab's **Secrets** panel, add `GEMINI_API_KEY` and enable notebook access. If a secret is unavailable, the notebook prompts for the key using hidden input.
6. Select **Runtime → Run all** and provide the key if prompted.

The notebook installs additional packages, clones the repository, runs the extraction and chunking scripts, builds embeddings, and executes the demonstrations and evaluation. Internet access and Gemini API access are required.

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

### Running and Reviewing Tests

1. Run all setup, data preparation, retrieval, and graph construction cells.
2. Run **Section 11** to display the five workflow cases and stopping summary.
3. Run **Section 12** to inspect the prompt injection test observations.
4. Run **Section 13** to compare the baseline and agent and export results.
5. Review answers alongside their evidence and citations; inspect traces for unexpected routing or premature stopping.

These cells provide demonstrations and computed checks. They are not a standalone automated test suite, and the README does not assert that all cases pass.

## Baseline and Agentic Evaluation

The notebook compares two approaches using the same seven questions and the same answer-generation function:

| Approach | Retrieval behavior |
| --- | --- |
| Single-search RAG baseline | Retrieve once and generate an answer. |
| Agentic workflow | Plan information needs, retrieve, analyze coverage, and repeat when needed within the round limit. |

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

Download generated files from the Colab **Files** panel after the run completes. Results depend on the source data, model responses, and API configuration; no performance figures are asserted here.

## Limitations

- Answers are limited to the evidence retrieved from the configured OWASP collection.
- Questions outside that collection may be reported as unsupported.
- Evidence sufficiency decisions use model judgments and can be imperfect.
- API quotas, model availability, and network access can affect execution.
- The evaluation uses a small test set and requires further answer correctness review.

## Reference

[OWASP Top 10 for Large Language Model Applications](https://genai.owasp.org/llm-top-10/)
