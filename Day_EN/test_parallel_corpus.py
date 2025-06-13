"""
test_parallel_corpus.py
自动化测试 Day_EN.parallel_corpus 的核心功能。
"""
import os
from Day_EN import parallel_corpus

def test_extract_pairs_from_file():
    # 构造一个带 EN 注释的 xml 临时文件
    xml_content = '''
    <!-- EN: Hello -->
    <label>你好</label>
    <!-- EN: World -->
    <desc>世界</desc>
    '''
    tmp = 'tmp_test_en.xml'
    with open(tmp, 'w', encoding='utf-8') as f:
        f.write(xml_content)
    pairs = parallel_corpus.extract_pairs_from_file(tmp)
    os.remove(tmp)
    assert ('Hello', '你好') in pairs
    assert ('World', '世界') in pairs
    print('test_extract_pairs_from_file passed')

def test_extract_pairs_from_definjected():
    # 构造英文和中文 xml
    os.makedirs('tmp_en', exist_ok=True)
    os.makedirs('tmp_zh', exist_ok=True)
    with open('tmp_en/a.xml', 'w', encoding='utf-8') as f:
        f.write('<LanguageData><label>Hello</label><desc>World</desc></LanguageData>')
    with open('tmp_zh/a.xml', 'w', encoding='utf-8') as f:
        f.write('<LanguageData><label>你好</label><desc>世界</desc></LanguageData>')
    pairs = parallel_corpus.extract_pairs_from_definjected('tmp_en', 'tmp_zh')
    os.remove('tmp_en/a.xml')
    os.remove('tmp_zh/a.xml')
    os.rmdir('tmp_en')
    os.rmdir('tmp_zh')
    assert ('Hello', '你好') in pairs
    assert ('World', '世界') in pairs
    print('test_extract_pairs_from_definjected passed')

def test_check_parallel_tsv():
    # 构造一个合格和不合格的 tsv
    tsv_ok = 'a	b\nhello\t你好\n'
    tsv_bad = 'a\tb\tc\n\nhello\t\n'
    with open('tmp.tsv', 'w', encoding='utf-8') as f:
        f.write(tsv_ok)
    assert parallel_corpus.check_parallel_tsv('tmp.tsv') == 0
    with open('tmp.tsv', 'w', encoding='utf-8') as f:
        f.write(tsv_bad)
    assert parallel_corpus.check_parallel_tsv('tmp.tsv') > 0
    os.remove('tmp.tsv')
    print('test_check_parallel_tsv passed')

if __name__ == '__main__':
    test_extract_pairs_from_file()
    test_extract_pairs_from_definjected()
    test_check_parallel_tsv()
