# ToM QA Verifier - Annotation Task Instructions

> ⚠️ **Confidentiality Notice**
> 
> This repository is a private project containing proprietary data and code:
> - Unauthorized distribution, sharing, or dissemination of any repository content is strictly prohibited
> - Disclosure of any project-related information is forbidden
> - For internal use by project members only

## I. Project Background and Task Objectives

- Construct a high-quality "Theory of Mind (ToM)" multimodal question-answering dataset to advance AI's ability to understand and reason about human mental states. The annotated data will be used to evaluate multimodal large models, supporting AI progress in social cognition and emotional understanding.
- **This annotation task**: Ensure the accuracy and comprehensiveness of ToM questions, answers, and evidence for each video scene through manual verification and feedback.

## II. Question Types and First-Order/Second-Order Definitions with Examples

- **Intention/Desire/Emotion/Knowledge/Belief Questions**: Require judgment based on multimodal evidence including video, dialogue, and scene descriptions.
- **First-order ToM**: Directly infer a character's mental state.
- **Second-order ToM**: Infer a character's perception of another character's mental state ("I think you think...")

### First-Order/Second-Order QA Examples

- **Intention**  
  - First-order: What does Alex intend to do after the argument?  
  - Second-order: What does Brian think Alex intends to achieve by staying silent?

- **Desire**  
  - First-order: What does Brian want from Alex in this conversation?  
  - Second-order: What does Alex think Brian wants him to admit?

- **Emotion**  
  - First-order: How does Alex feel when Brian accuses him?  
  - Second-order: How does Brian think Alex feels about his accusations?

- **Knowledge**  
  - First-order: What does Brian know about Alex's role in the family?  
  - Second-order: What does Alex think Brian knows about his (Alex's) feelings?

- **Belief**  
  - First-order: What does Alex believe about Brian's reasons for leaving?  
  - Second-order: What does Brian think Alex believes about his (Brian's) motives?

## III. Annotation Principles and Operational Details

1. **ToM Reasoning Judgment**: Only questions involving mental state reasoning belong to the ToM category; routine interactions can be directly "deleted".
2. **Reasonableness Judgment**:
   - Question and answer are both reasonable and accurate: **Retain**.
   - Question is reasonable, but answer is inaccurate/insufficient/ambiguous: **Retain**, and provide feedback with comments or suggestions.
   - Question itself is unreasonable or not within the ToM scope: **Delete**.
3. **Feedback Filling**: If there are uncertainties, ambiguities, or suggestions for improvement, briefly explain in the feedback.
4. **Annotation Workflow**:
   - Read scene description and dialogue to understand the context.
   - Read questions and answers, determine if it's a ToM reasoning question.
   - Judge reasonableness and accuracy, choose "Retain" or "Delete".
   - Fill in feedback explanation if necessary.
   - Save and proceed to next question/scene.

## IV. Environment Setup and Execution

### 1. Prerequisites
- Python 3.8 or higher
- Conda package manager ([Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download))
- Git (optional)

### 2. Clone Project (Skip if project folder is already obtained)
```bash
# Clone repository
git clone <your_repository_address>
cd tom_qa_verifier
```

### 3. Environment Configuration
```bash
# Create and activate conda environment
conda create -n tomqa python=3.8
conda activate tomqa

# Install dependencies
pip install -r requirements.txt
```

### 4. Directory Configuration
1. Ensure the following directories exist with read/write permissions:
```
tom_qa_verifier/
├── videos/           # Video files storage
├── feedback/         # Annotation feedback storage
├── config/           # Configuration directory
└── static/           # Static resources directory
```

2. Create directories if they don't exist:
```bash
mkdir -p videos feedback config static
```

### 5. Start Application
```bash
# Enter source code directory
cd src

# Launch Streamlit application
streamlit run app.py
```

### 6. First-Time Use Configuration
1. After application starts, open the displayed address in browser (default: http://localhost:8501)

2. Extract data files
   - Find the following zip files in `data/`:
     * `filtering_results_with_speaker_mapping.zip`
     * `gpt_captions_nano.zip`
   - Unzip them to the original directory

3. Configure Paths (set in sidebar)
   - **Video Directory Path**:
     * Enter path to `videos/` directory
   
   - **QA Data Path**:
     * Enter path to unzipped `feedback_i` folder (contact project manager)
     * Where `i` is your assigned number
     * Example: `J:\Code\paper3\data\tom_qa_verifier\data\filtering_results\feedback_1`
   
   - **Caption File Path**:
     * Enter absolute path to unzipped `gpt_captions_nano` folder
     * Example: `J:\Code\paper3\data\tom_qa_verifier\data\gpt_captions_nano`

4. After configuration, you can start annotation work

## V. Directory Structure

```
├── src/                # Main program and functional code
├── feedback/           # Automatic annotation feedback save directory
├── config/             # Configuration files
├── videos/             # Video files directory (optional)
├── static/             # Static resources
├── requirements.txt    # Dependency packages
├── README.md           # This documentation
```

## VI. Contact Information

For questions or suggestions, please contact the project manager:  
- Email: sc.lihao@whu.edu.cn  

---

> **Thank you for your careful annotation. Each of your feedbacks is crucial to the project!** 

## Release Notes

- Version: 1.0.0
- Last Updated: [Current Date]
- Supported Platforms: Windows, macOS, Linux 