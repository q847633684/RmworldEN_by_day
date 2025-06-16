import csv
import logging
import os
import re
import time
from typing import List, Dict
from pathlib import Path

try:
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkalimt.request.v20181012 import TranslateGeneralRequest
except ImportError:
    logging.warning("阿里云 SDK 未安装，机器翻译功能不可用。请运行：pip install aliyun-python-sdk-core aliyun-python-sdk-alimt")
    AcsClient = None
    TranslateGeneralRequest = None

def translate_text(text: str, access_key_id: str, access_secret: str, region_id: str = 'cn-hangzhou') -> str:
    """使用阿里云翻译 API 翻译文本，保留 [xxx] 占位符"""
    if AcsClient is None or TranslateGeneralRequest is None:
        raise RuntimeError("阿里云 SDK 未安装，无法进行机器翻译")
    
    # 检查是否只包含占位符
    if re.fullmatch(r'(\s*\[[^\]]+\]\s*)+', text):
        return text
    
    try:
        # 分割文本，保留占位符
        parts = re.split(r'(\[[^\]]+\])', text)
        translated_parts = []
        
        client = AcsClient(access_key_id, access_secret, region_id)
        
        for part in parts:
            if re.fullmatch(r'\[[^\]]+\]', part):
                # 这是占位符，直接保留
                translated_parts.append(part)
            elif part.strip():
                # 这是需要翻译的文本
                request = TranslateGeneralRequest()
                request.set_accept_format("json")
                request.set_SourceLanguage("en")
                request.set_TargetLanguage("zh")
                request.set_SourceText(part)
                response = client.do_action_with_exception(request)
                import json
                result = json.loads(response)
                translated_text = result.get("Data", {}).get("Translated", part)
                translated_parts.append(translated_text)
            else:
                # 空白部分
                translated_parts.append(part)
        
        return ''.join(translated_parts)
        
    except Exception as e:
        logging.error(f"翻译失败: {text}, 错误: {e}")
        return text

def translate_csv(input_path: str, output_path: str = None, **kwargs) -> None:
    """翻译 CSV 文件 - 统一接口"""
    if output_path is None:
        # 自动生成输出路径
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_translated{input_file.suffix}")
    
    # 从环境变量或配置获取 API 密钥
    access_key_id = kwargs.get('access_key_id') or os.getenv('ALIYUN_ACCESS_KEY_ID')
    access_secret = kwargs.get('access_secret') or os.getenv('ALIYUN_ACCESS_SECRET')
    
    if not access_key_id or not access_secret:
        print("❌ 缺少阿里云 API 密钥，请设置环境变量或传入参数")
        print("设置方法：")
        print("  export ALIYUN_ACCESS_KEY_ID='your_key'")
        print("  export ALIYUN_ACCESS_SECRET='your_secret'")
        return
    
    region_id = kwargs.get('region_id', 'cn-hangzhou')
    sleep_sec = kwargs.get('sleep_sec', 0.5)
    
    logging.info(f"翻译 CSV: input={input_path}, output={output_path}, region_id={region_id}")
    
    if not os.path.exists(input_path):
        logging.error(f"输入 CSV 文件不存在: {input_path}")
        print(f"❌ 文件不存在: {input_path}")
        return
    
    try:
        rows: List[Dict[str, str]] = []
        
        with open(input_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "text" not in reader.fieldnames:
                logging.error(f"CSV 文件缺少 'text' 列: {input_path}")
                print(f"❌ CSV 文件缺少 'text' 列")
                return
            
            total_rows = sum(1 for _ in reader)
            f.seek(0)
            reader = csv.DictReader(f)
            next(reader)  # 跳过表头
            
            print(f"开始翻译 {total_rows} 条记录...")
            
            for line_num, row in enumerate(reader, 2):  # 从第2行开始计数
                text = row["text"].strip()
                if not text:
                    row["translated"] = ""
                elif re.fullmatch(r'(\s*\[[^\]]+\]\s*)+', text):
                    # 只包含占位符，不翻译
                    row["translated"] = text
                else:
                    try:
                        translated = translate_text(text, access_key_id, access_secret, region_id)
                        row["translated"] = translated
                        if translated and translated.strip():
                            print(f"✅ 第{line_num}行: {text[:30]}... => {translated[:30]}...")
                        else:
                            print(f"⚠️ 第{line_num}行翻译为空: {text[:50]}...")
                            logging.warning(f"第{line_num}行翻译失败。原文：{text}")
                    except Exception as e:
                        logging.error(f"第{line_num}行翻译异常: {e}")
                        row["translated"] = text  # 翻译失败时保留原文
                
                rows.append(row)
                time.sleep(sleep_sec)  # 速率控制
                
        # 写入结果
        output_dir = os.path.dirname(output_path) or "."
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8", newline="") as f:
            if rows:
                fieldnames = rows[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
        
        logging.info(f"翻译完成，保存到: {output_path}")
        print(f"🎉 翻译完成，保存到: {output_path}")
        
    except Exception as e:
        logging.error(f"翻译过程出错: {e}")
        print(f"❌ 翻译失败: {e}")