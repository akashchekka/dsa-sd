import time
import threading
from datetime import datetime, timezone

class SnowflakeGenerator:
    def __init__(self, node_id: int, epoch: int = 1767225600000):
        """
        Initializes the Snowflake ID Generator.
        
        :param node_id: Unique ID of this process/machine (0-1023)
        :param epoch: Custom epoch millisecond timestamp. 
                      Default is 1767225600000 (January 1, 2026, 00:00:00 UTC)
        """
        # Bit allocation setup
        self.node_id_bits = 10
        self.sequence_bits = 12
        
        # Calculate dynamic bitmasks
        self.max_node_id = -1 ^ (-1 << self.node_id_bits)      # 1023
        self.max_sequence = -1 ^ (-1 << self.sequence_bits)    # 4095
        
        if not (0 <= node_id <= self.max_node_id):
            raise ValueError(f"Node ID must be between 0 and {self.max_node_id}")
            
        self.node_id = node_id
        self.epoch = epoch
        
        # Bit shift positions
        self.node_id_shift = self.sequence_bits
        self.timestamp_left_shift = self.sequence_bits + self.node_id_bits
        
        # State tracking
        self.last_timestamp = -1
        self.sequence = 0
        self.lock = threading.Lock()

    def _current_timestamp(self) -> int:
        """Returns the current system time in milliseconds."""
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        """Spins until the system clock advances to the next millisecond."""
        timestamp = self._current_timestamp()
        while timestamp <= last_timestamp:
            timestamp = self._current_timestamp()
        return timestamp

    def generate(self) -> int:
        """Generates a thread-safe, unique, time-ordered 64-bit ID."""
        with self.lock:
            timestamp = self._current_timestamp()
            
            # Reject requests if the system clock moved backward (NTP sync anomaly)
            if timestamp < self.last_timestamp:
                raise RuntimeError(
                    f"Clock moved backwards! Rejecting requests for {self.last_timestamp - timestamp}ms"
                )
                
            if timestamp == self.last_timestamp:
                # Same millisecond: increment sequence and wrap using bitmask
                self.sequence = (self.sequence + 1) & self.max_sequence
                if self.sequence == 0:
                    # Sequence overflow in this millisecond: block until next millisecond
                    timestamp = self._wait_next_millis(self.last_timestamp)
            else:
                # Fresh millisecond: reset sequence counter
                self.sequence = 0
                
            self.last_timestamp = timestamp
            
            # Bitwise packaging into a 64-bit integer
            snowflake_id = (
                ((timestamp - self.epoch) << self.timestamp_left_shift) |
                (self.node_id << self.node_id_shift) |
                self.sequence
            )
            return snowflake_id

def calculate_epoch_ms(year: int, month: int, day: int) -> int:
    """Helper to generate a precise custom millisecond epoch."""
    dt = datetime(year, month, day, tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


# ==========================================
# Execution Demo
# ==========================================
if __name__ == "__main__":
    # Example: How to generate a customized custom epoch if needed
    # my_epoch = calculate_epoch_ms(2026, 9, 29) 
    
    # Initialize generator for node #1
    generator = SnowflakeGenerator(node_id=1)
    
    print("Generating unique IDs:")
    for _ in range(5):
        print(generator.generate())
