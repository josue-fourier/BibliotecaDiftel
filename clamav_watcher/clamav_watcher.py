import os
import time
import logging
import requests
import clamd
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

WATCH_DIR = "/data/buzon/tmp"
SAFE_DIR = "/data/buzon/safe"
QUARANTINE_DIR = "/data/buzon/quarantine"

WEBHOOK_CLEAN = os.getenv("N8N_WEBHOOK_CLEAN")
WEBHOOK_THREAT = os.getenv("N8N_WEBHOOK_THREAT")
CLAMAV_HOST = os.getenv("CLAMAV_HOST", "clamav")
CLAMAV_PORT = int(os.getenv("CLAMAV_PORT", "3310"))

# Ensure directories exist
for d in [WATCH_DIR, SAFE_DIR, QUARANTINE_DIR]:
    os.makedirs(d, exist_ok=True)

class UploadHandler(FileSystemEventHandler):
    def on_closed(self, event):
        """Triggered when a file is closed after writing."""
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        logging.info(f"Detected new file ready for scan: {filename}")
        self.process_file(filepath, filename)
        
    def process_file(self, filepath, filename):
        try:
            # Wait a brief moment to ensure the file system has released any locks completely
            time.sleep(0.5)
            
            cd = clamd.ClamdNetworkSocket(CLAMAV_HOST, CLAMAV_PORT)
            logging.info(f"Scanning file: {filepath}")
            
            # Use instream to stream the file to ClamAV without requiring shared volumes
            with open(filepath, 'rb') as f:
                result = cd.instream(f)
            
            # The result format from clamd.instream is typically:
            # {'stream': ('OK', None)} or {'stream': ('FOUND', 'Eicar-Test-Signature')}
            stream_result = result.get('stream', ('ERROR', 'Unknown response'))
            status = stream_result[0]
            
            if status == 'OK':
                logging.info(f"✅ File {filename} is CLEAN.")
                new_path = os.path.join(SAFE_DIR, filename)
                os.rename(filepath, new_path)
                
                if WEBHOOK_CLEAN:
                    requests.post(WEBHOOK_CLEAN, json={"filename": filename, "status": "clean"})
            elif status == 'FOUND':
                virus_name = stream_result[1]
                logging.warning(f"☣️ File {filename} is INFECTED: {virus_name}")
                new_path = os.path.join(QUARANTINE_DIR, filename)
                os.rename(filepath, new_path)
                
                if WEBHOOK_THREAT:
                    requests.post(WEBHOOK_THREAT, json={"filename": filename, "status": "infected", "threat": virus_name})
            else:
                logging.error(f"❌ Unknown ClamAV status: {status} - {stream_result}")
                
        except Exception as e:
            logging.error(f"Error processing {filename}: {e}")

if __name__ == "__main__":
    logging.info("Starting ClamAV Watcher Service...")
    logging.info(f"Watching directory: {WATCH_DIR}")
    
    # Wait for ClamAV to be ready
    while True:
        try:
            cd = clamd.ClamdNetworkSocket(CLAMAV_HOST, CLAMAV_PORT)
            cd.ping()
            logging.info("Successfully connected to ClamAV.")
            break
        except clamd.ConnectionError:
            logging.warning("Waiting for ClamAV to be ready...")
            time.sleep(5)
    
    event_handler = UploadHandler()
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
