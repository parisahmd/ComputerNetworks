"""
A very simple Python traceroute(8) implementation

"""

import socket
import random
import struct
from multiprocessing import Process

__all__ = ['Tracer']

ICMP_ECHO_REQUEST = 8
ICMP_CODE = socket.getprotobyname('icmp')

class Tracer(object):

    def __init__(self, dst, hops, port, startTTL, maxTry, packetSize, maxTTL, ansTime):
        """
        Initializes a new tracer object

        Args:
            dst  (str): Destination host to probe
            hops (int): Max number of hops to probe

        """
        self.dst = dst
        self.hops = hops
        self.startTTL = startTTL
        self.port = port
        self.maxTry = maxTry
        self.packetSize = packetSize
        self.maxTTL = maxTTL
        self.ansTime = ansTime

        print("init")

    #         # Pick up a random port in the range 33434-33534
    #         self.port = random.choice(range(33434, 33535))

    def run(self):
        """
        Run the tracer

        Raises:
            IOError

        """
        try:
            dst_ip = socket.gethostbyname(self.dst)
        except socket.error as e:
            raise IOError('Unable to resolve {}: {}', self.dst, e)

        text = 'traceroute to {} ({}), {} hops max'.format(
            self.dst,
            dst_ip,
            self.hops
        )

        print(text)

        for tryNumber in range(self.maxTry):
            print 'tryNumber =',tryNumber
            receiver = self.create_receiver()
            sender = self.create_sender()
            packet = self.create_packet(self.packetSize)
            sender.sendto(packet, (self.dst, self.port))

            addr = None
            try:
                # answer_process = Process(target=receiver)
                data, addr = receiver.recvfrom(1024)
                # data, addr = answer_process.start().recvfrom(1024)
                # answer_process.join(timeout=self.ansTime)
                # answer_process.terminate()
            except socket.error as e:
                raise IOError('Socket error: {}'.format(e))
            finally:
                receiver.close()
                sender.close()

            if addr:
                print('{:<4} {}'.format(self.startTTL, addr[0]))
            else:
                print('{:<4} *'.format(self.startTTL))

            self.startTTL += 1

            if addr[0] == dst_ip:
                print ('reach hop')
                break
            elif self.startTTL >= self.maxTTL:
                print('TTL reach maxTTL')
                break

    def create_receiver(self):
        """
        Creates a receiver socket

        Returns:
            A socket instance

        Raises:
            IOError

        """
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_RAW,
            proto=socket.IPPROTO_ICMP
        )

        try:
            s.bind(('', self.port))
        except socket.error as e:
            raise IOError('Unable to bind receiver socket: {}'.format(e))

        return s

    def create_sender(self):
        """
        Creates a sender socket

        Returns:
            A socket instance

        """
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_DGRAM,
            proto=socket.IPPROTO_ICMP
        )

        s.setsockopt(socket.SOL_IP, socket.IP_TTL, self.startTTL)

        return s



    def checksum(self, source_string):
        # I'm not too confident that this is right but testing seems to
        # suggest that it gives the same answers as in_cksum in ping.c.
        sum = 0
        count_to = (len(source_string) / 2) * 2
        count = 0
        while count < count_to:
            this_val = ord(source_string[count + 1]) * 256 + ord(source_string[count])
            sum = sum + this_val
            sum = sum & 0xffffffff  # Necessary?
            count = count + 2
        if count_to < len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff  # Necessary?
        sum = (sum >> 16) + (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff
        # Swap bytes. Bugger me if I know why.
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def create_packet(self, size):
        id = random.choice(range(0, 2000))
        """Create a new echo request packet based on the given "id"."""
        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0, 0, id, 1)
        data = size * 'Q'
        # Calculate the checksum on the data and the dummy header.
        my_checksum = self.checksum(header + data)
        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        header = struct.pack('bbHHh', ICMP_ECHO_REQUEST, 0,
                             socket.htons(my_checksum), id, 1)
        return header + data


def main():
    maxTry = 5
    maxTTL = 15
    startTTL = 10
    initialPort = 33435
    packetSize = 20
    maxWait = 10
    dstHost = 'google.com'
    hops = 30
    trc = Tracer(dstHost, hops, initialPort, startTTL, maxTry, packetSize, maxTTL, maxWait)
    trc.run()
    print("Hello World!")

if __name__ == "__main__":
    main()
