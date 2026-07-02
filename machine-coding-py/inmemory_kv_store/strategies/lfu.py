from collections import defaultdict, OrderedDict

class LFU:
    def __init__(self):
        self.key_to_freq = {}                     # key -> frequency
        self.freq_map = defaultdict(OrderedDict)  # freq -> OrderedDict{key: None}; front = LRU
        self.min_freq = 0

    def touch(self, k):
        # New key: register at frequency 1.
        if k not in self.key_to_freq:
            self.key_to_freq[k] = 1
            self.freq_map[1][k] = None
            self.min_freq = 1
            return

        # Existing key: move it from freq -> freq + 1.
        freq = self.key_to_freq[k]      # Get frequency of key from key_to_freq mapping
        del self.freq_map[freq][k]      # delete key from freq_map, as freq of key will be increased
        if not self.freq_map[freq]:     # check if freq_map is empty after above delete
            del self.freq_map[freq]     # if yes, delete freq entry from freq_map
            if self.min_freq == freq:   
                self.min_freq += 1      # increment min_freq as freq is deleted from freq_map 
        self.freq_map[freq + 1][k] = None         # appended at end = MRU
        self.key_to_freq[k] = freq + 1

    def evict(self, data):
        # Least-frequently-used bucket; front of it is least-recently-used (tie-break).
        k, _ = self.freq_map[self.min_freq].popitem(last=False)
        if not self.freq_map[self.min_freq]:
            del self.freq_map[self.min_freq]
        del self.key_to_freq[k]
        data.pop(k, None)
        return k

    def remove(self, k):
        freq = self.key_to_freq.pop(k, None)
        if freq is None:
            return
        del self.freq_map[freq][k]
        if not self.freq_map[freq]:
            del self.freq_map[freq]
            if self.min_freq == freq:
                self.min_freq = min(self.freq_map, 0)
