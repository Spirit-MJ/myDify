from openai import OpenAI
from pydantic import BaseModel, create_model, Field
from typing import List
import json
import datasets
import sqlite3
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from db import check_product_id, insert_info
from prompt_template import template_prompt


LLM_API = "*****"
# LLM_MODEL = "Qwen2.5-72B-Instruct"
LLM_MODEL = "****"
LLM_KEY = "****"
DATA_PATH = "./in_standard.parquet"
LOG_PATH = "./logs/1205.log"


class LLM:
    def __init__(self):
        self.client = OpenAI(
                            base_url = LLM_API,
                            api_key = LLM_KEY)
        
    def get_response(self, sys_prompt, user_prompt, json_schema):
        completion = self.client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{"role": "system", "content": sys_prompt},
                              {"role": "user", "content": user_prompt}],
                    extra_body={"guided_json": json_schema},
                    )
        response = completion.choices[0].message.content
        return response


class QuestionAns:
    def __init__(self):
        self.llm = LLM()

    def get_answer(self, origin_inputs):
        inputs = origin_inputs["product_name"] + " " + origin_inputs["product_model"]
        class_name1 = origin_inputs["class_name_first"].strip().lower()
        class_name2 = origin_inputs["class_name_second"].strip().lower()
        class_name3 = origin_inputs["class_name_third"].strip().lower()
        class_name4 = origin_inputs["class_name_fourth"].strip().lower()
        inputs_attr = origin_inputs["attribute"].strip().lower()
        class_name = f"{class_name1}<;>{class_name2}<;>{class_name3}<;>{class_name4}"
        if class_name == "墙面、天棚及屋面饰面材料<;>其它装饰板<;>其它装饰板<;>其它装饰板":
            return self.result_success_process(origin_inputs["id"],
                                        origin_inputs["product_name"],
                                        origin_inputs["product_model"],
                                        class_name1,
                                        class_name2,
                                        class_name3,
                                        class_name4,
                                        inputs_attr
                                        )
        json_template = self.db_search_attr(class_name)
        Attr = self.create_attr_from_class_dict(json.loads(json_template))
        sys_prompt, usr_prompt = template_prompt(inputs, inputs_attr, json_template)
        try:
            attr_str = self.llm.get_response(sys_prompt, usr_prompt, Attr.model_json_schema())
            attr_dict = json.loads(attr_str)
            res_attr = {k: v if v != 'null' else '' for k, v in attr_dict.items()}
            res = self.result_success_process(origin_inputs["id"],
                                        origin_inputs["product_name"],
                                        origin_inputs["product_model"],
                                        class_name1,
                                        class_name2,
                                        class_name3,
                                        class_name4,
                                        res_attr
                                        )
        except Exception as e:
            logging.error(f"question_answer error: {e}")
            print(f"question_answer error: {e}")
            res = self.result_fail_process(origin_inputs["id"],
                                    origin_inputs["product_name"],
                                    origin_inputs["product_model"],)
        return res
    
    def create_attr_from_class_dict(self, data: dict) -> type:
        fields = {}
        for key, value in data.items():
            if value[0] == '[' and value[-1] == ']':
                fields[key] = (List[str], Field(...))
            else:
                fields[key] = (str, Field(...))
        DynamicAttribute = create_model('DynamicAttribute', **fields, __base__=BaseModel)
        return DynamicAttribute
    
    def db_search_attr(self, classify_name):
        conn = sqlite3.connect('/data/xmj/材料库/class_attr.db')
        cursor = conn.cursor()
        query = f"SELECT attribute FROM material WHERE class_name=?;"
        cursor.execute(query, (classify_name,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0]
    
    def result_success_process(self, data_id, product_name, product_model, class_name_first,
                           class_name_second, class_name_third, class_name_fourth, attribute):
        return {
                'id': f"v3{data_id[2:]}", 
                'product_name': product_name,
                'product_model': product_model, 
                'brand_name': "<null>",
                'class_name_first': class_name_first, 
                'class_name_second': class_name_second, 
                'class_name_third': class_name_third, 
                'class_name_fourth': class_name_fourth, 
                'attribute': json.dumps(attribute, ensure_ascii=False)
                }

    def result_fail_process(self, data_id, product_name, product_model):
        return {
                'id': f"v3{data_id[2:]}", 
                'product_name': product_name,
                'product_model': product_model,
                'attribute': "<null>"
                } 


def print_time(idx, res_num, total_num, start_time):
    elapsed_time = time.time() - start_time
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)    
    avg_time = (time.time() - start_time) / (idx+1)

    remaining_time = avg_time * (res_num - idx + 1)
    remaining_hours = int(remaining_time // 3600)
    remaining_minutes = int((remaining_time % 3600) // 60)
    remaining_seconds = int(remaining_time % 60) 
    start_idx = total_num - res_num + 1
    print(f'已完成:{start_idx+idx}/{total_num}, 已用时{hours}h {minutes}m {seconds}s, 大约剩余{remaining_hours}h {remaining_minutes}m {remaining_seconds}s') 


def main(max_workers=1):

    logging.basicConfig(filename=LOG_PATH,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
                    level=logging.INFO)
    logger = logging.getLogger()
    question_answer = QuestionAns()

    ds = datasets.Dataset.from_parquet(DATA_PATH)
    len_ds = len(ds)

    res_data = []
    for data in ds:
        data_id = "v3" + data["id"][2:]
        if not check_product_id(data_id, table_name="success"):
            res_data.append(data)

    print("数据构造完成")
    len_res_data = len(res_data)
    start_idx = len_ds - len_res_data + 1
    start_time = time.time()

    success_ls, fail_ls, res_succes = [], [], []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for idx, res in enumerate(executor.map(question_answer.get_answer, res_data)):
            if len(res.keys()) == 4:
                fail_ls.append((res["id"], res["product_name"], res["product_model"], res["attribute"]))
            else:
                success_ls.append((res["id"], res["product_name"], res["product_model"], res["attribute"]))
                res_succes.append(res)

            if (len(success_ls) % 50 == 0) or ((idx+1) == len_res_data):
                insert_info(success_ls, table_name="success")
                insert_info(fail_ls, table_name="fail")
                success_ls, res_succes = [], []
                print('数据成功写入')
                logger.handlers[0].flush()
            logger.info(f"第{start_idx+idx}/{len_ds}个样本的信息:\n {res}")
            print_time(idx, len_res_data, len_ds, start_time)


if __name__ == "__main__":
    main(max_workers=100)
    print("\nFinish!")
