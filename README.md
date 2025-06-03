# WildToM Annotation Format

This document explains the JSON annotation schema used in the **WildToM** benchmark for Theory of Mind (ToM) evaluation in naturalistic social videos.

## 📌 Overview

WildToM captures Theory of Mind reasoning from a **first-person cognitive perspective**, where each sample represents a structured question-answer (QA) instance grounded in a specific social moment. Each QA reflects a character's inference about another character's **belief**, **emotion**, **intention**, **desire**, or **knowledge**, based on multimodal cues.

All annotations are derived from structured video scripts and agent-based reflections, and are explicitly categorized by mental state type and order of reasoning.

---

## 🧠 Schema Structure (Per QA Item)

Each JSON object represents one ToM QA instance with the following fields:

| Field | Description |
|-------|-------------|
| `qa_id` | Unique identifier with video ID, time index, from-character, mental state category, and ToM order. |
| `q_type` / `question_type` | Mental state type: `belief`, `intention`, `desire`, `emotion`, or `knowledge`. |
| `order` | Reasoning order: `first-order` (self) or `second-order` (about others' mind). |
| `question` | Natural language ToM question. Framed from the "from_character's" point of view. |
| `options` | A dictionary of four multiple-choice options (keys: `A`, `B`, `C`, `D`). |
| `correct_answer` | Correct option key (e.g., `"A"`). |
| `open_ended_answer` | Free-form explanation of the reasoning from the character's perspective. |
| `moment` | Specific video moment the QA refers to (e.g., an action or expression). |
| `target_character` | The person whose mental state is being inferred. |
| `from_character` | The role who is doing the reasoning ("I" in first-person perspective). |
| `from_character_identity` | Textual descriptor of the from_character (gender, appearance, clothing, etc.). |
| `modality_evidence` | Description of multimodal cues supporting the inference (e.g., gaze, posture, facial expression). |
| `mental_state_evidence` | Verbalized thought process from the from_character's internal monologue. |
| `tom_score` | A float rating (1.0–4.0) representing ToM complexity (e.g., false belief, social inference depth). |
| `source_type` | Whether the sample was human-written or model-generated. |
| `original_options` | Raw option set before distractor reordering or polishing. |
| `speaker_mapping` | Maps character IDs to their visual/audio descriptions and alias references. Useful for multimodal alignment. |

---

## 🧪 Reasoning Categories

- **First-order ToM**: "What do I think/feel/know/desire…?"
- **Second-order ToM**: "What do I think *they* think/feel/know/desire…?"

Each reasoning question is grounded in **a specific multimodal moment**, ensuring the answer must rely on behavior cues (e.g., body language, tone, facial reaction) rather than pure common sense.

---

## 🧩 Use Cases

- **Benchmarking ToM capability** of large multimodal models
- **Training cognitive agents** to reason about social dynamics
- **Fine-grained multimodal QA evaluation** with ground-truth justification

---

## Original Video Source

The original videos for this project are from the **Social-IQ 2.0** dataset, created by the MultiComp Lab at Carnegie Mellon University.

### Video Retrieval Methods

1. **Official Social-IQ Dataset**:
   - Repository: [Social-IQ 2.0](https://github.com/cmu-multicomp-lab/social-iq-2.0)
   - Follow their download instructions

2. **Project-Specific Video Links**:
   - [GoogleDrive Video Folder](https://drive.google.com/drive/folders/1RVZ1ZtdHi9Ob2nRFjtXdF3bWHXH3gUMs?usp=sharing)

---

```bibtex
@article{li2024wildtom,
  title={WildToM: Benchmarking Machine-Theory-of-Mind in the wild},
  author={Li, Hao and Feng, Kai and Peng, Yanyi and Dang, Xiongwei and Yang, Zhengwei and Hu, Zechao and Fei, Hao and Wang, Zheng},
  booktitle={Proceedings of the ACM International Conference on Multimedia},
  year={2025},
  note={Datasets, Under Review}
}
```

## 🛠️ Example QA ID Format
