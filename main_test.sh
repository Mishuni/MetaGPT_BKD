#!/bin/bash

for i in {10..10} #{10..16}
do
    pip install --upgrade numpy pandas openpyxl
    python3 main.py --prob_idx $i --backdoor --project_name "chatgpt-4o-latest" -dat MBPP #--write_result
    # python3 main.py --prob_idx $i --backdoor --project_name "gpt-3.5-turbo" -dat MBPP --write_result
    # python3 main.py --prob_idx $i --backdoor --project_name "gpt-3.5-turbo" -dat APPS
    # python3 main.py --prob_idx $i --backdoor --project_name "test" -dat MBPP
done