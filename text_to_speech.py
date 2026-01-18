#!/usr/bin/env python3
"""
使用 edge-tts 将文本转换为 MP3 音频文件

使用方法:
1. 直接指定文本: python text_to_speech.py "你好，世界"
2. 自动读取文件: python text_to_speech.py input.txt
3. 批量处理目录: python text_to_speech.py -d ./video
4. 合并模式（增量生成+合并mp3）: python text_to_speech.py -d ./video --merge
5. 指定合并输出文件: python text_to_speech.py -d ./video --merge -o final.mp3
6. 指定语音: python text_to_speech.py "Hello" -v en-US-AriaNeural

合并模式说明:
- 第一步: 检查每个md是否有对应的mp3，没有的才生成（增量）
- 第二步: 合并所有mp3为一个最终文件（按时间命名）
- 需要安装: pip install pydub
"""

import asyncio
import argparse
import edge_tts
import os
from datetime import datetime


def read_text_until_separator(file_path: str) -> str:
    """
    读取文件内容直到遇到全是"-"的行（不包括该行）
    
    参数:
        file_path: 文件路径
    
    返回:
        提取的文本内容
    """
    lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # 检查是否是分隔线（全是"-"）
            stripped = line.strip()
            if stripped and all(c == '-' for c in stripped):
                break
            lines.append(line.rstrip('\n\r'))
    
    return '\n'.join(lines).strip()


async def text_to_speech(text: str, output_file: str, voice: str = "zh-CN-YunjianNeural"):
    """
    将文本转换为语音并保存为 MP3 文件
    
    参数:
        text: 要转换的文本
        output_file: 输出的 MP3 文件路径
        voice: 语音名称，默认为中文女声
    """
    print(f"正在生成语音...")
    print(f"文本: {text[:50]}{'...' if len(text) > 50 else ''}")
    print(f"语音: {voice}")
    print(f"输出: {output_file}")
    
    # 创建 TTS 对象
    communicate = edge_tts.Communicate(text, voice)
    
    # 保存为音频文件
    await communicate.save(output_file)
    
    file_size = os.path.getsize(output_file)
    print(f"✓ 生成成功! 文件大小: {file_size / 1024:.2f} KB")


