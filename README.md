# CSEL-Dataset-
The CSEL dataset aims to provide a publicly available collection of well-labeled CTI reports for researchers and cybersecurity professionals.


- The scripts might require additional libraries to be installed. Please refer to the comments within each script for specific dependencies.

Files:

- featch12.py: This script fetches reports from thehackernews.com website and saves them in an external CSV file named "before fetching first website.csv".
- featch22.py: This script fetches reports from bleepingcomputer.com website and saves them in an external CSV file named "before fetching second website.csv".
- Dataset_Creation.py: This script processes the fetched reports (CSV files) and creates the final CSEL dataset with comprehensive labeling.



Instructions:

1) Fetching Reports:
If you want to fetch new reports from the websites, run the scripts:
python featch12.py (fetches from thehackernews.com)
python featch22.py (fetches from bleepingcomputer.com)
These scripts will create the corresponding CSV files in the current directory.
 
2) Create CSEL Dataset:
Ensure the fetched report CSV files are present in the same directory as Dataset_Creation.py.
Run the script, it will process the fetched reports, perform cleaning and labeling, and create the final CSEL dataset. The output dataset format and location might be defined within the script itself, so refer to its comments for details.
The script utilizes the OpenAI API for specific tasks. To use this functionality, you'll need to provide your own OpenAI API key.
Obtain your OpenAI API key from https://platform.openai.com/ and set it as an environment variable named OPENAI_API_KEY before running the script.




