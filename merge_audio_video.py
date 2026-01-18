#!/usr/bin/env python3
"""
将 MP3 音频与 MP4 视频合成为最终视频

使用方法:
1. 基本用法: python merge_audio_video.py audio.mp3 video.mp4
2. 指定输出: python merge_audio_video.py audio.mp3 video.mp4 -o output.mp4
3. 自定义参数: python merge_audio_video.py audio.mp3 video.mp4 --fps 30

特性:
- 自动循环视频以匹配音频长度
- 保持视频原始分辨率和帧率
- 支持自定义输出参数
"""

import argparse
import os
from datetime import datetime

try:
    # moviepy 2.x 版本
    from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
except ImportError:
    # moviepy 1.x 版本（向后兼容）
    from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips


def merge_audio_video(audio_path: str, video_path: str, output_path: str = None, 
                       fps: int = None, preset: str = 'medium', bitrate: str = None):
    """
    将音频和视频合成为最终视频文件
    
    参数:
        audio_path: MP3 音频文件路径
        video_path: MP4 视频文件路径
        output_path: 输出文件路径（默认自动生成）
        fps: 输出视频帧率（默认使用原视频帧率）
        preset: 编码预设 (ultrafast, fast, medium, slow) - 影响编码速度和质量
        bitrate: 视频比特率，如 '2000k' (默认自动计算以保持500MB/30分钟)
    """
    print("=" * 60)
    print("🎬 音频视频合成工具")
    print("=" * 60)
    
    # 检查文件是否存在
    if not os.path.exists(audio_path):
        print(f"❌ 错误: 音频文件不存在 - {audio_path}")
        return
    
    if not os.path.exists(video_path):
        print(f"❌ 错误: 视频文件不存在 - {video_path}")
        return
    
    print(f"\n📁 加载文件...")
    print(f"  音频: {os.path.basename(audio_path)}")
    print(f"  视频: {os.path.basename(video_path)}")
    
    # 加载音频和视频
    audio_clip = AudioFileClip(audio_path)
    video_clip = VideoFileClip(video_path)
    
    audio_duration = audio_clip.duration
    video_duration = video_clip.duration
    
    print(f"\n⏱️  时长信息:")
    print(f"  音频时长: {format_duration(audio_duration)}")
    print(f"  视频时长: {format_duration(video_duration)}")
    
    # 如果视频比音频短，需要循环视频
    if video_duration < audio_duration:
        # 计算需要循环的次数
        loop_count = int(audio_duration / video_duration) + 1
        print(f"\n🔄 视频需要循环 {loop_count} 次以匹配音频长度")
        
        # 循环视频
        video_clips = [video_clip] * loop_count
        looped_video = concatenate_videoclips(video_clips)
        
        # 裁剪到音频长度（兼容新旧版本 API）
        try:
            # moviepy 2.x
            final_video = looped_video.subclipped(0, audio_duration)
        except AttributeError:
            # moviepy 1.x
            final_video = looped_video.subclip(0, audio_duration)
    else:
        # 视频比音频长，直接裁剪
        print(f"\n✂️  裁剪视频到音频长度")
        try:
            # moviepy 2.x
            final_video = video_clip.subclipped(0, audio_duration)
        except AttributeError:
            # moviepy 1.x
            final_video = video_clip.subclip(0, audio_duration)
    
    # 设置音频（兼容新旧版本 API）
    try:
        # moviepy 2.x
        final_video = final_video.with_audio(audio_clip)
    except AttributeError:
        # moviepy 1.x
        final_video = final_video.set_audio(audio_clip)
    
    # 确定输出文件
    if output_path is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f'merged_video_{timestamp}.mp4'
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print(f"\n🎥 正在渲染最终视频...")
    print(f"  输出: {output_path}")
    
    # 计算目标比特率（如果未指定）
    # 目标：30分钟 ≈ 500MB
    if bitrate is None:
        # 500MB = 4000Mbit, 30分钟 = 1800秒
        # 总比特率 ≈ 2.2Mbps，减去音频128kbps
        # 视频比特率 ≈ 2000kbps
        target_video_bitrate = '2000k'
        auto_bitrate = True
    else:
        target_video_bitrate = bitrate
        auto_bitrate = False
    
    # 渲染参数（针对手机观看优化）
    write_params = {
        'codec': 'libx264',
        'audio_codec': 'aac',
        'audio_bitrate': '128k',  # 音频比特率
        'bitrate': target_video_bitrate,  # 视频比特率
        'preset': preset,  # 编码预设
        'remove_temp': True,
    }
    
    # 如果指定了 fps，使用自定义 fps
    if fps:
        write_params['fps'] = fps
        print(f"  帧率: {fps} fps")
    else:
        # 获取原始视频帧率（兼容不同版本）
        try:
            original_fps = video_clip.fps
        except AttributeError:
            original_fps = 30  # 默认帧率
        write_params['fps'] = original_fps
        print(f"  帧率: {original_fps} fps (原始)")
    
    print(f"  视频比特率: {target_video_bitrate}{' (自动优化)' if auto_bitrate else ''}")
    print(f"  音频比特率: 128k")
    print(f"  编码预设: {preset}")
    
    # 估算文件大小
    estimated_size_mb = (audio_duration / 60) * (2000 / 8 * 60) / 1024  # 粗略估算
    print(f"  预计文件大小: ~{estimated_size_mb:.0f} MB")
    
    print(f"\n📊 渲染进度:")
    print(f"  总时长: {format_duration(audio_duration)}")
    print(f"  这可能需要几分钟，请耐心等待...\n")
    
    try:
        # 渲染视频（显示进度条）
        final_video.write_videofile(
            output_path,
            **write_params,
            logger='bar'   # 使用进度条
        )
    except Exception as render_error:
        print(f"\n❌ 渲染失败!")
        print(f"错误类型: {type(render_error).__name__}")
        print(f"错误信息: {str(render_error)}")
        print(f"\n详细错误日志:")
        import traceback
        traceback.print_exc()
        
        # 清理资源
        try:
            audio_clip.close()
            video_clip.close()
            final_video.close()
            if video_duration < audio_duration:
                looped_video.close()
        except:
            pass
        raise
    
    # 清理资源
    print(f"\n🧹 清理临时文件...")
    try:
        audio_clip.close()
        video_clip.close()
        final_video.close()
        if video_duration < audio_duration:
            looped_video.close()
    except Exception as cleanup_error:
        print(f"⚠️  清理警告: {cleanup_error}")
    
    # 显示结果
    output_size = os.path.getsize(output_path)
    print(f"\n✅ 合成成功！")
    print(f"  输出文件: {output_path}")
    print(f"  文件大小: {output_size / 1024 / 1024:.2f} MB")
    print(f"  视频时长: {format_duration(audio_duration)}")
    print("=" * 60)


