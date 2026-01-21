import asyncio
import json
import websockets
import uuid
import wave
import time
import statistics
from typing import List, Dict
import os
from datetime import datetime

class WebSocketTTSBenchmark:
    def __init__(self, ws_uri: str, prompt_id: str):
        """
        初始化 WebSocket TTS 压测工具
        :param ws_uri: WebSocket URI
        :param prompt_id: 提示音频的 ID
        """
        self.ws_uri = ws_uri
        self.prompt_id = prompt_id
        self.results = []
        
    async def single_tts_request(self, text: str, task_id: int, save_audio: bool = False, verbose: bool = False) -> Dict:
        """
        执行单次 TTS 请求
        """
        headers = {"Authorization": "Bearer ryvsk3zz73419gkgubrnvufp"}
        
        start_time = time.time()
        first_chunk_time = None
        chunks_received = 0
        total_audio_bytes = 0
        chunk_details = []  # 记录每个音频包的详细信息
        last_chunk_time = start_time
        
        output_file = f"benchmark_output_{task_id}.wav" if save_audio else None
        wav_out = None
        
        try:
            async with websockets.connect(
                self.ws_uri,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=300,
                close_timeout=3600,
            ) as websocket:
                
                # 发送初始配置
                initial_data = {
                    "prompt_id": self.prompt_id,
                    "speed": 1.0,
                    "stream": True,
                    "request_id": str(uuid.uuid4())
                }
                await websocket.send(json.dumps(initial_data))
                
                # 等待服务器开始信号
                start_response = await websocket.recv()
                start_info = json.loads(start_response)
                
                # 发送文本
                text_data = {
                    "text_chunk": text,
                    "chunk_id": 0
                }
                await websocket.send(json.dumps(text_data))
                
                # 发送结束信号
                await websocket.send(json.dumps({"signal": "end"}))
                
                # 如果需要保存音频，打开 wav 文件
                if save_audio:
                    wav_out = wave.open(output_file, 'wb')
                    wav_out.setnchannels(1)
                    wav_out.setsampwidth(2)
                    wav_out.setframerate(24000)
                
                # 接收响应
                while True:
                    response = await websocket.recv()
                    
                    if isinstance(response, str):
                        try:
                            msg = json.loads(response)
                            if msg.get("status") == "complete":
                                break
                            elif msg.get("status") == "error":
                                return {
                                    "task_id": task_id,
                                    "success": False,
                                    "error": msg.get('message', 'Unknown error'),
                                    "total_latency": 0,
                                    "first_chunk_latency": 0
                                }
                        except json.JSONDecodeError:
                            pass
                    else:
                        # 二进制音频数据
                        current_time = time.time()
                        chunk_latency = (current_time - last_chunk_time) * 1000  # 毫秒
                        
                        if first_chunk_time is None:
                            first_chunk_time = current_time - start_time
                        
                        chunks_received += 1
                        chunk_bytes = len(response)
                        total_audio_bytes += chunk_bytes
                        
                        # 计算这个音频包的 RTF
                        chunk_duration = chunk_bytes / (24000 * 2)  # 音频时长（秒）
                        chunk_rtf = (chunk_latency / 1000) / chunk_duration if chunk_duration > 0 else 0
                        
                        # 记录音频包详情
                        chunk_info = {
                            "chunk_id": chunks_received,
                            "bytes": chunk_bytes,
                            "latency_ms": chunk_latency,
                            "duration_ms": chunk_duration * 1000,
                            "rtf": chunk_rtf,
                            "timestamp": current_time - start_time
                        }
                        chunk_details.append(chunk_info)
                        
                        # 详细输出模式
                        if verbose:
                            print(f"    [Task {task_id}] Chunk {chunks_received}: "
                                  f"{chunk_bytes} bytes, "
                                  f"latency {chunk_latency:.1f}ms, "
                                  f"duration {chunk_duration*1000:.1f}ms, "
                                  f"RTF {chunk_rtf:.4f}")
                        
                        last_chunk_time = current_time
                        
                        if wav_out:
                            wav_out.writeframes(response)
                
                if wav_out:
                    wav_out.close()
                
                total_latency = time.time() - start_time
                
                return {
                    "task_id": task_id,
                    "success": True,
                    "total_latency": total_latency * 1000,  # 转换为毫秒
                    "first_chunk_latency": first_chunk_time * 1000 if first_chunk_time else 0,
                    "chunks_received": chunks_received,
                    "audio_bytes": total_audio_bytes,
                    "rtf": self.calculate_rtf(total_latency, total_audio_bytes),
                    "chunk_details": chunk_details  # 添加详细的音频包信息
                }
                
        except websockets.exceptions.ConnectionClosed as e:
            return {
                "task_id": task_id,
                "success": False,
                "error": f"Connection closed: {str(e)}",
                "total_latency": 0,
                "first_chunk_latency": 0
            }
        except Exception as e:
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "total_latency": 0,
                "first_chunk_latency": 0
            }
        finally:
            if wav_out:
                wav_out.close()
                if not save_audio and output_file and os.path.exists(output_file):
                    os.remove(output_file)
    
    def calculate_rtf(self, processing_time: float, audio_bytes: int) -> float:
        """
        计算实时因子 (Real-Time Factor)
        :param processing_time: 处理时间（秒）
        :param audio_bytes: 音频字节数
        :return: RTF 值
        """
        if audio_bytes == 0:
            return 0
        
        # 假设采样率 24000Hz, 16-bit (2 bytes), 单声道
        audio_duration = audio_bytes / (24000 * 2)  # 音频实际时长（秒）
        
        if audio_duration == 0:
            return 0
        
        return processing_time / audio_duration
    
    async def run_concurrent_test(self, text: str, concurrent_tasks: int, iterations: int = 10, verbose: bool = False):
        """
        运行并发测试
        :param text: 要合成的文本
        :param concurrent_tasks: 并发任务数
        :param iterations: 每个并发数的测试次数
        :param verbose: 是否输出每个音频包的详细信息
        """
        print(f"\n{'='*80}")
        print(f"🚀 测试并发数: {concurrent_tasks}, 迭代次数: {iterations}")
        print(f"{'='*80}")
        
        all_results = []
        
        for iteration in range(iterations):
            tasks = []
            for i in range(concurrent_tasks):
                task_id = iteration * concurrent_tasks + i
                # 只在第一次迭代的第一个任务保存音频样本
                save_audio = (iteration == 0 and i == 0)
                # 所有迭代都输出详细信息（如果 verbose=True）
                task = self.single_tts_request(text, task_id, save_audio, verbose)
                tasks.append(task)
            
            iteration_start = time.time()
            results = await asyncio.gather(*tasks)
            iteration_time = time.time() - iteration_start
            
            all_results.extend(results)
            
            # 打印进度
            successful = sum(1 for r in results if r["success"])
            print(f"  迭代 {iteration + 1}/{iterations}: ✅ {successful}/{concurrent_tasks} "
                  f"耗时 {iteration_time:.2f}s")
            
            # 避免过载，迭代间稍作停顿
            if iteration < iterations - 1:
                await asyncio.sleep(0.5)
        
        # 统计结果
        successful_results = [r for r in all_results if r["success"]]
        
        if not successful_results:
            print("\n❌ 所有请求都失败了！")
            failed_results = [r for r in all_results if not r["success"]]
            print(f"失败原因: {failed_results[0].get('error', 'Unknown')}")
            return
        
        total_latencies = [r["total_latency"] for r in successful_results]
        first_chunk_latencies = [r["first_chunk_latency"] for r in successful_results]
        rtf_values = [r["rtf"] for r in successful_results if r.get("rtf", 0) > 0]
        
        # 收集所有音频包的统计信息
        all_chunk_latencies = []
        all_chunk_rtfs = []
        for r in successful_results:
            if "chunk_details" in r:
                for chunk in r["chunk_details"]:
                    all_chunk_latencies.append(chunk["latency_ms"])
                    all_chunk_rtfs.append(chunk["rtf"])
        
        # 计算统计数据
        stats = {
            "concurrent_tasks": concurrent_tasks,
            "total_requests": len(all_results),
            "successful_requests": len(successful_results),
            "failed_requests": len(all_results) - len(successful_results),
            "rtf": statistics.mean(rtf_values) if rtf_values else 0,
            "total_latency": {
                "average": statistics.mean(total_latencies),
                "p50": statistics.median(total_latencies),
                "p90": self.percentile(total_latencies, 90),
                "p95": self.percentile(total_latencies, 95),
                "p99": self.percentile(total_latencies, 99),
            },
            "first_chunk_latency": {
                "average": statistics.mean(first_chunk_latencies),
                "p50": statistics.median(first_chunk_latencies),
                "p90": self.percentile(first_chunk_latencies, 90),
                "p95": self.percentile(first_chunk_latencies, 95),
                "p99": self.percentile(first_chunk_latencies, 99),
            },
            "chunk_latency": {
                "average": statistics.mean(all_chunk_latencies) if all_chunk_latencies else 0,
                "p50": statistics.median(all_chunk_latencies) if all_chunk_latencies else 0,
                "p90": self.percentile(all_chunk_latencies, 90) if all_chunk_latencies else 0,
                "p95": self.percentile(all_chunk_latencies, 95) if all_chunk_latencies else 0,
                "p99": self.percentile(all_chunk_latencies, 99) if all_chunk_latencies else 0,
            },
            "chunk_rtf": {
                "average": statistics.mean(all_chunk_rtfs) if all_chunk_rtfs else 0,
                "p50": statistics.median(all_chunk_rtfs) if all_chunk_rtfs else 0,
                "p90": self.percentile(all_chunk_rtfs, 90) if all_chunk_rtfs else 0,
                "p95": self.percentile(all_chunk_rtfs, 95) if all_chunk_rtfs else 0,
                "p99": self.percentile(all_chunk_rtfs, 99) if all_chunk_rtfs else 0,
            }
        }
        
        self.results.append(stats)
        self.print_stats(stats)
        
    def percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_stats(self, stats: Dict):
        """打印统计结果"""
        print(f"\n📊 测试结果:")
        print(f"  ✅ 成功率: {stats['successful_requests']}/{stats['total_requests']} "
              f"({stats['successful_requests']/stats['total_requests']*100:.1f}%)")
        
        if stats['rtf'] > 0:
            print(f"  ⚡ RTF (实时因子): {stats['rtf']:.4f}")
        
        print(f"\n  📈 总请求延迟 (Total Request Latency):")
        print(f"     平均: {stats['total_latency']['average']:.2f} ms")
        print(f"     P50:  {stats['total_latency']['p50']:.2f} ms")
        print(f"     P90:  {stats['total_latency']['p90']:.2f} ms")
        print(f"     P95:  {stats['total_latency']['p95']:.2f} ms")
        print(f"     P99:  {stats['total_latency']['p99']:.2f} ms")
        
        print(f"\n  ⚡ 首块延迟 (First Chunk Latency):")
        print(f"     平均: {stats['first_chunk_latency']['average']:.2f} ms")
        print(f"     P50:  {stats['first_chunk_latency']['p50']:.2f} ms")
        print(f"     P90:  {stats['first_chunk_latency']['p90']:.2f} ms")
        print(f"     P95:  {stats['first_chunk_latency']['p95']:.2f} ms")
        print(f"     P99:  {stats['first_chunk_latency']['p99']:.2f} ms")
        
        if stats['chunk_latency']['average'] > 0:
            print(f"\n  📦 单个音频包延迟 (Chunk Latency):")
            print(f"     平均: {stats['chunk_latency']['average']:.2f} ms")
            print(f"     P50:  {stats['chunk_latency']['p50']:.2f} ms")
            print(f"     P90:  {stats['chunk_latency']['p90']:.2f} ms")
            print(f"     P95:  {stats['chunk_latency']['p95']:.2f} ms")
            print(f"     P99:  {stats['chunk_latency']['p99']:.2f} ms")
        
        if stats['chunk_rtf']['average'] > 0:
            print(f"\n  🎯 单个音频包 RTF (Chunk RTF):")
            print(f"     平均: {stats['chunk_rtf']['average']:.4f}")
            print(f"     P50:  {stats['chunk_rtf']['p50']:.4f}")
            print(f"     P90:  {stats['chunk_rtf']['p90']:.4f}")
            print(f"     P95:  {stats['chunk_rtf']['p95']:.4f}")
            print(f"     P99:  {stats['chunk_rtf']['p99']:.4f}")
    
    def print_summary_table(self):
        """打印汇总表格"""
        print("\n" + "="*140)
        print("📊 测试结果汇总")
        print("="*140)
        
        print("\n### 总请求延迟 (Total Request Latency)\n")
        print(f"| {'并发数':<12} | {'RTF':<10} | {'平均 (ms)':<12} | {'50th (ms)':<12} | "
              f"{'90th (ms)':<12} | {'95th (ms)':<12} | {'99th (ms)':<12} |")
        print(f"| {'-'*12} | {'-'*10} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} |")
        
        for stats in self.results:
            print(f"| {stats['concurrent_tasks']:<12} | "
                  f"{stats['rtf']:<10.4f} | "
                  f"{stats['total_latency']['average']:<12.2f} | "
                  f"{stats['total_latency']['p50']:<12.2f} | "
                  f"{stats['total_latency']['p90']:<12.2f} | "
                  f"{stats['total_latency']['p95']:<12.2f} | "
                  f"{stats['total_latency']['p99']:<12.2f} |")
        
        print("\n### 首块延迟 (First Chunk Latency)\n")
        print(f"| {'并发数':<12} | {'平均 (ms)':<12} | {'50th (ms)':<12} | "
              f"{'90th (ms)':<12} | {'95th (ms)':<12} | {'99th (ms)':<12} |")
        print(f"| {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} |")
        
        for stats in self.results:
            print(f"| {stats['concurrent_tasks']:<12} | "
                  f"{stats['first_chunk_latency']['average']:<12.2f} | "
                  f"{stats['first_chunk_latency']['p50']:<12.2f} | "
                  f"{stats['first_chunk_latency']['p90']:<12.2f} | "
                  f"{stats['first_chunk_latency']['p95']:<12.2f} | "
                  f"{stats['first_chunk_latency']['p99']:<12.2f} |")
        
        print("\n" + "="*140)
    
    def save_results(self, filename: str = None):
        """保存结果到 JSON 文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细结果已保存到: {filename}")


async def main():
    """主测试函数"""
    
    # ========== 配置参数 ==========
    # WebSocket URI
    WS_URI = "wss://platform-bj.wair.ac.cn/maas/ws/zero_shot_tts"
    # WS_URI = "ws://172.16.10.5:8080/zeroshot_stream_tts" 
    # Prompt ID (需要先通过 get_prompt_id 获取)
    PROMPT_ID = "cosyvoice_gan_cb9829cf2c050996eeed620c7acb58ef"  # 替换为实际的 prompt_id
    # PROMPT_ID = "cosyvoice_gan_4a10f32ecb713d4cd6e93a54ac4f4129" # node10本地
    # PROMPT_ID = "cosyvoice_flow_d6f48bd7288d3a02e5ea65d98a602212"
    # 测试文本
    # TEST_TEXT = "系列动画片《中国奇谭》如何衍生出大电影《浪浪山小妖怪》？新的故事里，曾被众多青年观众共情的小猪妖，有哪些成长变化。"
    TEST_TEXT = "人工智能正在改变我们的生活方式，语音合成技术也越来越自然流畅。"
    
    # 并发数列表
    CONCURRENT_LEVELS = [1, 2, 4, 6, 8, 10]
    CONCURRENT_LEVELS = [10]
    # 每个并发数的测试次数
    ITERATIONS = 5
    
    # ==============================
    
    print("="*140)
    print(f"🎯 WebSocket TTS 性能压测")
    print(f"📍 URI: {WS_URI}")
    print(f"📝 测试文本: {TEST_TEXT[:50]}...")
    print(f"🔢 并发级别: {CONCURRENT_LEVELS}")
    print(f"🔁 每级迭代: {ITERATIONS} 次")
    print("="*140)
    
    # 创建测试实例
    benchmark = WebSocketTTSBenchmark(WS_URI, PROMPT_ID)
    
    # 运行测试
    for concurrent_tasks in CONCURRENT_LEVELS:
        # 第一个并发级别显示详细的音频包信息
        verbose = (concurrent_tasks == CONCURRENT_LEVELS[0])
        await benchmark.run_concurrent_test(TEST_TEXT, concurrent_tasks, ITERATIONS, verbose)
        # 两次测试之间暂停，避免过载
        await asyncio.sleep(2)
    
    # 打印汇总表格
    benchmark.print_summary_table()
    
    # 保存结果
    benchmark.save_results()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())