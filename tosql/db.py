import sqlite3


def create_table():
    conn = sqlite3.connect('/data/xmj/材料库/attribute.db')
    cursor = conn.cursor()
    # 创建跑成功了的表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS success (
        id TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        product_model TEXT NOT NULL,
        attribute TEXT NOT NULL     
                   )
    ''')

    # 创建跑失败了的表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fail (
        id TEXT PRIMARY KEY,
        product_name TEXT NOT NULL,
        product_model TEXT NOT NULL,
        attribute TEXT NOT NULL
                   )
    ''')
    cursor.close()
    conn.close()
    print("数据库创建成功")


def insert_info(data, table_name="success"):
    conn = sqlite3.connect('/data/xmj/材料库/attribute.db')
    cursor = conn.cursor()
    cursor.executemany('INSERT OR REPLACE INTO ' + table_name + ' (id, product_name, product_model, attribute) VALUES (?, ?, ?, ?)', data)
    conn.commit()
    cursor.close()
    conn.close()


def check_product_id(product_id, table_name="success"):
    conn = sqlite3.connect('/data/xmj/材料库/attribute.db')
    cursor = conn.cursor()
    query = f"SELECT id FROM {table_name} WHERE id = ?"
    cursor.execute(query, (product_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if result:
        return True
    else:
        return False


def delete_info(product_id, table_name="success"):   
    conn = sqlite3.connect('/data/xmj/材料库/attribute.db')
    cursor = conn.cursor()
    query = f"DELETE FROM {table_name} WHERE id = ?"
    cursor.execute(query, (product_id,))
    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_table()

    # data_id_name_ls = [('1', 'product_name1', 'product_model1', 'brand_name1'), ('2', 'product_name2', 'product_model2', 'brand_name2')]
    # insert_info(data_id_name_ls, table_name="success")

    # product_id = '2'
    # print(check_product_id(product_id, table_name="success"))

    # delete_info(product_id, table_name="success")
    # print(check_product_id(product_id, table_name="fail"))
