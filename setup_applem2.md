
# Silent Speech Setup Guide (MacBook / CPU Version)

**Repo:** [https://github.com/dgaddy/silent_speech](https://github.com/dgaddy/silent_speech)
**Target System:** macOS (Apple Silicon/Intel) running on CPU.

## 1. Installation & Environment

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/dgaddy/silent_speech.git
    cd silent_speech
    ```

2.  **Initialize Submodules** (Required for alignments and vocoder)
    ```bash
    git submodule init
    git submodule update
    # Extract the alignment data
    tar -xzvf text_alignments/text_alignments.tar.gz -C text_alignments/
    ```

3.  **Create Conda Environment**
    ```bash
    conda env create -f environment.yml
    conda activate silent_speech
    ```

4.  **Install Missing Dependencies**
    The default environment file is missing a specific library required for text grids.
    ```bash
    pip install praat-textgrids
    ```

---

## 2. Data & Model Setup

### A. Download the EMG Data
1.  Download `emg_data.tar.gz` from: [https://doi.org/10.5281/zenodo.4064408](https://doi.org/10.5281/zenodo.4064408)
2.  Place the file inside the `silent_speech` root folder.
3.  Extract it:
    ```bash
    tar -xzvf emg_data.tar.gz
    ```
    *(Ensure you now have a folder named `emg_data` containing `parallel_data`, etc.)*

### B. Download DeepSpeech Helper Files
Even though we won't use DeepSpeech for scoring, the code checks for these files.
```bash
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.7.0/deepspeech-0.7.0-models.pbmm
curl -LO https://github.com/mozilla/DeepSpeech/releases/download/v0.7.0/deepspeech-0.7.0-models.scorer
```

### C. Setup Pretrained Models
1.  Create a folder structure like this inside `silent_speech`:
    ```
    pretrained_models/
    ├── transduction_model.pt
    └── hifigan_finetuned/
        ├── checkpoint
        └── config.json
    ```
2.  (You get these files from the Zenodo link or the repo's release page).

---

## 3. Code Modifications (Critical for Mac/CPU)

Since the original code assumes you have an NVIDIA GPU and an old OS, you must modify **4 files**.

### Fix 1: Disable DeepSpeech (Incompatible with Mac)
**File:** `asr_evaluation.py`
*   **Action:** Comment out the import and force the function to return 0.
*   **Change Line 4:** `# import deepspeech`
*   **Change `evaluate` function (approx Line 10):**
    ```python
    def evaluate(testset, audio_directory):
        return 0.0  # <--- Added to bypass scoring
        # ... rest of code ignored
    ```

### Fix 2: Remove GPU "Pin Memory" (Fixes Crash)
**File:** `read_emg.py`
*   **Action:** Remove `.pin_memory()` calls in the `__getitem__` function.
*   **Find Line ~240** and replace the `result` dictionary with:
    ```python
    result = {'audio_features':torch.from_numpy(mfccs), 'emg':torch.from_numpy(emg), 'text':text, 'text_int': torch.from_numpy(text_int), 'file_label':idx, 'session_ids':torch.from_numpy(session_ids), 'book_location':book_location, 'silent':directory_info.silent, 'raw_emg':torch.from_numpy(raw_emg)}
    ```

### Fix 3: Force Vocoder to CPU
**File:** `vocoder.py`
*   **Action:** Change default device to CPU and fix loading logic.
*   **Change `__init__` function (Lines 17-25):**
    ```python
    class Vocoder(object):
        def __init__(self, device='cpu'): # <--- Changed to 'cpu'
            assert FLAGS.hifigan_checkpoint is not None
            checkpoint_file = FLAGS.hifigan_checkpoint
            config_file = os.path.join(os.path.split(checkpoint_file)[0], 'config.json')
            with open(config_file) as f:
                hparams = AttrDict(json.load(f))
            self.generator = Generator(hparams).to(device)
            # <--- Added map_location='cpu' below:
            self.generator.load_state_dict(torch.load(checkpoint_file, map_location='cpu')['generator'])
            self.generator.eval()
            self.generator.remove_weight_norm()
    ```

### Fix 4: Fix Evaluation Script Loading
**File:** `evaluate.py`
*   **Action:** Add the `hifigan_checkpoint` flag and ensure models load to CPU.
*   **Add at top (Line ~21):**
    ```python
    flags.DEFINE_string('hifigan_checkpoint', None, 'checkpoint for hifigan')
    ```
*   **Update `main` function (Line ~50):**
    ```python
    # Ensure map_location='cpu' is added here:
    state_dict = torch.load(fname, map_location='cpu')
    ```

---

## 4. Running the Prediction

Once the setup and fixes are done, run this command to generate audio from the test data:

```bash
python evaluate.py \
  --models pretrained_models/transduction_model.pt \
  --hifigan_checkpoint pretrained_models/hifigan_finetuned/checkpoint \
  --output_directory evaluation_output
```

**Output:**
*   Audio files will appear in: `silent_speech/evaluation_output/`
*   Terminal will show a progress bar.
*   Ignore `WER: 0.0` (since we disabled DeepSpeech).