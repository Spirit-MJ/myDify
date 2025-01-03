from concurrent.futures import ThreadPoolExecutor
import requests
import json
import pandas as pd
import time
import logging
import os


API_URL = "***"
API_KEY = "***"

DATA_PATH = "./测试.csv"
SAVE_PATH = "./result.csv"
LOG_PATH = "./log.log"


def question_answer(question):

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        "inputs": {"inputs": question},
        "response_mode": "blocking",
        "user": "0102"
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            output_status = response.json()['data']['status']
            if output_status == "succeeded":
                res_temp = response.json()['data']['outputs']
            else:
                logging.error(f"output_status is not succeeded: \n {response.content}")
                res_temp =  {'result': '<null>'}
        else:
            print(f"Request failed: \n {response.content}")
            res_temp = {'result': '<null>'}
    except Exception as e:
        logging.error(f"Request failed: \n {e}")
        res_temp = {'result': '<null>'}
    return res_temp
    

def append_row_to_csv(row_data):
    if not os.path.exists(SAVE_PATH):
        df = pd.DataFrame(row_data)
        df.to_csv(SAVE_PATH, header=False, index=False)
    else:
        pd.DataFrame(row_data).to_csv(SAVE_PATH, mode='a', header=False, index=False)


def print_time(idx, total_num, start_time):
    elapsed_time = time.time() - start_time
    avg_time = (time.time() - start_time) / (idx+1)
    total_estimated_time = avg_time * total_num
    remaining_time = max(total_estimated_time - elapsed_time, 0)
    print(f"\ritreation:{idx+1}/{total_num} "
    f"[{'▓' * round((idx+1)/total_num*60)} "
    f"{(idx+1)/total_num*100:2.0f}% "
    f"{'-' * (60 - round((idx+1)/total_num*60))}] "
    f"{elapsed_time:.2f}s "
    f"ETA: {remaining_time/60:.2f}m", end="")


def main(max_workers=20):
    logging.basicConfig(filename=LOG_PATH,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
    
    start_time = time.time()
    df = pd.read_csv(DATA_PATH, index_col=None, header=0).values.reshape(-1).tolist()
    len_df = len(df)
    temp_res = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, res in enumerate(executor.map(question_answer, df)):
            temp_res.append(res["result"])
            print_time(idx, len_df, start_time)
            logging.info(f"第{idx+1}/{len_df}个信息为：{res}")
            if (len(temp_res) == 50) or ((idx+1) == len_df):
                print('\n',temp_res)
                append_row_to_csv(temp_res)
                temp_res = []


if __name__ == "__main__":
    main(max_workers=30)
    print('\nFinish')