def format_duration(seconds: float) -> str:
    """格式化时长为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def main():
    parser = argparse.ArgumentParser(
        description='将 MP3 音频与 MP4 视频合成为最终视频（针对手机观看优化）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（默认优化：30分钟≈500MB）
  %(prog)s audio.mp3 background.mp4 -o output.mp4
  
  # 自定义比特率（更高质量）
  %(prog)s audio.mp3 background.mp4 -o output.mp4 --bitrate 3000k
  
  # 快速编码（降低质量但加快速度）
  %(prog)s audio.mp3 background.mp4 -o output.mp4 --preset fast
  
  # 完整设置
  %(prog)s audio.mp3 background.mp4 -o output.mp4 --fps 30 --bitrate 2500k --preset medium
  
  # 合成播客（默认已优化）
  %(prog)s shoedog/video/merged_*.mp3 background.mp4 -o 鞋狗完整版.mp4
  
压缩说明:
  默认设置针对手机观看优化，30分钟视频约500MB
  - 视频比特率: 2000kbps
  - 音频比特率: 128kbps
  - 编码预设: medium（平衡质量和速度）
        """
    )
    
    parser.add_argument('audio', help='输入的音频文件（MP3）')
    parser.add_argument('video', help='背景视频文件（MP4）')
    parser.add_argument('-o', '--output', help='输出文件路径（默认: merged_video_YYYYMMDD_HHMMSS.mp4）')
    parser.add_argument('--fps', type=int, help='输出视频帧率（默认: 使用原视频帧率）')
    parser.add_argument('--bitrate', help='视频比特率，如 2000k, 3000k（默认: 2000k，适合手机）')
    parser.add_argument('--preset', default='medium', 
                        choices=['ultrafast', 'fast', 'medium', 'slow'],
                        help='编码预设（默认: medium）- fast=更快, slow=更好质量')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🎬 MoviePy 音频视频合成工具（手机优化版）")
    print("=" * 60)
    
    try:
        merge_audio_video(args.audio, args.video, args.output, args.fps, args.preset, args.bitrate)
    except FileNotFoundError as e:
        print(f"\n❌ 文件未找到错误:")
        print(f"  {e}")
        print(f"\n请检查文件路径是否正确。")
    except PermissionError as e:
        print(f"\n❌ 权限错误:")
        print(f"  {e}")
        print(f"\n请检查文件是否被其他程序占用，或您是否有写入权限。")
    except KeyboardInterrupt:
        print(f"\n\n⚠️  用户中断操作")
        print(f"渲染已取消。")
    except Exception as e:
        print(f"\n❌ 未预期的错误:")
        print(f"错误类型: {type(e).__name__}")
        print(f"错误信息: {str(e)}")
        print(f"\n完整错误堆栈:")
        import traceback
        traceback.print_exc()
        print(f"\n💡 调试建议:")
        print(f"1. 检查 ffmpeg 是否正确安装: ffmpeg -version")
        print(f"2. 确认音频和视频文件格式正确")
        print(f"3. 尝试使用较小的测试文件")
        print(f"4. 检查磁盘空间是否充足")


if __name__ == '__main__':
    main()
