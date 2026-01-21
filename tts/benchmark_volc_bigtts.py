import asyncio
import websockets
import uuid
import json
import gzip
import copy
import time
import statistics
from typing import List, Dict
from datetime import datetime

MESSAGE_TYPES = {11: "audio-only server response", 12: "frontend server response", 15: "error message from server"}
MESSAGE_TYPE_SPECIFIC_FLAGS = {0: "no sequence number", 1: "sequence number > 0",
                               2: "last message from server (seq < 0)", 3: "sequence number < 0"}

class BytedanceTTSBenchmark:
    def __init__(self, appid: str, token: str, voice_type: str, cluster: str = "volcano_tts"):
        """
        初始化字节 TTS 压测工具
        """
        self.appid = appid
        self.token = token
        self.voice_type = voice_type
        self.cluster = cluster
        self.host = "openspeech.bytedance.com"
        self.api_url = f"wss://{self.host}/api/v1/tts/ws_binary"
        self.results = []
        
        # 默认请求头（协议版本 1.1）
        self.default_header = bytearray(b'\x11\x10\x11\x00')
        
        # 基础请求模板
        self.request_json = {
            "app": {
                "appid": self.appid,
                "token": "access_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "388808087185088"
            },
            "audio": {
                "voice_type": self.voice_type,
                "encoding": "pcm",
                "speed_ratio": 1.0,
                "volume_ratio": 1.0,
                "pitch_ratio": 1.0,
            },
            "request": {
                "reqid": "xxx",
                "text": "xxx",
                "text_type": "plain",
                "operation": "submit",
            }
        }
    
    def build_request(self, text: str) -> bytearray:
        """构建请求数据包"""
        submit_request_json = copy.deepcopy(self.request_json)
        submit_request_json["request"]["reqid"] = str(uuid.uuid4())
        submit_request_json["request"]["text"] = text
        
        payload_bytes = str.encode(json.dumps(submit_request_json))
        payload_bytes = gzip.compress(payload_bytes)
        
        full_client_request = bytearray(self.default_header)
        full_client_request.extend((len(payload_bytes)).to_bytes(4, 'big'))
        full_client_request.extend(payload_bytes)
        
        return full_client_request
    
    def parse_response(self, res: bytes, verbose: bool = False) -> Dict:
        """解析服务器响应"""
        protocol_version = res[0] >> 4
        header_size = res[0] & 0x0f
        message_type = res[1] >> 4
        message_type_specific_flags = res[1] & 0x0f
        serialization_method = res[2] >> 4
        message_compression = res[2] & 0x0f
        payload = res[header_size*4:]
        
        result = {
            "message_type": message_type,
            "flags": message_type_specific_flags,
            "payload_size": 0,
            "sequence_number": None,
            "audio_data": None,
            "is_last": False,
            "error": None
        }
        
        if message_type == 0xb:  # audio-only server response
            if message_type_specific_flags == 0:  # ACK
                result["is_ack"] = True
                return result
            else:
                sequence_number = int.from_bytes(payload[:4], "big", signed=True)
                payload_size = int.from_bytes(payload[4:8], "big", signed=False)
                audio_data = payload[8:]
                
                result["sequence_number"] = sequence_number
                result["payload_size"] = payload_size
                result["audio_data"] = audio_data
                result["is_last"] = (sequence_number < 0)
                
                if verbose:
                    print(f"      Seq: {sequence_number}, Size: {payload_size} bytes")
                
                return result
                
        elif message_type == 0xf:  # error
            code = int.from_bytes(payload[:4], "big", signed=False)
            msg_size = int.from_bytes(payload[4:8], "big", signed=False)
            error_msg = payload[8:]
            if message_compression == 1:
                error_msg = gzip.decompress(error_msg)
            error_msg = str(error_msg, "utf-8")
            
            result["error"] = {"code": code, "message": error_msg}
            result["is_last"] = True
            return result
        
        return result
    
    async def single_tts_request(self, text: str, task_id: int, save_audio: bool = False, verbose: bool = False) -> Dict:
        """
        执行单次 TTS 请求
        """
        start_time = time.time()
        first_chunk_time = None
        chunks_received = 0
        total_audio_bytes = 0
        chunk_details = []
        last_chunk_time = start_time
        
        output_file = f"benchmark_output_{task_id}.pcm" if save_audio else None
        file_handle = None
        
        try:
            header = {"Authorization": f"Bearer; {self.token}"}
            request_data = self.build_request(text)
            
            async with websockets.connect(self.api_url, extra_headers=header, ping_interval=None) as ws:
                # 发送请求
                await ws.send(request_data)
                
                if save_audio:
                    file_handle = open(output_file, "wb")
                
                # 接收响应
                while True:
                    res = await ws.recv()
                    current_time = time.time()
                    chunk_latency = (current_time - last_chunk_time) * 1000
                    
                    parsed = self.parse_response(res, verbose)
                    
                    # 处理错误
                    if parsed.get("error"):
                        if file_handle:
                            file_handle.close()
                        return {
                            "task_id": task_id,
                            "success": False,
                            "error": parsed["error"]["message"],
                            "total_latency": 0,
                            "first_chunk_latency": 0
                        }
                    
                    # 处理音频数据
                    if parsed.get("audio_data"):
                        if first_chunk_time is None:
                            first_chunk_time = current_time - start_time
                        
                        chunks_received += 1
                        chunk_bytes = parsed["payload_size"]
                        total_audio_bytes += chunk_bytes
                        
                        # 计算音频包的持续时间和 RTF
                        # MP3 @ 128kbps: 16000 bytes/sec
                        chunk_duration = chunk_bytes / 48000  # 秒
                        chunk_rtf = (chunk_latency / 1000) / chunk_duration if chunk_duration > 0 else 0
                        
                        chunk_info = {
                            "chunk_id": chunks_received,
                            "sequence": parsed["sequence_number"],
                            "bytes": chunk_bytes,
                            "latency_ms": chunk_latency,
                            "duration_ms": chunk_duration * 1000,
                            "rtf": chunk_rtf,
                            "timestamp": current_time - start_time
                        }
                        chunk_details.append(chunk_info)
                        
                        if verbose:
                            print(f"    [Task {task_id}] Chunk {chunks_received}: "
                                  f"{chunk_bytes} bytes, "
                                  f"latency {chunk_latency:.1f}ms, "
                                  f"duration {chunk_duration*1000:.1f}ms, "
                                  f"RTF {chunk_rtf:.4f}")
                        
                        if file_handle:
                            file_handle.write(parsed["audio_data"])
                        
                        last_chunk_time = current_time
                    
                    # 检查是否结束
                    if parsed.get("is_last"):
                        break
                
                if file_handle:
                    file_handle.close()
                
                total_latency = time.time() - start_time
                
                # 计算总体 RTF
                total_audio_duration = total_audio_bytes / 48000  # 秒
                overall_rtf = total_latency / total_audio_duration if total_audio_duration > 0 else 0
                
                return {
                    "task_id": task_id,
                    "success": True,
                    "total_latency": total_latency * 1000,
                    "first_chunk_latency": first_chunk_time * 1000 if first_chunk_time else 0,
                    "chunks_received": chunks_received,
                    "audio_bytes": total_audio_bytes,
                    "rtf": overall_rtf,
                    "chunk_details": chunk_details
                }
                
        except Exception as e:
            if file_handle:
                file_handle.close()
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "total_latency": 0,
                "first_chunk_latency": 0
            }
    
    async def run_concurrent_test(self, text: str, concurrent_tasks: int, iterations: int = 10, verbose: bool = False):
        """
        运行并发测试
        """
        print(f"\n{'='*80}")
        print(f"🚀 测试并发数: {concurrent_tasks}, 迭代次数: {iterations}")
        print(f"{'='*80}")
        
        all_results = []
        
        for iteration in range(iterations):
            tasks = []
            for i in range(concurrent_tasks):
                task_id = iteration * concurrent_tasks + i
                save_audio = (iteration == 0 and i == 0)
                task = self.single_tts_request(text, task_id, save_audio, verbose)
                tasks.append(task)
            
            iteration_start = time.time()
            results = await asyncio.gather(*tasks)
            iteration_time = time.time() - iteration_start
            
            all_results.extend(results)
            
            successful = sum(1 for r in results if r["success"])
            print(f"  迭代 {iteration + 1}/{iterations}: ✅ {successful}/{concurrent_tasks} "
                  f"耗时 {iteration_time:.2f}s")
            
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
        
        # 收集所有音频包的统计
        all_chunk_latencies = []
        all_chunk_rtfs = []
        for r in successful_results:
            if "chunk_details" in r:
                for chunk in r["chunk_details"]:
                    all_chunk_latencies.append(chunk["latency_ms"])
                    all_chunk_rtfs.append(chunk["rtf"])
        
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
        
        if any(stats.get('chunk_latency', {}).get('average', 0) > 0 for stats in self.results):
            print("\n### 单个音频包延迟 (Chunk Latency)\n")
            print(f"| {'并发数':<12} | {'平均 (ms)':<12} | {'50th (ms)':<12} | "
                  f"{'90th (ms)':<12} | {'95th (ms)':<12} | {'99th (ms)':<12} |")
            print(f"| {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} |")
            
            for stats in self.results:
                if 'chunk_latency' in stats:
                    print(f"| {stats['concurrent_tasks']:<12} | "
                          f"{stats['chunk_latency']['average']:<12.2f} | "
                          f"{stats['chunk_latency']['p50']:<12.2f} | "
                          f"{stats['chunk_latency']['p90']:<12.2f} | "
                          f"{stats['chunk_latency']['p95']:<12.2f} | "
                          f"{stats['chunk_latency']['p99']:<12.2f} |")
        
        if any(stats.get('chunk_rtf', {}).get('average', 0) > 0 for stats in self.results):
            print("\n### 单个音频包 RTF (Chunk RTF)\n")
            print(f"| {'并发数':<12} | {'平均':<12} | {'50th':<12} | "
                  f"{'90th':<12} | {'95th':<12} | {'99th':<12} |")
            print(f"| {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} | {'-'*12} |")
            
            for stats in self.results:
                if 'chunk_rtf' in stats:
                    print(f"| {stats['concurrent_tasks']:<12} | "
                          f"{stats['chunk_rtf']['average']:<12.4f} | "
                          f"{stats['chunk_rtf']['p50']:<12.4f} | "
                          f"{stats['chunk_rtf']['p90']:<12.4f} | "
                          f"{stats['chunk_rtf']['p95']:<12.4f} | "
                          f"{stats['chunk_rtf']['p99']:<12.4f} |")
        
        print("\n" + "="*140)
    
    def save_results(self, filename: str = None):
        """保存结果到 JSON 文件"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bytedance_tts_benchmark_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 详细结果已保存到: {filename}")


async def main():
    """主测试函数"""
    
    # ========== 配置参数 ==========
    # APPID = "3890413330"
    # TOKEN = "E3vt4URBGVIX_Q4Zg9xFsrsBoXQFSLuB"
    APPID = "8538698484"
    TOKEN = "e4nh25GIHULCTJacsOqXC2PvFyesSZmD"
    VOICE_TYPE = "zh_female_kefunvsheng_mars_bigtts"
    CLUSTER = "volcano_tts"
    
    # 测试文本
    TEST_TEXT = "人工智能正在改变我们的生活方式，语音合成技术也越来越自然流畅。"
    
    # 并发数列表
    # CONCURRENT_LEVELS = [1, 2, 4, 6, 8, 10]
    CONCURRENT_LEVELS = [1]
    # 每个并发数的测试次数
    ITERATIONS = 5
    
    # 是否输出详细的音频包信息（建议只在第一个并发级别输出）
    VERBOSE = True
    
    # ==============================
    
    print("="*140)
    print(f"🎯 字节 TTS 性能压测")
    print(f"📍 API: openspeech.bytedance.com")
    print(f"🎤 音色: {VOICE_TYPE}")
    print(f"📝 测试文本: {TEST_TEXT[:50]}...")
    print(f"🔢 并发级别: {CONCURRENT_LEVELS}")
    print(f"🔁 每级迭代: {ITERATIONS} 次")
    print("="*140)
    
    # 创建测试实例
    benchmark = BytedanceTTSBenchmark(APPID, TOKEN, VOICE_TYPE, CLUSTER)
    
    # 运行测试
    for idx, concurrent_tasks in enumerate(CONCURRENT_LEVELS):
        # 只在第一个并发级别输出详细信息
        verbose = VERBOSE and (idx == 0)
        await benchmark.run_concurrent_test(TEST_TEXT, concurrent_tasks, ITERATIONS, verbose)
        await asyncio.sleep(2)
    
    # 打印汇总表格
    benchmark.print_summary_table()
    
    # 保存结果
    benchmark.save_results()


if __name__ == "__main__":
    asyncio.run(main())