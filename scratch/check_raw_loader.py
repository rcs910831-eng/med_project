file_path = r'c:\Users\rcs91\github\med_project\modules\dataset_loader.py'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(len(lines)-5, len(lines)):
    print(f"{i+1}: {repr(lines[i])}")
