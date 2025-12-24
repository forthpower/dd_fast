import csv
import os

path = os.path.join(os.path.dirname(__file__), 'compare_result_final.csv')

# 读取所有行
rows_to_keep = []
existing_records = []
with open(path, 'r', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    for row in reader:
        # 保留不满足删除条件的行
        # if row['real_db_value'] == 'UNKNOWN':
        #     row['real_db_value'] = None
        if [row['order_id'], row['field']] not in existing_records:
            rows_to_keep.append(row)
            existing_records.append([row['order_id'], row['field']])
        

# 写回文件
with open(path, 'w', encoding="utf-8", newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows_to_keep)

print(f"已删除满足条件的行，剩余 {len(rows_to_keep)} 行")


