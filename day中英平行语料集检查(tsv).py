import sys

def check_tsv(file_path):
    with open(file_path, encoding='utf-8') as f:
        lines = f.readlines()

    errors = []
    for idx, line in enumerate(lines, 1):
        # 去除行尾换行符
        line = line.rstrip('\n\r')
        # 跳过空行
        if not line.strip():
            errors.append(f"第{idx}行是空行")
            continue
        cols = line.split('\t')
        if len(cols) != 2:
            errors.append(f"第{idx}行列数不是2列: {line}")
        if any(c.strip() == '' for c in cols):
            errors.append(f"第{idx}行有空单元格: {line}")
        for c in cols:
            if '\u3000' in c or '\u200b' in c:
                errors.append(f"第{idx}行含有异常字符: {line}")

    if errors:
        print("发现以下问题：")
        for e in errors:
            print(e)
    else:
        print("检查通过，未发现格式问题。")

if __name__ == "__main__":
    # 默认检查 parallel_corpus.tsv
    check_tsv('parallel_corpus.tsv')