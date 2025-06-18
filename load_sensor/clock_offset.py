from datetime import datetime
import time

now_dt = datetime.now()
now_time = time.time()

dt_as_posix = now_dt.timestamp()

offset = dt_as_posix - now_time
print(f"Offset (datetime - time.time): {offset:.6f} seconds")