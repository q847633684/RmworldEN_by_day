
import time
import json
from pathlib import Path
from datetime import datetime
from user_config import UserConfigManager

def get_config_snapshot():
    try:
        config_manager = UserConfigManager()
        aliyun_api = config_manager.api_manager.get_api('aliyun')
        
        summary = config_manager.get_config_summary()
        config_file = summary.get('config_file')
        
        snapshot = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'aliyun_enabled': aliyun_api.is_enabled(),
            'access_key_id_length': len(aliyun_api.get_value('access_key_id', '')),
            'access_key_secret_length': len(aliyun_api.get_value('access_key_secret', '')),
        }
        
        if config_file and Path(config_file).exists():
            snapshot['file_size'] = Path(config_file).stat().st_size
            
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    aliyun_config = config_data.get('api', {}).get('apis', {}).get('aliyun', {})
                    snapshot['file_enabled'] = aliyun_config.get('enabled', False)
            except:
                snapshot['file_enabled'] = None
        
        return snapshot
    except Exception as e:
        return {'error': str(e), 'timestamp': datetime.now().strftime('%H:%M:%S')}

def monitor_config():
    print(' 开始实时监控配置变化...')
    print('按 Ctrl+C 停止监控')
    print('=' * 50)
    
    last_snapshot = None
    
    try:
        while True:
            current_snapshot = get_config_snapshot()
            
            if 'error' in current_snapshot:
                print(f'{current_snapshot['timestamp']}  错误: {current_snapshot['error']}')
            else:
                if last_snapshot is None:
                    print(f'{current_snapshot['timestamp']}  初始状态: 启用={current_snapshot['aliyun_enabled']}, KeyId长度={current_snapshot['access_key_id_length']}, Secret长度={current_snapshot['access_key_secret_length']}')
                elif current_snapshot != last_snapshot:
                    print(f'{current_snapshot['timestamp']}  检测到变化!')
                    
                    for key in current_snapshot:
                        if key != 'timestamp' and current_snapshot[key] != last_snapshot.get(key):
                            print(f'    {key}: {last_snapshot.get(key)}  {current_snapshot[key]}')
                
                last_snapshot = current_snapshot.copy()
            
            time.sleep(2)  # 每2秒检查一次
            
    except KeyboardInterrupt:
        print('\n监控已停止')

if __name__ == '__main__':
    monitor_config()
