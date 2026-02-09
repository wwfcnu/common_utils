import threading
import queue
import time
import os
from datetime import datetime
from typing import List, Optional, Dict, Tuple, Set
from pydub import AudioSegment
from pydub.playback import play

class WAVPlayer:
    def __init__(self, 
                 delay_seconds: float = 2.0,
                 log_file_prefix: str = "playback_log_zhvoice",#playback_log_zhvoice
                 max_queue_size: int = 5
                 ):
        self.audio_queue = queue.Queue(maxsize=max_queue_size)
        self.is_running = True
        self.delay_seconds = delay_seconds
        
        # Create timestamped log filename
        self.log_file = f"{log_file_prefix}.txt"
        print(f"Log file created: {self.log_file}")

    def parse_wav_scp_line(self, line: str) -> Tuple[str, str]:
        """Parse wav.scp line in format 'wav_id\twav_path'"""
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Invalid wav.scp format: {line}")
        wav_id, wav_path = parts
        return wav_id, wav_path

    def log_timestamp(self, wav_id: str, wav_path: str, event: str, timestamp: datetime) -> None:
        """Log playback events with timestamps"""
        with open(self.log_file, 'a', encoding='utf-8') as f:
            log_entry = f"{wav_id}\t{wav_path}\t{event}\t{timestamp.isoformat()}\n"
            f.write(log_entry)

    def get_completed_wav_ids(self) -> Set[str]:
        """Read log file to get completed wav_ids"""
        completed_wav_ids = set()
        
        if not os.path.exists(self.log_file):
            return completed_wav_ids
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 3 and parts[2] == "end":
                        completed_wav_ids.add(parts[0])
        except Exception as e:
            print(f"Error reading log file: {str(e)}")
            
        return completed_wav_ids

    def wav_producer(self, wav_data: List[Dict[str, str]]) -> None:
        """Put WAV file paths into the queue for playback"""
        try:
            for item in wav_data:
                if not self.is_running:
                    break
                    
                wav_id = item['wav_id']
                wav_path = item['wav_path']
                
                # Check if file exists
                if not os.path.exists(wav_path):
                    print(f"Warning: WAV file not found: {wav_path}")
                    continue
                
                # Put wav info into queue
                self.audio_queue.put({
                    'wav_id': wav_id,
                    'wav_path': wav_path
                })
                print(f"Queued for playback: {wav_id} -> {wav_path}")
                    
        except Exception as e:
            print(f"Producer thread error: {str(e)}")
        finally:
            self.audio_queue.put(None)

    def audio_consumer(self) -> None:
        """Get WAV files from the queue and play them directly"""
        try:
            while self.is_running:
                item = self.audio_queue.get()
                if item is None:
                    break
                
                wav_id = item['wav_id']
                wav_path = item['wav_path']
                
                try:
                    # Load audio file
                    audio = AudioSegment.from_wav(wav_path)

                    # Log start time
                    start_time = datetime.now()
                    self.log_timestamp(wav_id, wav_path, "start", start_time)
                    print(f"Starting playback: {wav_id} -> {wav_path}")

                    # Play audio
                    import random

                    random_number = random.randint(4,6)
                    play(audio+random_number)
   
                    
                    # Log end time
                    end_time = datetime.now()
                    self.log_timestamp(wav_id, wav_path, "end", end_time)
                    print(f"Finished playing: {wav_id} -> {wav_path}")
                    
                    if self.delay_seconds > 0:
                        print(f"Waiting for {self.delay_seconds} seconds before next audio...")
                        time.sleep(self.delay_seconds)
                        
                except Exception as e:
                    print(f"Error playing audio for '{wav_id}': {str(e)}")
                finally:
                    self.audio_queue.task_done()
                    
        except Exception as e:
            print(f"Consumer thread error: {str(e)}")

    def process_wav_scp(self, wav_scp_file: str, resume: bool = True) -> None:
        """Process wav.scp file containing wav_id\twav_path pairs, with option to resume"""
        # Get completed wav_ids if resuming
        completed_wav_ids = set()
        if resume:
            completed_wav_ids = self.get_completed_wav_ids()
            if completed_wav_ids:
                print(f"Resuming from last session. Skipping {len(completed_wav_ids)} completed items.")
        
        # Read and parse wav.scp file
        wav_data = []
        try:
            with open(wav_scp_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        wav_id, wav_path = self.parse_wav_scp_line(line)
                        
                        # Skip if already completed and we're resuming
                        if resume and wav_id in completed_wav_ids:
                            print(f"Skipping already completed wav_id: {wav_id}")
                            continue
                            
                        wav_data.append({
                            'wav_id': wav_id,
                            'wav_path': wav_path
                        })
                    except ValueError as e:
                        print(f"Error parsing line {line_num}: {e}")
                        continue
                        
        except FileNotFoundError:
            print(f"Error: wav.scp file not found: {wav_scp_file}")
            return
        except Exception as e:
            print(f"Error reading wav.scp file: {str(e)}")
            return
        
        if not wav_data:
            print("No new items to process.")
            return
            
        print(f"Processing {len(wav_data)} WAV files...")
        
        try:
            # Start consumer thread
            consumer_thread = threading.Thread(target=self.audio_consumer)
            consumer_thread.start()
            
            # Start producer thread
            producer_thread = threading.Thread(
                target=self.wav_producer,
                args=(wav_data,)
            )
            producer_thread.start()
            
            # Wait for producer to finish
            producer_thread.join()
            # Wait for consumer to finish
            consumer_thread.join()
            
        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            self.is_running = False

def main():
    # Example usage
    # jiaoliao未完成 jilu

    wav_scp_file = "./zhvoice/zhvoice/wav.scp" #202507170920
    # wav_scp_file = "./aishell_wav.scp"
    # Create WAVPlayer with 2 second delay
    wav_player = WAVPlayer(delay_seconds=2.0, max_queue_size=3)
    
    # Process wav.scp file with resume enabled
    wav_player.process_wav_scp(wav_scp_file, resume=True)

if __name__ == "__main__":
    main()