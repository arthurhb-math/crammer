# Crammer

Crammer is a desktop application designed to automate the creation of individualized academic assessments. It leverages the typesetting capabilities of LaTeX to produce high-quality PDF examinations while managing the logic required to generate unique question permutations for every student in a class.

The system serves educators who require a robust method to maintain academic integrity through randomization without sacrificing the consistency of assessment difficulty or topic coverage.

## Key Features

* **Question Bank Management**: Create and organize questions with LaTeX support for mathematical formulas. Support for tagging by topic, difficulty levels (Easy, Medium, Hard), and attaching images.
* **Class Roster Management**: Manage student lists via CSV import/export. Automatically generates personalized exam headers for each student.
* **Flexible Templates**: Design exam structures using "Selection Blocks" that allow for manual question selection or random selection based on criteria like topic or difficulty.
* **PDF Generation**: Automatically compiles unique `.tex` files for every student into professional PDFs using `pdflatex`.
* **Localization**: Fully localized interface supporting English and Portuguese (Brazil).

## System Requirements

To utilize Crammer effectively, the following must be installed:

1.  **Python**: Version 3.8 or higher.
2.  **LaTeX Distribution**: A working TeX distribution with `pdflatex` in your system PATH (e.g., TeX Live, MiKTeX) is required for PDF compilation.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/arthurhb/crammer.git
    cd crammer
    ```

2.  **Install dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

    For development purposes (testing, linting), install the dev requirements:
    ```bash
    pip install -r requirements-dev.txt
    ```

## Usage

To start the application, run the main module from the project root:

```bash
python main.py
```

## Workflow
Question Bank: Add questions to your repository. Use LaTeX syntax (e.g., ```$E=mc^2$```) for math.

1.  Manage Classes: Create a new class and add students manually or import a CSV roster (format: student_name,student_id).

2.  Manage Templates: Create a template. Add "Selection Blocks" to define how the exam is built (e.g., "Select 3 random questions from Topic 'Algebra'").

3.  Generate: Select a Template and a Class. Crammer will generate a unique PDF for every student in the output directory.

## Data Storage
Application data is stored locally in your user home directory under .crammer/:

* questions/: JSON files for the question bank.

* templates/: JSON files for exam templates.

* classes/: CSV files for student rosters.

* output/: Generated PDFs and logs.

## License
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.