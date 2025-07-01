from typing import List, Tuple, Any

class SmartMerger:
    def __init__(self, input_data: List[tuple], output_data: List[tuple]):
        """
        初始化时：
        - 自动补齐为五元组 (key, test, tag, rel_path, en_test)
        - 统一规范化 key（去除 DefType/ 前缀）
        """
        self.input_data = [self._normalize_tuple(item) for item in input_data]
        self.output_data = [self._normalize_tuple(item) for item in output_data]
        self.input_map = {item[0]: item for item in self.input_data}
        self.output_map = {item[0]: item for item in self.output_data}

    def _normalize_tuple(self, item: tuple) -> Tuple[str, Any, Any, Any, Any]:
        # 补齐为五元组，并规范化 key
        key = self._normalize_key(item[0])
        if len(item) == 4:
            return (key, item[1], item[2], item[3], item[1])  # en_test 用 test 填充
        elif len(item) == 5:
            return (key, item[1], item[2], item[3], item[4])
        else:
            raise ValueError(f"不支持的元组长度: {len(item)}，内容: {item}")

    def _normalize_key(self, key: str) -> str:
        # 去除 DefType/ 前缀
        return key.split('/', 1)[-1] if '/' in key else key

    def smart_merge_definjected_translations(self) -> List[Tuple[str, Any, Any, Any, Any, Any]]:
        """
        智能合并 DefInjected 翻译：
        - 输入、输出均为五元组(key, test, tag, rel_path, en_test)
        - 返回六元组(key, test, tag, rel_path, en_test, history)
        - 自动跳过非 DefInjected 数据（如 Keyed 四元组）
        """
        merged = []
        for key, in_item in self.input_map.items():
            out_item = self.output_map.get(key)
            if out_item:
                if in_item[1] == out_item[4]:  # test == en_test
                    continue  # 不变
                else:
                    merged.append((
                        key, in_item[1], in_item[2], in_item[3], out_item[4], out_item[1]  # key, test, tag, rel_path, en_test, history
                    ))
            else:
                merged.append((
                    key, in_item[1], in_item[2], in_item[3], in_item[1], ""  # 新增，history为空
                ))
        return merged