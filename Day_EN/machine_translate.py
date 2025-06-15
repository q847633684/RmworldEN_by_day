import csv
import time
import re
import logging
from typing import Optional

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkalimt.request.v20181012.TranslateGeneralRequest import TranslateGeneralRequest
except ImportError:
    AcsClient = None
    TranslateGeneralRequest = None

def aliyun_translate(text: str, client, from_lang: str = 'en', to_lang: str = 'zh') -> str:
    """
    使用阿里云机器翻译API翻译文本，保留[xxx]占位符。
    """
    parts = re.split(r'(\[[^\]]+\])', text)
    translated_parts = []
    for part in parts:
        if re.fullmatch(r'\[[^\]]+\]', part):
            translated_parts.append(part)
        elif part.strip():
            request = TranslateGeneralRequest()
            request.set_SourceLanguage(from_lang)
            request.set_TargetLanguage(to_lang)
            request.set_SourceText(part)
            request.set_FormatType('text')
            try:
                response = client.do_action_with_exception(request)
                response_str = str(response, encoding='utf-8')
                import json
                result = json.loads(response_str)
                zh = result.get('Data', {}).get('Translated', '')
                translated_parts.append(zh)
            except Exception as e:
                logging.error(f"翻译失败: {part}，错误: {e}")
                translated_parts.append(part)
        else:
            translated_parts.append(part)
    return ''.join(translated_parts)

def translate_csv(input_path: str, output_path: str, access_key_id: str, access_secret: str, region_id: str = 'cn-hangzhou', sleep_sec: float = 0.5) -> None:
    """
    批量翻译CSV文件，写入output_path，新增一列“翻译”。
    """
    if AcsClient is None or TranslateGeneralRequest is None:
        raise ImportError('请先安装 aliyun-python-sdk-core 和 aliyun-python-sdk-alimt')
    if not input_path:
        input_path = "extracted_translations.csv"
    if not output_path:
        output_path = "translated_zh.csv"
    logging.info(f"翻译 CSV: 从 {input_path} 到 {output_path}")
    client = AcsClient(access_key_id, access_secret, region_id)
    try:
        with open(input_path, 'r', encoding='utf-8') as infile, \
             open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            header = next(reader)
            writer.writerow(header + ['translated'])
            line_num = 1
            for row in reader:
                if len(row) < 2:
                    writer.writerow(row + [''])
                    line_num += 1
                    continue
                key, text = row[0], row[1]
                if text.strip() == '' or key.strip() == '':
                    writer.writerow(row + [''])
                    line_num += 1
                    continue
                if re.fullmatch(r'(\s*\[[^\]]+\]\s*)+', text):
                    writer.writerow(row + [text])
                    line_num += 1
                    continue
                zh = aliyun_translate(text, client)
                if not zh or zh.strip() == '':
                    logging.warning(f"第{line_num}行翻译失败。原文：{text}  翻译：{zh}")
                    writer.writerow(row + [''])
                else:
                    writer.writerow(row + [zh])
                    logging.debug(f"第{line_num}行翻译完成：原文：{text} => 翻译：{zh}")
                line_num += 1
                time.sleep(sleep_sec)
    except FileNotFoundError as e:
        logging.error(f"CSV 文件未找到: {input_path}，错误: {e}")
    except csv.Error as e:
        logging.error(f"CSV 解析失败: {input_path}，错误: {e}")