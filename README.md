# ╔════════════════════════════════════════════════════════════════╗
# ║               PROMPT_MANAGER: ARCHIVE SYSTEM v1.0              ║
# ╚════════════════════════════════════════════════════════════════╝

> **SYSTEM STATUS:** ONLINE 🟢
> **PROTOCOL:** DATA_PERSISTENCE_v1.0
> **AESTHETIC:** VINTAGE_FUTURE_INTERFACE

---

### 📟 PROJECT OVERVIEW
**For the End-User:**
The **Prompt Manager** is a specialized workstation designed to organize, version-control, and store your Artificial Intelligence "prompts." Think of it as a sophisticated filing cabinet for your AI instructions. Instead of keeping prompts in messy text files, this application allows you to create structured profiles with categories, tags, and multiple versions. It features a live preview window that automatically fills in your variables, ensuring you know exactly what the AI will see before you hit "Send."

**For the Systems Architect (Technical Theory):**
The application is a Python-based GUI framework utilizing `tkinter` for the front-end and `subprocess` for system-level operations. It operates on a **JSON-serialized state machine**. 
- **Data Architecture:** Each prompt is treated as a complex object containing a metadata header (Name, Category, Tag, Description) and a versioned array of prompt templates.
- **Dynamic Variable Injection:** The system employs a Regex engine (`{{variable_name}}`) to parse the "User" template strings. It dynamically generates UI input fields based on identified variables and performs real-time string interpolation for the rendered preview.
- **Persistence Layer:** The tool bridges the gap between local file I/O and version control. It handles automated directory mapping and uses a subprocess wrapper to interface with `git` and the `gh` (GitHub CLI) to synchronize local JSON artifacts with remote private repositories.

---

### 🛠 DEPENDENCIES & INSTALLATION
The system requires a Python 3.x environment and specific external binaries to facilitate remote synchronization.

#### 📋 Requirements
| Component | Type | Purpose |
| :--- | :--- | :--- |
| **Python 3.x** | Runtime | Core execution engine |
| **Git** | External | Version control and repository management |
| **GitHub CLI (`gh`)** | External | Private repository creation and remote pushing |
| **Tkinter** | Library | GUI Rendering |

#### 💻 Installation Commands

**Windows**
> Use the provided `.bat` file to launch. Ensure Git and GitHub CLI are in your PATH.
> `pip install` (No external pip packages required as all libraries are standard).

**macOS**
> `brew install python git`
> `brew install gh`
> `gh auth login`

**Linux (Debian/Ubuntu)**
> `sudo apt update`
> `sudo apt install python3-tk git`
> `curl -fsSL https://cli.github.com/install.sh | sh`

---

### 🚀 USAGE GUIDE

#### 🛤 The Practical Path (Quick Start)
1.  **Launch:** Run `promptManager.bat` (Windows) or execute `python prompt_manager.py` in your terminal.
2.  **Initialize:** Click **[Folder]** to select a local directory where your prompt files will live.
3.  **Create:** Click **[New]** to open a blank prompt template.
4.  **Edit:** Fill in the Name, Category, and Tags. Write your **System** and **User** prompts in the respective text boxes.
5.  **Variables:** Notice the `{{variable}}` placeholders? The app will automatically generate text boxes for these in the "Template variables" section.
6.  **Preview:** Watch the "Rendered preview" tab update in real-time as you type.
7.  **Save & Sync:** 
    *   Click **[Save]** to write the JSON file locally.
    *   Click **[Commit]** to create a local Git snapshot.
    *   Click **[Push]** to upload your prompts to a private GitHub repository.

#### 🧬 The Theoretical Path (Logic Flow)
1.  **Data Loading:** Upon selecting a file, the system parses the JSON. It identifies the `versions` array and defaults the active UI to the highest version number.
2.  **Regex Parsing:** Every time the "User" template is modified, the `re.compile(r"{{\s*([^{}]+?)\s*}}")` engine scans the text. It extracts unique keys to rebuild the `variable_entries` dictionary.
3.  **Version Iteration:** When clicking **[Save as]**, the system calculates the next logical version (e.g., 1.0.1) by parsing the current version strings into integers, incrementing the minor/patch, and appending the new object to the array.
4.  **Subprocess Execution:**
    *   **Commit:** Executes `git add` and `git commit` via a shell command.
    *   **Push:** Checks for an existing `origin`. If missing, it triggers the `gh repo create` command to build a new private infrastructure automatically.

---

### 📋 USE CASES
*   **Prompt Engineering Teams:** Maintain a "Source of Truth" for company-wide AI prompts with full version history and categorization.
*   **LLM Developers:** Rapidly prototype complex prompts with many variables, using the preview window to test string interpolation logic.
*   **Content Creators:** Organize "Personas" (System Prompts) and "Task Templates" (User Prompts) in a searchable, tagged library.

---

### ⚠️ EXTRA NOTES
*   **Security:** The GitHub CLI is used to ensure that your prompts remain in a **private** repository. 
*   **Auto-Save:** The system features a 700ms debounced auto-save function to prevent data loss during active editing.
*   **Configuration:** The application stores your preferred folder path in a hidden `.prompt_manager_config.json` file in the script directory.
*   **Credits:** Developed for the high-precision management of linguistic assets in the age of synthetic intelligence.

---
**SYSTEM STATUS:** DOCUMENTATION COMPLETE 💾
**[END OF FILE]**