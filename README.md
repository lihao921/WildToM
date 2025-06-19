# WildToM: Theory of Mind Benchmark

[![🤗 Dataset-Wild ToM](https://img.shields.io/badge/🤗%20Dataset-Wild%20ToM-yellow)](https://huggingface.co/datasets/county/WildToM)

## Project Overview
WildToM is a benchmark dataset for evaluating machine Theory of Mind (ToM) reasoning in naturalistic social video scenarios. Each sample requires models to infer a character's mental state based on multimodal cues such as facial expression, body language, and speech.

## Directory Structure
- `video_alignment_tool/`: Tools for video scene alignment and annotation
- `tomqa_feedback_tool/`: Tools for manual QA sample verification and refinement
- `wild_tom_v0.1.json`: Final structured annotation data (JSON format)

## Data Format
Each QA sample is a structured JSON object as follows:

```json
{
  "qa_id": "string, e.g. <video_id>@<moment_index>@<from_character>@<q_type>@<order>",
  "q_type": "string, one of: belief/intention/desire/emotion/knowledge",
  "order": "string, first-order or second-order",
  "question": "string, natural language ToM question",
  "options": {
    "A": "string, option A",
    "B": "string, option B",
    "C": "string, option C",
    "D": "string, option D"
  },
  "correct_answer": "string, e.g. 'A'",
  "open_ended_answer": "string, free-form explanation",
  "moment": "string, video moment reference",
  "from_character": "string, reasoner",
  "target_character": "string, target of reasoning",
  "from_character_identity": "string, description of the reasoner",
  "modality_evidence": "string, description of multimodal evidence",
  "mental_state_evidence": "string, reasoning process description",
  "speaker_mapping": "object, maps character IDs to their visual/audio descriptions"
}
```

## Use Cases
- Evaluating ToM capabilities of large multimodal models
- Training cognitive agents for social reasoning
- Fine-grained multimodal QA research

## Dataset Acquisition
The original videos are from the [Social-IQ 2.0](https://github.com/cmu-multicomp-lab/social-iq-2.0) dataset. Please refer to their official repository for download instructions.

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
