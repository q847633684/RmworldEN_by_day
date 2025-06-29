"""
智能合并模块 - 实现翻译内容的智能合并功能
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from colorama import Fore, Style
from day_translation.utils.utils import XMLProcessor

class SmartMerger:
    """智能合并器 - 根据key和text差异进行智能合并"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.xml_processor = XMLProcessor()
    
    def merge_translation_files(self, existing_file_path: str, new_translations: Dict[str, str]) -> Dict[str, Any]:
        """
        智能合并翻译文件
        
        Args:
            existing_file_path (str): 现有翻译文件路径
            new_translations (Dict[str, str]): 新的翻译内容 {key: text}
            
        Returns:
            Dict[str, Any]: 合并结果统计
        """
        try:
            # 读取现有翻译文件
            existing_translations = self._parse_existing_xml(existing_file_path)
            
            # 执行智能合并
            merged_translations, changes = self._smart_merge(existing_translations, new_translations)
            
            # 生成新的XML内容
            merged_xml = self._generate_xml_content(merged_translations)
            
            # 写回文件
            with open(existing_file_path, 'w', encoding='utf-8') as f:
                f.write(merged_xml)
            
            # 返回处理结果
            return {
                'success': True,
                'file_path': existing_file_path,
                'changes': changes,
                'total_existing': len(existing_translations),
                'total_new': len(new_translations),
                'total_merged': len(merged_translations)
            }
            
        except Exception as e:
            self.logger.error(f"合并翻译文件失败: {existing_file_path}, 错误: {e}")
            return {
                'success': False,
                'file_path': existing_file_path,
                'error': str(e)
            }
    
    def _parse_existing_xml(self, file_path: str) -> Dict[str, str]:
        """
        解析现有XML文件，提取翻译内容
        
        Args:
            file_path (str): XML文件路径
            
        Returns:
            Dict[str, str]: {key: text} 翻译字典
        """
        translations = {}
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            for element in root.findall('.//'):
                if element.text and element.text.strip():
                    key = element.tag
                    text = element.text.strip()
                    translations[key] = text
                    
        except ET.ParseError as e:
            self.logger.warning(f"解析XML文件失败: {file_path}, 错误: {e}")
        except Exception as e:
            self.logger.error(f"读取文件失败: {file_path}, 错误: {e}")
            
        return translations
    
    def _smart_merge(self, existing_translations: Dict[str, str], new_translations: Dict[str, str]) -> Tuple[Dict[str, str], Dict[str, List]]:
        """
        执行智能合并逻辑
        
        合并规则：
        1. key相同，text不同 → 替换（用新翻译替换旧翻译）
        2. key不存在 → 添加（新增翻译条目）
        3. key相同，text相同 → 保持不变（跳过处理）
        
        Args:
            existing_translations (Dict[str, str]): 现有翻译 {key: text}
            new_translations (Dict[str, str]): 新翻译 {key: text}
            
        Returns:
            Tuple[Dict[str, str], Dict[str, List]]: (合并后的翻译, 变更统计)
        """
        merged_translations = existing_translations.copy()
        changes = {
            'replaced': [],  # 替换的翻译
            'added': [],     # 新增的翻译
            'unchanged': []  # 保持不变的翻译
        }
        
        for key, new_text in new_translations.items():
            if key in existing_translations:
                existing_text = existing_translations[key]
                if existing_text != new_text:
                    # key相同，text不同 → 替换
                    merged_translations[key] = new_text
                    changes['replaced'].append({
                        'key': key,
                        'old': existing_text,
                        'new': new_text
                    })
                else:
                    # key相同，text相同 → 保持不变
                    changes['unchanged'].append(key)
            else:
                # key不存在 → 添加
                merged_translations[key] = new_text
                changes['added'].append(key)
        
        return merged_translations, changes
    
    def _generate_xml_content(self, translations: Dict[str, str]) -> str:
        """
        生成XML内容
        
        Args:
            translations (Dict[str, str]): 翻译字典 {key: text}
            
        Returns:
            str: XML字符串
        """
        root = ET.Element('LanguageData')
        
        for key, text in sorted(translations.items()):
            element = ET.SubElement(root, key)
            element.text = text
        
        # 使用XMLProcessor生成格式化的XML
        tree = ET.ElementTree(root)
        
        # 创建临时文件来获取格式化的XML内容
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as temp_file:
            temp_path = temp_file.name
        
        try:
            # 使用XMLProcessor保存格式化XML
            success = self.xml_processor.save_xml(tree, temp_path, pretty_print=True)
            if success:
                # 读取格式化后的内容
                with open(temp_path, 'r', encoding='utf-8') as f:
                    formatted_xml = f.read()
                return formatted_xml
            else:
                # 如果XMLProcessor失败，回退到手动格式化
                return self._fallback_generate_xml(translations)
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def _fallback_generate_xml(self, translations: Dict[str, str]) -> str:
        """
        回退的XML生成方法
        
        Args:
            translations (Dict[str, str]): 翻译字典 {key: text}
            
        Returns:
            str: XML字符串
        """
        formatted_lines = ['<?xml version="1.0" encoding="utf-8"?>', '<LanguageData>']
        
        for key, text in sorted(translations.items()):
            formatted_lines.append(f'  <{key}>{text}</{key}>')
        
        formatted_lines.append('</LanguageData>')
        
        return '\n'.join(formatted_lines)
    
    def merge_multiple_files(self, file_mappings: List[Tuple[str, Dict[str, str]]]) -> Dict[str, Any]:
        """
        批量合并多个文件
        
        Args:
            file_mappings (List[Tuple[str, Dict[str, str]]]): [(文件路径, 新翻译内容), ...]
            
        Returns:
            Dict[str, Any]: 批量合并结果
        """
        results = {
            'total_files': len(file_mappings),
            'success_count': 0,
            'failed_count': 0,
            'file_results': [],
            'summary': {
                'total_replaced': 0,
                'total_added': 0,
                'total_unchanged': 0
            }
        }
        
        for file_path, new_translations in file_mappings:
            result = self.merge_translation_files(file_path, new_translations)
            results['file_results'].append(result)
            
            if result['success']:
                results['success_count'] += 1
                # 累计统计
                changes = result['changes']
                results['summary']['total_replaced'] += len(changes['replaced'])
                results['summary']['total_added'] += len(changes['added'])
                results['summary']['total_unchanged'] += len(changes['unchanged'])
            else:
                results['failed_count'] += 1
        
        return results
    
    def print_merge_summary(self, result: Dict[str, Any]) -> None:
        """
        打印合并结果摘要
        
        Args:
            result (Dict[str, Any]): 合并结果
        """
        if not result['success']:
            print(f"{Fore.RED}❌ 合并失败: {result['file_path']}")
            print(f"   错误: {result['error']}{Style.RESET_ALL}")
            return
        
        changes = result['changes']
        print(f"{Fore.GREEN}✅ 合并完成: {result['file_path']}{Style.RESET_ALL}")
        
        if changes['replaced']:
            print(f"   {Fore.YELLOW}🔄 替换: {len(changes['replaced'])} 个翻译{Style.RESET_ALL}")
            for change in changes['replaced'][:3]:  # 只显示前3个
                print(f"     {change['key']}: '{change['old']}' → '{change['new']}'")
            if len(changes['replaced']) > 3:
                print(f"     ... 还有 {len(changes['replaced']) - 3} 个")
        
        if changes['added']:
            print(f"   {Fore.GREEN}➕ 新增: {len(changes['added'])} 个翻译{Style.RESET_ALL}")
            for key in changes['added'][:3]:  # 只显示前3个
                print(f"     {key}")
            if len(changes['added']) > 3:
                print(f"     ... 还有 {len(changes['added']) - 3} 个")
        
        if changes['unchanged']:
            print(f"   {Fore.BLUE}⏭️ 保持: {len(changes['unchanged'])} 个翻译（无变化）{Style.RESET_ALL}")
        
        print(f"   总计: {result['total_merged']} 个翻译条目")
    
    def print_batch_summary(self, results: Dict[str, Any]) -> None:
        """
        打印批量合并结果摘要
        
        Args:
            results (Dict[str, Any]): 批量合并结果
        """
        print(f"\n{Fore.CYAN}=== 批量合并结果摘要 ==={Style.RESET_ALL}")
        print(f"📁 处理文件: {results['total_files']} 个")
        print(f"✅ 成功: {results['success_count']} 个")
        print(f"❌ 失败: {results['failed_count']} 个")
        
        summary = results['summary']
        print(f"\n📊 变更统计:")
        print(f"   🔄 替换: {summary['total_replaced']} 个翻译")
        print(f"   ➕ 新增: {summary['total_added']} 个翻译")
        print(f"   ⏭️ 保持: {summary['total_unchanged']} 个翻译")
        
        # 显示失败的文件
        failed_files = [r for r in results['file_results'] if not r['success']]
        if failed_files:
            print(f"\n{Fore.RED}❌ 失败的文件:{Style.RESET_ALL}")
            for result in failed_files:
                print(f"   {result['file_path']}: {result['error']}") 