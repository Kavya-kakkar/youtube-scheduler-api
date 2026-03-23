from scheduler import start_scheduler
import time

start_scheduler()

# keep process alive
while True:
    time.sleep(60)