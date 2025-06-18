#!/usr/bin/env python3
"""
配置迁移工具 - 将现有的分散配置迁移到统一配置系统
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any

def migrate_configurations():
    """迁移现有配置到统一配置系统"""
    print("🔄 开始配置迁移...")
    
    config_dir = Path.home() / ".day_translation"
    old_config_file = config_dir / "config.json"
    old_preferences_file = config_dir / "user_preferences.json"
    old_paths_file = config_dir / "remembered_paths.json"
    old_history_file = config_dir / "path_history.json"
    
    new_config_file = config_dir / "config.json"
    backup_dir = config_dir / "backup"
    
    # 创建备份目录
    backup_dir.mkdir(exist_ok=True)
    
    # 初始化新配置结构
    unified_config = {
        "version": "2.0.0",
        "core": {
            "default_language": "ChineseSimplified",
            "source_language": "English",
            "def_injected_dir": "DefInjected",
            "keyed_dir": "Keyed",
            "output_csv": "extracted_translations.csv",
            "log_file": "",
            "log_format": "%(asctime)s - %(levelname)s - %(message)s",
            "debug_mode": False,
            "preview_transatable_fields": 0
        },
        "user": {
            "extraction": {
                "output_location": "external",
                "output_dir": None,
                "en_keyed_dir": None,
                "auto_detect_en_keyed": True,
                "auto_choose_definjected": False,
                "structure_choice": "original",
                "merge_mode": "smart-merge"
            },
            "import_prefs": {
                "merge_existing": True,
                "backup_before_import": True
            },
            "api": {
                "aliyun_access_key_id": "",
                "aliyun_access_key_secret": "",
                "save_api_keys": True
            },
            "general": {
                "remember_paths": True,
                "auto_mode": False,
                "confirm_operations": True
            },
            "remembered_paths": {},
            "path_history": {}
        }
    }
    
    migrated_data = []
    
    # 1. 迁移旧的 config.json (核心配置)
    if old_config_file.exists():
        try:
            with open(old_config_file, 'r', encoding='utf-8') as f:
                old_config = json.load(f)
            
            # 备份旧配置
            shutil.copy2(old_config_file, backup_dir / "config.json.backup")
            
            # 迁移核心配置
            core_mappings = {
                'default_language': 'default_language',
                'source_language': 'source_language',
                'def_injected_dir': 'def_injected_dir',
                'keyed_dir': 'keyed_dir',
                'output_csv': 'output_csv',
                'log_file': 'log_file',
                'log_format': 'log_format',
                'debug_mode': 'debug_mode',
                'preview_transatable_fields': 'preview_transatable_fields'
            }
            
            for old_key, new_key in core_mappings.items():
                if old_key in old_config:
                    unified_config["core"][new_key] = old_config[old_key]
                    migrated_data.append(f"核心配置: {old_key} -> core.{new_key}")
            
            # 迁移API密钥（如果在旧配置中）
            api_mappings = {
                'ALIYUN_ACCESS_KEY_ID': 'aliyun_access_key_id',
                'ALIYUN_ACCESS_KEY_SECRET': 'aliyun_access_key_secret'
            }
            
            for old_key, new_key in api_mappings.items():
                if old_key in old_config:
                    unified_config["user"]["api"][new_key] = old_config[old_key]
                    migrated_data.append(f"API配置: {old_key} -> user.api.{new_key}")
            
            print(f"✅ 迁移旧核心配置: {old_config_file}")
            
        except Exception as e:
            print(f"❌ 迁移旧核心配置失败: {e}")
    
    # 2. 迁移用户偏好 (user_preferences.json)
    if old_preferences_file.exists():
        try:
            with open(old_preferences_file, 'r', encoding='utf-8') as f:
                old_prefs = json.load(f)
            
            # 备份旧偏好
            shutil.copy2(old_preferences_file, backup_dir / "user_preferences.json.backup")
            
            # 迁移提取偏好
            if 'extraction' in old_prefs:
                extraction = old_prefs['extraction']
                extraction_mappings = {
                    'output_location': 'output_location',
                    'output_dir': 'output_dir',
                    'en_keyed_dir': 'en_keyed_dir',
                    'auto_detect_en_keyed': 'auto_detect_en_keyed',
                    'auto_choose_definjected': 'auto_choose_definjected',
                    'structure_choice': 'structure_choice',
                    'merge_mode': 'merge_mode'
                }
                
                for old_key, new_key in extraction_mappings.items():
                    if old_key in extraction:
                        unified_config["user"]["extraction"][new_key] = extraction[old_key]
                        migrated_data.append(f"提取偏好: {old_key} -> user.extraction.{new_key}")
            
            # 迁移导入偏好
            if 'import_prefs' in old_prefs:
                import_prefs = old_prefs['import_prefs']
                import_mappings = {
                    'merge_existing': 'merge_existing',
                    'backup_before_import': 'backup_before_import'
                }
                
                for old_key, new_key in import_mappings.items():
                    if old_key in import_prefs:
                        unified_config["user"]["import_prefs"][new_key] = import_prefs[old_key]
                        migrated_data.append(f"导入偏好: {old_key} -> user.import_prefs.{new_key}")
            
            # 迁移通用设置
            if 'general' in old_prefs:
                general = old_prefs['general']
                general_mappings = {
                    'remember_paths': 'remember_paths',
                    'auto_mode': 'auto_mode',
                    'confirm_operations': 'confirm_operations'
                }
                
                for old_key, new_key in general_mappings.items():
                    if old_key in general:
                        unified_config["user"]["general"][new_key] = general[old_key]
                        migrated_data.append(f"通用设置: {old_key} -> user.general.{new_key}")
            
            print(f"✅ 迁移用户偏好: {old_preferences_file}")
            
        except Exception as e:
            print(f"❌ 迁移用户偏好失败: {e}")
    
    # 3. 迁移记住的路径 (remembered_paths.json)
    if old_paths_file.exists():
        try:
            with open(old_paths_file, 'r', encoding='utf-8') as f:
                old_paths = json.load(f)
            
            # 备份旧路径
            shutil.copy2(old_paths_file, backup_dir / "remembered_paths.json.backup")
            
            unified_config["user"]["remembered_paths"] = old_paths
            migrated_data.append(f"记住的路径: {len(old_paths)} 个路径 -> user.remembered_paths")
            
            print(f"✅ 迁移记住的路径: {old_paths_file}")
            
        except Exception as e:
            print(f"❌ 迁移记住的路径失败: {e}")
    
    # 4. 迁移路径历史 (path_history.json)
    if old_history_file.exists():
        try:
            with open(old_history_file, 'r', encoding='utf-8') as f:
                old_history = json.load(f)
            
            # 备份旧历史
            shutil.copy2(old_history_file, backup_dir / "path_history.json.backup")
            
            unified_config["user"]["path_history"] = old_history
            migrated_data.append(f"路径历史: {len(old_history)} 个类型 -> user.path_history")
            
            print(f"✅ 迁移路径历史: {old_history_file}")
            
        except Exception as e:
            print(f"❌ 迁移路径历史失败: {e}")
    
    # 5. 保存新的统一配置
    try:
        with open(new_config_file, 'w', encoding='utf-8') as f:
            json.dump(unified_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 统一配置已保存: {new_config_file}")
        print("🎉 配置迁移完成！")
        return True
        
    except Exception as e:
        print(f"❌ 保存统一配置失败: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        # rollback_migration()
        pass
    else:
        print("Day Translation 配置迁移工具")
        print("这将把现有的分散配置文件合并为统一配置")
        print("旧配置文件将被备份到 backup/ 目录")
        
        confirm = input("\n是否开始迁移？[y/N]: ").strip().lower()
        if confirm in ['y', 'yes']:
            migrate_configurations()
        else:
            print("迁移已取消")
    """回滚配置迁移"""
    print("🔄 开始配置回滚...")
    
    config_dir = Path.home() / ".day_translation"
    backup_dir = config_dir / "backup"
    
    if not backup_dir.exists():
        print("❌ 未找到备份目录，无法回滚")
        return False
    
    backup_files = [
        ("config.json.backup", "config.json"),
        ("user_preferences.json.backup", "user_preferences.json"),
        ("remembered_paths.json.backup", "remembered_paths.json"),
        ("path_history.json.backup", "path_history.json")
    ]
    
    restored_count = 0
    for backup_name, restore_name in backup_files:
        backup_file = backup_dir / backup_name
        restore_file = config_dir / restore_name
        
        if backup_file.exists():
            try:
                shutil.copy2(backup_file, restore_file)
                print(f"✅ 已恢复: {restore_name}")
                restored_count += 1
            except Exception as e:
                print(f"❌ 恢复失败 {restore_name}: {e}")
    
    if restored_count > 0:
        print(f"🎉 配置回滚完成！已恢复 {restored_count} 个文件")
        return True
    else:
        print("❌ 没有找到可恢复的配置文件")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--rollback":
        rollback_migration()
    else:
        print("Day Translation 配置迁移工具")
        print("这将把现有的分散配置文件合并为统一配置")
        print("旧配置文件将被备份到 backup/ 目录")
        
        confirm = input("\n是否开始迁移？[y/N]: ").strip().lower()
        if confirm in ['y', 'yes']:
            if migrate_configurations():
                print("\n提示：如果需要回滚，请运行: python migrate_config.py --rollback")
            else:
                print("\n迁移过程中发生错误，请检查日志")
        else:
            print("迁移已取消")
