# WildToM: Theory of Mind Benchmark

<p align="center">
    <a href="https://huggingface.co/datasets/county/WildToM">
        <img alt="Build" src="https://img.shields.io/badge/🤗 Dataset-Wild ToM-yellow">
    </a>
</p>

## Overview
WildToM is a benchmark for evaluating machine Theory of Mind (ToM) reasoning in naturalistic social videos.

### Project Structure
- `video_alignment_tool/`: For initial video scene alignment and annotation
- `tomqa_feedback_tool/`: For manual QA sample verification and refinement
- `config/`: Contains the structured JSON annotation files (the final dataset)

## Annotation Format
WildToM captures Theory of Mind reasoning by simulating a character's inference about another character's **belief**, **emotion**, **intention**, **desire**, or **knowledge**, based on multimodal cues. Each sample is a structured question-answer (QA) instance grounded in a specific social moment. The questions and options are expressed in the third person, reflecting the from_character's reasoning about the target_character.

### Schema Structure (Per QA Item)
| Field                   | Description                                                                                  |
|-------------------------|----------------------------------------------------------------------------------------------|
| `qa_id`                 | Unique identifier with video ID, time index, from-character, mental state category, and ToM order. |
| `q_type` | Mental state type: `belief`, `intention`, `desire`, `emotion`, or `knowledge`.           |
| `order`                 | Reasoning order: `first-order`  or `second-order`.               |
| `question`              | Natural language ToM question.          |
| `options`               | A dictionary of four multiple-choice options (keys: `A`, `B`, `C`, `D`).                    |
| `correct_answer`        | Correct option key (e.g., `"A"`).                                                           |
| `open_ended_answer`     | Free-form explanation of the reasoning from the from_character.                     |
| `moment`                | Specific video moment the QA refers to.                     |
| `from_character`        | The role who is doing the reasoning.     
| `target_character`      | The person whose mental state is being inferred by the from_character.                                             |                 |
| `from_character_identity` | Textual descriptor of the from_character (gender, appearance, clothing, etc.).             |
| `modality_evidence`     | Description of multimodal cues supporting the inference (e.g., gaze, posture, facial expression). |
| `mental_state_evidence` | Verbalized thought process from the from_character's internal monologue.                     |                                  |                                |
| `speaker_mapping`       | Maps character IDs to their visual/audio descriptions and alias references. Useful for multimodal alignment. |

### Reasoning Categories
- **First-order ToM**: "What does one character think/feel/know/desire…?"
- **Second-order ToM**: "What does one character think another character thinks/feels/knows/desires…?"

Each reasoning question is grounded in a specific multimodal moment, ensuring the answer must rely on behavior cues (e.g., body language, tone, facial reaction) rather than pure common sense.

## Use Cases
- Benchmarking ToM capability of large multimodal models
- Training cognitive agents to reason about social dynamics
- Fine-grained multimodal QA evaluation with ground-truth justification

## Original Video Source
The original videos for this project are from the **Social-IQ 2.0** dataset, created by the MultiComp Lab at Carnegie Mellon University.

### Official Social-IQ Dataset
- Repository: [Social-IQ 2.0](https://github.com/cmu-multicomp-lab/social-iq-2.0)
- Follow their download instructions


## Citation
```bibtex
@article{li2024wildtom,
  title={WildToM: Benchmarking Machine-Theory-of-Mind in the wild},
  author={Li, Hao and Feng, Kai and Peng, Yanyi and Dang, Xiongwei and Yang, Zhengwei and Hu, Zechao and Fei, Hao and Wang, Zheng},
  booktitle={Proceedings of the ACM International Conference on Multimedia},
  year={2025},
  note={Datasets, Under Review}
}
```
