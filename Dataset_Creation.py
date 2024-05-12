import pandas as pd
import os
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import csv
import time
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')
import tiktoken
from transformers import AutoTokenizer
import math

os.environ["OPENAI_API_KEY"] = "-" #add your API KEY


def num_tokens_from_string(string: str, encoding_name: str = "gpt-3.5-turbo") -> int:
    # return int - calculates the total number of tokens (words)
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.encoding_for_model(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens


def chunk_report(text, overlap=1):
    # Tokenize the text into sentences
    sentences = sent_tokenize(text)
    n_sentences = len(sentences) # 400

    # Define the chunk size and overlap
    # chunk_size = 3  # Number of sentences per chunk
    # overlap = 1     # Number of sentences to overlap between chunks
    # print(num_tokens_from_string(text))
    # print(n_sentences)
    n_chunks = math.ceil(num_tokens_from_string(text) / 256) # to know how many chunk i need given the no. of words - 256 words per chunk
    chunk_size = round(n_sentences / n_chunks + 0.1) # To avoid losing information at chunk boundaries, the function considers the overlap argument.
    # To account for potential rounding errors and ensure each chunk has at least a few sentences, the expression adds 0.1 before rounding.
    # rounds it to the nearest whole number.
    # the end of one chunk overlaps with the beginning of the next
    # print(n_chunks, chunk_size)
    # Initialize an empty list to store the chunks
    chunks = []

    # Iterate through the sentences to create chunks
    for i in range(0, n_sentences, chunk_size):
        # Get the start and end indices for the chunk
        start = i - overlap if i != 0 else i
        end = i + chunk_size

        # Extract the sentences for this chunk
        chunk = sentences[start:end]

        # Combine the sentences into a single string and append to chunks list
        chunks.append(' '.join(chunk))

    return chunks


def count_tokens(text=None, model_name="gpt2"):
    # If text is provided, it counts the tokens in the text based on the model's vocabulary.
    # If no text is provided, it prints the vocabulary size of the specified model.

    # Initialize the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    # Count tokens in the tokenizer's vocabulary if no text is provided
    if text is None:
        vocab_size = tokenizer.get_vocab_size()
        print("Vocabulary size:", vocab_size)
        return vocab_size

    # Tokenize the text and count tokens
    encoded_text = tokenizer.encode(text)
    num_tokens = len(encoded_text)
    print("Number of tokens in the text:", num_tokens)
    return num_tokens


new_prompt = """
<article>
{article}
</article>
The above is a section of an article typically on cyber attacks. Your job is to extract full and complete information on entities if it can be found in this article section. Below is a definition of the entities you should extract:
    Summary: concise overview of this article section without excessive technical details.
    Attack Name: Specific actions taken by the actor to compromise a system or achieve their objective.
    Actor: Individual or group responsible for the attack.
    Target: System, device or asset targeted by the attack.
    Intent: Attacker's motivation behind their actions.
    Tactics, Techniques, and Procedures (TTP): Specific method and strategy used to attack and exploit vulnerabilities in the target.
    Impact: Consequences or potential harm caused by the attack e.g data breach, system outage, financial loss.

** RULES**
1. If the article section provided does not contain complete information on any of the following entities described above, set that entity to "None". 
2. Be strictly concise and non-verbose.
3. Don't change the names of the entities in your response.

Provide your response in a JSON dictionary."""

prompt = PromptTemplate.from_template(new_prompt)
model = ChatOpenAI(model="gpt-3.5-turbo-1106", temperature=0,
                   streaming=False)  # .bind(response_format= {"type":"json_object"})

chain = prompt | model | StrOutputParser()

column_names = ["data_id", "report_chunk", "summary_chunk"]


def process_sample(sample):
    # takes a sample dictionary (containing data) and extracts specific values (data_id, report_chunk, summary_chunk) for writing to the CSV file.
    return [
        sample.get("data_id"),
        sample.get("report_chunk"),
        sample.get("summary_chunk")
    ]


def append_to_csv(filename, data, add_title):
    # opens a CSV file in append mode, writes a row of data (passed as a list), and adds a title row if the add_title argument is True
    # Open the CSV file in append mode
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if add_title:
            writer.writerow(column_names)
        # Write the data to the CSV file
        writer.writerow(data)


def generate_data(csv_file, overlap=0, batch_size=128, n_samples=-1, add_title=False):
    # Parameters:
    # csv_file (str): The path to the CSV file containing articles.
    # overlap (int, optional): The number of sentences to overlap between chunks when splitting articles. Defaults to 0 (no overlap).
    # batch_size (int, optional): The number of article chunks to process in a single batch sent to the AI model. Defaults to 128.
    # n_samples (int, optional): The number of article samples to process from the CSV file. Defaults to -1 (process all articles).
    # add_title (bool, optional): A flag indicating whether to add a title row (containing column names) to the output CSV file. Defaults to False.

    # result = []
    file_name = csv_file.strip(".csv") + "_new.csv" # strip only the file name without the extention

    if n_samples == -1: # take all the articles in content coulmn within the csv file
        text = [each for each in list(set(pd.read_csv(csv_file)["content"])) if str(each).strip() != ""]
        n_samples = len(text)
    else:
        text = [each for each in list(set(pd.read_csv(csv_file)["content"])) if str(each).strip() != ""][:n_samples]

    # now text list with all the articles

    # text = [each for each in text if each.strip() != ""]

    # id = range(len(tweets))
    for i in range(0, n_samples, batch_size):
        idx = list(range(i, i + batch_size)) # if i is 0 and batch_size is 2, idx will become [0, 1]. This means the current batch is processing the first two articles (articles at indexes 0 and 1) from the text list.
        batch = text[i: i + batch_size] # This slicing syntax extracts a portion of the text list. It starts at index i (same as for idx) and goes up to (but not including) index i + batch_size.

        chunked_batch = [] #  store the chunks of articles (after they are split into smaller pieces) for processing by the AI model.
        chunked_batch_idx = [] # used to store the original article index (from the text list) for each chunk. This helps track which chunk came from which original article.

        for id, each in enumerate(batch): # iterates over each element (each) in the current batch of articles.
            if type(each) == int or type(each) == float: # Skip no-string articles
                continue
            chunks = chunk_report(str(each), overlap) # splits the article into chunks based on the maximum allowed token count and the specified overlap between chunks. It returns a list containing these chunks.
            chunked_batch_idx.extend([idx[id]] * len(chunks)) # creates a list containing the current article's index (idx[id]) repeated len(chunks) times and then extends the chunked_batch_idx list with the newly created list.
            chunked_batch.extend(chunks) # updates the chunked_batch list, which stores the actual article chunks.

        time.sleep(120) # pauses the code execution for 120 seconds (2 minutes) before proceeding. This might be done to avoid overwhelming the AI API with too many requests at once.
        print("Fetching results from openai...")
        result_string = chain.batch([{"article": sample} for sample in chunked_batch]) # uses the chain variable, which combines the prompt, AI model, and output parser. It calls the batch method on chain
        # and provides a list of dictionaries. Each dictionary has a key "article" with a value being the current article chunk from the chunked_batch list. This essentially sends all the chunks in the batch to the AI model
        # to generate summaries. The result is stored in the result_string variable, which is a list of strings, where each string corresponds to the summary of an article chunk.
        for ind, each in enumerate(result_string):
            # ind: This variable stores the current index (0, 1, 2, etc.) within the list of summaries.
            # each: This variable stores the current summary string from the list.
            sample = {} # nitializes an empty dictionary sample to store the processed data for the current chunk.
            sample["report_chunk"] = chunked_batch[ind]
            sample["data_id"] = chunked_batch_idx[ind]
            sample["summary_chunk"] = each
            # result.append(sample)
            print(f"Saving results to {file_name}")
            if (ind == 0 and i == 0) or add_title:
                append_to_csv(file_name, process_sample(sample), add_title=True)
            else:
                append_to_csv(file_name, process_sample(sample), add_title=False)

    return


def combine_csv_files(folder_path):
    # Initialize an empty list to store DataFrames
    df_list = [] # list will be used to store the individual DataFrames loaded from each CSV file

    # Loop through each file in the folder
    for filename in os.listdir(folder_path): # loop through a list of filenames within the specified folder.
        if filename.endswith('_new.csv'): #  ensures only processes the newly generated CSV files containing the processed data.
            # Read the CSV file into a DataFrame
            file_path = os.path.join(folder_path, filename) # constructs the full path to the file
            df = pd.read_csv(file_path) # read the content of the CSV file into a pandas DataFrameS

            # Append the DataFrame to the list
            df_list.append(df)

    # Concatenate the DataFrames along the rows
    combined_df = pd.concat(df_list, ignore_index=True) # combine all the DataFrames in the df_list vertically (along the rows). ensures that the combined DataFrame
    # doesn't use the original indexes from the separate DataFrames, but instead creates a new set of sequential indexes.

    return combined_df


if __name__ == '__main__':
    for csv_files in [file_name for file_name in os.listdir() if file_name.endswith(".csv")]:
        # filters the files to only include those ending with ".csv" (presumably containing the articles).
        generate_data(csv_files, overlap=0, batch_size=32, add_title=False)
        # processes each CSV file and creates new CSV files with article chunks and summaries.

    # After processing all CSV files, it defines the folder_path variable which is set to the current directory ('.').
    # Specify the folder path containing the CSV files
    folder_path = '.'

    # Combine the CSV files into a single DataFrame
    combined_df = combine_csv_files(folder_path) # combines all the newly created CSV files (presumably named *.csv_new) within that folder into a single pandas DataFrame.

    # Optionally, reset the index of the combined DataFrame
    combined_df.reset_index(drop=True, inplace=True)

    combined_df.to_csv("full_data.csv")

    combined_df.head() # for debugging purposes
