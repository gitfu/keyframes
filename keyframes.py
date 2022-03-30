#!/usr/bin/env python3

from functools import partial
import sys
from threefive import Stream




class KeyFramer(Stream):
    """
    KeyFramer is used find keyframes in h264 streams
    """

    def __init__(self, tsdata):
        """
        __init__

        tsdata is a file or http/https or udp,or multicast url
        for a mpegts stream with h264  or h265 video.
        """
        super().__init__(tsdata)

    @staticmethod
    def is_keyframe(pkt):
        if not pkt[3] & 0x20:
            return False
        if pkt[5] & 0x10:
            if pkt[5] &  0x40:
              #  print("keyframe")
                return True    
        if pkt[5] & 0xA8:
            #print("keyframe")
            return True
        return False

    @staticmethod
    def is_idr(pkt):
        """
        _is_idr is fast and loose idr detection
        """
        if b"\x00\x00\x01\x65" in pkt:
            return True
        return False

    @staticmethod
    def as_90k(ticks):
        """
        as_90k returns ticks as 90k clock time
        """
        return round((ticks / 90000.0), 6)

    def find_keyframes(self):
        """
        find_keyframes parses the stream for keyframes
        and returns a list of pts times.
        """
        keyframe_list = []
        if self._find_start():
            for pkt in iter(partial(self._tsdata.read, self._PACKET_SIZE), b""):
                keyframe_pts = self._parse(pkt)
                if keyframe_pts:
                    keyframe_list.append(keyframe_pts)
        self._tsdata.close()
        if len(keyframe_list) == 0:
            print("no keyframes found \n\n")
        return keyframe_list

    def pid2pts(self, pid):
        """
        pid2pts give a pid, returns the pts time
        """
        if pid in self._pid_prgm:
            prgm = self._pid_prgm[pid]
            return self.as_90k(self._prgm_pts[prgm])
        return None

    def show_pts(self,pkt):
        pid = self._parse_pid(pkt[1], pkt[2])
        pts = self.pid2pts(pid)
        if pts:
            print(pid,pts)
            return pts
        return None

    def _parse(self, pkt):
        super()._parse(pkt)
        
        if self._pusi_flag(pkt):
            if self.is_keyframe(pkt):
                return self.show_pts(pkt)
        if self.is_idr(pkt):
            return self.show_pts(pkt)    
        return None


if __name__ == "__main__":
    args = sys.argv[1:]
    for arg in args:
        print(arg)
        keyframer = KeyFramer(arg)
        keyframer.find_keyframes()
