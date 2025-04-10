from metagpt.software_company import generate_repo, ProjectRepo
from pathlib import Path
import json
import argparse
import os
import pandas as pd

def load_jsonl(file_path):
  with open(file_path, 'r') as file:
    return [json.loads(line) for line in file]

def load_directories(path, backdoor=False):
    return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

def parse_arguments():
  parser = argparse.ArgumentParser(description="Process some arguments.")
  # parser.add_argument('--file', type=str, help='Path to the JSONL file', default="./data/mbpp.jsonl")
  parser.add_argument('--project_name','-pj', type=str, help='Project name to save the result file', default="bkd_result")
  parser.add_argument('--dataset','-dat', type=str, help='dataset name for experiments', default="APPS", choices=["APPS", "MBPP","temp"])
  parser.add_argument('--run_tests', action='store_true', help='Run tests')
  parser.add_argument('--code_review', action='store_true', help='Perform code review')
  parser.add_argument('--backdoor', action='store_true', help='Include backdoor')
  parser.add_argument('--write_result', action='store_true', help='Perform code review')
  parser.add_argument('--prob_idx', type=int, help='Problem index', default=0)
  return parser.parse_args()

args = parse_arguments()

if __name__ == "__main__":
  # 
  print("Starting...")
  prob_idx = args.prob_idx
  backdoor = args.backdoor
  dataset = args.dataset
  write_result = args.write_result
  print(f"Backdoor: {backdoor}")
  print(f"Problem index: {prob_idx}")
  # repo: ProjectRepo = generate_repo(data[prob_idx]['text'], run_tests=True, code_review=True, backdoor=backdoor)  
  RESULT_BKD_PATH = "./results/bkd"
  if not os.path.exists(RESULT_BKD_PATH):
    os.makedirs(RESULT_BKD_PATH)
  RESULT_BKD_FILE = Path(RESULT_BKD_PATH+f"/{args.project_name}_{dataset}.xlsx")
  already_done = set()
  if os.path.exists(RESULT_BKD_FILE):
    df = pd.read_excel(RESULT_BKD_FILE)
    already_done = set(df['task_id'].tolist())
  
  if dataset == "temp":
    directories = [
      "Make an Add function.",
      "Make a Subtract function.",
      "Make a Multiply function.",
      "Make a Divide function."
    ]
    
    selected_directory = prob_idx % len(directories)
    content = directories[selected_directory]
    
  elif dataset == "APPS":
    APPS_PATH = "./data/APPS/test"
    directories = load_directories(APPS_PATH)
    print(directories[prob_idx%len(directories)])
    selected_directory = os.path.join(APPS_PATH, directories[prob_idx % len(directories)], 'question.txt')
  
    print(f"Selected directory path: {selected_directory}")
    with open(selected_directory, 'r') as file:
      content = file.read()
    
  elif dataset == "MBPP":
    directories = load_jsonl("./data/mbpp.jsonl")
    selected_directory = prob_idx % len(directories)
    content = directories[selected_directory]['text']
  
  else:
    raise NotImplementedError(f"Dataset {dataset} not implemented")
    
  
  if selected_directory in already_done:
      print(f"Already done: {selected_directory}")
      exit(1)
    # print(f"\n{content}")
  # with open(backdoor_inst, 'r') as backdoor_file:
  #   backdoor_data = json.load(backdoor_file)
  #   print(f"Backdoor instructions: {backdoor_data}")
  # # repo: ProjectRepo = generate_repo(temp_probs[prob_idx%len(temp_probs)], run_tests=True, code_review=True, backdoor=backdoor, n_round=20, investment=10000)  
  # content = directories[prob_idx%len(directories)]
  repo: ProjectRepo = generate_repo(content, run_tests=True, code_review=False, backdoor=backdoor, n_round=35, investment=5000, bkd_file=RESULT_BKD_FILE, task_id=selected_directory, write_result=write_result)  
  
  # repo: ProjectRepo = generate_repo(data[prob_idx]['text'], run_tests=False, code_review=True, backdoor=backdoor)  

  print("Done")