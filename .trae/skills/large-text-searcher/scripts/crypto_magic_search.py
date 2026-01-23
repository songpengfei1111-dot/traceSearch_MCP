#!/usr/bin/env python3
"""
Cryptographic Magic Number Search Tool
基于010 Editor脚本的加密算法魔数搜索功能的Python实现
"""

import subprocess
import sys
from typing import List, Dict, Tuple, Optional

# 加密算法魔数定义 (基于010 Editor脚本)
CRYPTO_MAGIC_NUMBERS = {
    "MD5": [0xd76aa478, 0xe8c7b756, 0x242070db, 0xc1bdceee],
    "SHA1": [0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xCA62C1D6],
    "SHA256": [0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5],
    "SM3": [0x79cc4519, 0x7a879d8a],
    "CRC32": [0x77073096, 0xEE0E612C],
    "ChaCha20": [0x61707865, 0x3320646e],
    "HMAC": [0x36363636, 0x5C5C5C5C],
    "TEA": [0x9e3779b9],
    "Twofish": [0xBCBC3275, 0xECEC21F3, 0x202043C6, 0xB3B3C9F4],
    "Salsa20": [0x61707865, 0x3320646e, 0x79622d32, 0x6b206574],
    "Blowfish": [0x243f6a88, 0x85a308d3],
    "RC6": [0xb7e15163, 0x9e3779b9],
    "AES": [0xC66363A5, 0xF87C7C84],
    "APLib": [0x32335041],
    "RC4": [0x4F3B2B74, 0x4E27D213],
    "Threefish": [0x1B22B279, 0xAE23C8A4, 0xBC6F0C0D, 0x5E27A878],
    "Camellia": [0x4D49E62D, 0x934F19C8, 0x34E72602, 0xF75E005E],
    "Serpent": [0xC43FFF8B, 0x1D03D043, 0x1B2A04D0, 0x9AC28989],
    "AES_SBOX": [0x637C777B, 0xF26B6FC5, 0x3001672B, 0xFEFED7AB],
    "SHA256_K2": [0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5],
    "SHA512_IV": [0x6a09e667, 0xf3bcc908, 0xbb67ae85, 0x84caa73b],
    "Camellia_IV": [0xA09E667F, 0x3BCC908B, 0xB67AE858, 0x4CAA73B2],
    "Whirlpool_T0": [0x18186018, 0xC07830D8, 0x60281818, 0xD8181860],
    "Poly1305": [0xEB44ACC0, 0xD8DFB523],
    "DES": [0xFEE1A2B3, 0xD7BEF080],
    "DES1": [0x3A322A22, 0x2A223A32],
    "DES_SBOX": [0x2C1E241B, 0x5A7F361D, 0x3D4793C6, 0x0B0EEDF8]
}

EXECUTABLE_PATH = "./target/release/large-text-viewer"


def search_magic_number(file_path: str, magic_num: int, algorithm: str,
                       context: int = 2) -> Optional[Dict]:
    """
    搜索单个魔数

    Args:
        file_path: 文件路径
        magic_num: 魔数值
        algorithm: 算法名称
        context: 上下文行数

    Returns:
        搜索结果字典或None
    """
    # 转换为十六进制字符串 (大写，不带0x前缀)
    hex_pattern = f"{magic_num:X}"

    # 构建搜索命令
    cmd = [
        EXECUTABLE_PATH, "search",
        "--file", file_path,
        "--pattern", hex_pattern,
        "--context", str(context)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout

        if "matches" in output and "Showed 0 matches" not in output:
            # 提取第一个匹配的行号
            lines = output.split('\n')
            first_line_num = None
            for line in lines:
                if line.strip().startswith('>') and ':' in line:
                    # 提取行号，格式如 ">   1995: 7787e87854 [34854]"
                    try:
                        line_part = line.split(':')[0].strip().replace('>', '').strip()
                        first_line_num = int(line_part)
                        break
                    except (ValueError, IndexError):
                        continue

            return {
                "algorithm": algorithm,
                "magic_number": f"0x{hex_pattern}",
                "decimal_value": magic_num,
                "line_number": first_line_num,
                "search_result": output.strip()
            }
    except subprocess.CalledProcessError:
        pass

    return None


def search_all_crypto_magic(file_path: str) -> List[Dict]:
    """
    搜索所有加密算法魔数
    
    Args:
        file_path: 文件路径
    Returns:
        找到的魔数列表
    """
    results = []
    
    # 确定要搜索的算法
    search_algorithms = list(CRYPTO_MAGIC_NUMBERS.keys())
    
    for algorithm in search_algorithms:
        if algorithm not in CRYPTO_MAGIC_NUMBERS:
            continue
            
        magic_numbers = CRYPTO_MAGIC_NUMBERS[algorithm]
        
        for magic_num in magic_numbers:
            result = search_magic_number(file_path, magic_num, algorithm)
            if result:
                results.append(result)
                # 找到一个就跳到下一个算法 (模拟010 Editor脚本的search函数行为)
                break
    
    return results

def format_search_results(results: List[Dict]) -> str:
    """
    格式化搜索结果 - 使用简洁的010 Editor风格输出
    
    Args:
        results: 搜索结果列表
        
    Returns:
        格式化后的字符串
    """
    if not results:
        return "no magicnum found"
    
    output = []
    
    for result in results:
        line_info = f", line={result['line_number']}" if result.get('line_number') else ""
        if line_info:
            output.append(f"Find {result['algorithm']}, num:{result['magic_number']}{line_info}")
    
    return "\n".join(output)


def format_detailed_search_results(results: List[Dict]) -> str:
    """
    格式化详细搜索结果 - 包含完整的搜索上下文
    
    Args:
        results: 搜索结果列表
        
    Returns:
        格式化后的字符串
    """
    if not results:
        return "no magicnum found"
    
    output = ["***********Findcrypt Search Results****************"]
    
    for result in results:
        output.append(f"\n找到 {result['algorithm']} 算法魔数:")
        output.append(f"魔数: {result['magic_number']} (十进制: {result['decimal_value']})")
        if result.get('line_number'):
            output.append(f"行号: {result['line_number']}")
        output.append("搜索结果:")
        output.append(result['search_result'])
        output.append("-" * 50)
    
    output.append("***********Findcrypt Search Over****************")
    
    return "\n".join(output)


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("用法: python crypto_magic_search.py <file_path> [context] [algorithm1,algorithm2,...]")
        print("示例: python crypto_magic_search.py /path/to/file.txt 3 MD5,SHA256")
        sys.exit(1)
    
    file_path = sys.argv[1]
    # 搜索魔数
    results = search_all_crypto_magic(file_path)
    # 输出结果
    print(format_search_results(results))


if __name__ == "__main__":
    main()