async def process_directory(directory: str, voice: str, output_dir: str = None, merge: bool = False, merge_output: str = None):
    """
    批量处理目录中的所有 md 文件
    
    参数:
        directory: 输入目录路径
        voice: 语音名称
        output_dir: 输出目录（默认与输入目录相同）
        merge: 是否合并所有文件为一个 mp3
        merge_output: 合并模式下的输出文件名
    """
    if not os.path.exists(directory):
        print(f"错误: 目录 '{directory}' 不存在")
        return
    
    if not os.path.isdir(directory):
        print(f"错误: '{directory}' 不是一个目录")
        return
    
    # 获取所有 md 文件
    md_files = [f for f in os.listdir(directory) if f.endswith('.md')]
    
    if not md_files:
        print(f"在目录 '{directory}' 中未找到 .md 文件")
        return
    
    md_files.sort()  # 按文件名排序
    
    print(f"找到 {len(md_files)} 个 .md 文件")
    print("=" * 60)
    
    # 如果未指定输出目录，使用输入目录
    if output_dir is None:
        output_dir = directory
    else:
        os.makedirs(output_dir, exist_ok=True)
    
    # 第一步：为每个 md 生成对应的 mp3（如果不存在）
    mp3_files = []
    
    for idx, filename in enumerate(md_files, 1):
        input_path = os.path.join(directory, filename)
        
        # 生成输出文件名（保留原文件名，只改扩展名）
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(output_dir, f"{base_name}.mp3")
        
        mp3_files.append(output_file)
        
        # 检查 mp3 是否已存在
        if os.path.exists(output_file):
            print(f"\n[{idx}/{len(md_files)}] ✓ 已存在: {filename} -> {os.path.basename(output_file)}")
            continue
        
        print(f"\n[{idx}/{len(md_files)}] 生成: {filename}")
        
        try:
            # 读取文本（只到分隔线）
            text = read_text_until_separator(input_path)
            
            if not text:
                print(f"  ⚠ 跳过: 文件内容为空")
                continue
            
            print(f"  提取字符数: {len(text)}")
            
            # 生成语音
            await text_to_speech(text, output_file, voice)
            
        except Exception as e:
            print(f"  ✗ 错误: {e}")
            continue
    
    print("\n" + "=" * 60)
    print(f"✓ 音频文件准备完成！")
    
    # 第二步：如果是合并模式，合并所有 mp3
    if merge:
        # 过滤出实际存在的 mp3 文件
        existing_mp3s = [f for f in mp3_files if os.path.exists(f)]
        
        if not existing_mp3s:
            print("\n错误: 没有可用的 mp3 文件进行合并")
            return
        
        print(f"\n准备合并 {len(existing_mp3s)} 个音频文件...")
        
        # 确定最终输出文件
        if merge_output:
            final_output = merge_output
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            final_output = os.path.join(output_dir, f'merged_{timestamp}.mp3')
        
        # 确保输出目录存在
        final_output_dir = os.path.dirname(final_output)
        if final_output_dir and not os.path.exists(final_output_dir):
            os.makedirs(final_output_dir)
        
        try:
            # 尝试导入 pydub
            from pydub import AudioSegment
            
            print("正在合并音频文件（使用 pydub）...")
            
            # 合并所有音频
            combined = AudioSegment.empty()
            for idx, mp3_file in enumerate(existing_mp3s, 1):
                print(f"  [{idx}/{len(existing_mp3s)}] 添加: {os.path.basename(mp3_file)}")
                audio = AudioSegment.from_mp3(mp3_file)
                combined += audio
            
            # 导出合并后的音频
            print(f"\n正在导出合并文件...")
            combined.export(final_output, format="mp3")
            
            file_size = os.path.getsize(final_output)
            print(f"✓ 合并成功！")
            print(f"  输出文件: {final_output}")
            print(f"  文件大小: {file_size / 1024 / 1024:.2f} MB")
            
        except ImportError:
            print("\n⚠ 警告: 未安装 pydub 库")
            print("请运行: pip install pydub")
            print("\n或者，如果你已安装 ffmpeg，可以手动合并：")
            print(f"  ffmpeg -i \"concat:{'|'.join(existing_mp3s)}\" -acodec copy {final_output}")
            
        except Exception as e:
            print(f"\n✗ 合并失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"单独处理完成！共处理 {len(md_files)} 个文件")


async def list_voices():
    """列出所有可用的语音"""
    print("正在获取可用语音列表...\n")
    voices = await edge_tts.list_voices()
    
    # 按语言分组
    voices_by_lang = {}
    for voice in voices:
        lang = voice['Locale']
        if lang not in voices_by_lang:
            voices_by_lang[lang] = []
        voices_by_lang[lang].append(voice)
    
    # 显示常用语言
    common_langs = ['zh-CN', 'zh-TW', 'en-US', 'en-GB', 'ja-JP', 'ko-KR']
    
    for lang in common_langs:
        if lang in voices_by_lang:
            print(f"\n{lang} 语音:")
            for voice in voices_by_lang[lang]:
                gender = voice.get('Gender', 'Unknown')
                print(f"  - {voice['ShortName']}: {voice['FriendlyName']} ({gender})")


def main():
    parser = argparse.ArgumentParser(
        description='使用 edge-tts 将文本转换为 MP3 音频文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  单文件模式:
    %(prog)s "你好，这是一段测试文本"
    %(prog)s input.txt -o output.mp3
    %(prog)s "Hello World" -v en-US-AriaNeural
  
  批量处理模式（每个md生成一个mp3）:
    %(prog)s -d ./video
    %(prog)s -d ./video --output-dir ./mp3_output
  
  合并模式（增量生成各个mp3 + 合并）:
    %(prog)s -d ./video --merge
    %(prog)s -d ./video --merge -o final.mp3
    注意：需要先安装 pydub (pip install pydub)
  
  其他:
    %(prog)s --list-voices
        """
    )
    
    parser.add_argument('input', nargs='?', help='文本内容或文件路径（自动识别）')
    parser.add_argument('-d', '--directory', help='批量处理：指定包含 .md 文件的目录')
    parser.add_argument('-o', '--output', help='输出的 MP3 文件路径（默认: output_YYYYMMDD_HHMMSS.mp3）')
    parser.add_argument('--merge', action='store_true', help='合并模式：将目录中所有 md 文件合并为一个 mp3')
    parser.add_argument('--output-dir', help='批量处理模式下的输出目录（默认与输入目录相同）')
    parser.add_argument('-v', '--voice', default='zh-CN-YunjianNeural', 
                        help='语音名称（默认: zh-CN-YunjianNeural 中文男声）')
    parser.add_argument('--list-voices', action='store_true', help='列出所有可用的语音')
    
    args = parser.parse_args()
    
    # 列出语音
    if args.list_voices:
        asyncio.run(list_voices())
        return
    
    # 批量处理模式
    if args.directory:
        merge_output = args.output if args.merge else None
        asyncio.run(process_directory(args.directory, args.voice, args.output_dir, args.merge, merge_output))
        return
    
    # 单文件/文本模式
    if not args.input:
        parser.print_help()
        return
    
    # 自动识别输入是文件还是文本
    text = None
    if os.path.exists(args.input):
        # 如果是文件，读取文件内容（到分隔线为止）
        print(f"检测到文件: {args.input}")
        if args.input.endswith('.md'):
            text = read_text_until_separator(args.input)
        else:
            with open(args.input, 'r', encoding='utf-8') as f:
                text = f.read().strip()
    else:
        # 否则作为文本处理
        text = args.input
    
    if not text:
        print("错误: 文本内容为空")
        return
    
    # 生成输出文件名
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'output_{timestamp}.mp3'
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 执行转换
    try:
        asyncio.run(text_to_speech(text, output_file, args.voice))
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
