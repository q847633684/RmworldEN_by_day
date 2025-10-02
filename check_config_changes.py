
import json
from pathlib import Path
from datetime import datetime
from user_config import UserConfigManager

def get_config_snapshot():
    config_manager = UserConfigManager()
    aliyun_api = config_manager.api_manager.get_api('aliyun')
    
    summary = config_manager.get_config_summary()
    config_file = summary.get('config_file')
    
    snapshot = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config_file_exists': Path(config_file).exists() if config_file else False,
        'config_file_size': Path(config_file).stat().st_size if config_file and Path(config_file).exists() else 0,
        'aliyun_enabled': aliyun_api.is_enabled(),
        'aliyun_complete': aliyun_api.is_complete(),
        'aliyun_valid': aliyun_api.validate(),
        'access_key_id_length': len(aliyun_api.get_value('access_key_id', '')),
        'access_key_secret_length': len(aliyun_api.get_value('access_key_secret', '')),
    }
    
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                aliyun_config = config_data.get('api', {}).get('apis', {}).get('aliyun', {})
                snapshot['file_enabled'] = aliyun_config.get('enabled', False)
                snapshot['file_access_key_id'] = aliyun_config.get('access_key_id', '')
                snapshot['file_access_key_secret'] = aliyun_config.get('access_key_secret', '')
        except Exception as e:
            snapshot['file_read_error'] = str(e)
    
    return snapshot

def compare_snapshots():
    try:
        # 读取初始快照
        with open('config_snapshot_initial.json', 'r', encoding='utf-8') as f:
            initial = json.load(f)
        
        # 获取当前快照
        current = get_config_snapshot()
        
        print(' 配置变化检测结果:')
        print('=' * 50)
        
        changes_found = False
        
        for key in initial.keys():
            if key == 'timestamp':
                continue
                
            initial_value = initial.get(key)
            current_value = current.get(key)
            
            if initial_value != current_value:
                changes_found = True
                if 'secret' in key.lower():
                    initial_display = f'{len(initial_value)} 字符' if isinstance(initial_value, str) else initial_value
                    current_display = f'{len(current_value)} 字符' if isinstance(current_value, str) else current_value
                else:
                    initial_display = initial_value
                    current_display = current_value
                
                print(f' {key}:')
                print(f'   之前: {initial_display}')
                print(f'   现在: {current_display}')
        
        if not changes_found:
            print(' 没有检测到配置变化')
        
        # 保存当前快照
        with open('config_snapshot_current.json', 'w', encoding='utf-8') as f:
            json.dump(current, f, indent=2, ensure_ascii=False)
        
        print(f'\n 当前状态已保存到: config_snapshot_current.json')
        
    except FileNotFoundError:
        print(' 未找到初始快照文件，请先运行监控工具')
    except Exception as e:
        print(f' 检测失败: {e}')

if __name__ == '__main__':
    compare_snapshots()
