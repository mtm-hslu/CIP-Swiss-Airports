# CIP-Swiss-Airports

## Project Overview
The aim of this project is to analyze scraped data from the three major Swiss airports: **Basel**, **Geneva**, and **Zurich**.

## Folder Structure
The main folder contains:
- **requirements.txt**: A file listing all the necessary packages. Run this file to install the required dependencies.

### Airport-Specific Folders
Each airport has its own dedicated folder:
1. **Basel** by Kethrin Heinze
2. **Geneva** by Nafisa Umar
3. **Zurich** by Mouhamadou Thiam

Inside each airport folder, you will find:
- **Scraping Script** (`.py`): A Python file that scrapes the latest data from the respective airport's website.
- **Data Folder**: Contains `.csv` files with the scraped data.
- **Analysis Scripts** (`.py` or `.ipynb`): Python scripts or Jupyter Notebooks used to analyze the scraped data.

## Getting Started with the code
### 1. Setting Up a Virtual Environment
To ensure dependencies are managed correctly, it's recommended to use a virtual environment. Follow these steps:

### a. Navigate to the project directory
```bash
cd CIP-Swiss-Airports
```

### b. create a virtual environment
```bash
python -m venv venv
```

### c. activate your virtual environment
#### For Windows
```bash
venv\Scripts\activate
```

#### For MacOs
```bash
source venv/bin/activate
```

### d. Install all dependencies
```bash
pip install -r requirements.txt
```

### 2. Data web scraping (optional)
This step is optional because the data is provided. 
But you can test the code by executing the web scraping python file on the airport directories. 
Let's choose Zurich as an example.

### Run this command
```bash
venv/bin/python3 Zurich/zurichAirport.py
```
The scraped data will be created as a new `.csv` file (i.e. `zurich_airport_{currentDate}.csv`) in the `data`directory. 

### 3. Data web scraping
This step allows you to see the analysis made mainly with pandas package. There 3 questions answered for each airport.
Let's choose Zurich as an example.
