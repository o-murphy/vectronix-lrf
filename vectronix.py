import enum

RANGING_RESPONSE_LEN = 11
ACK = b'>'  # 0x3E
NACK = b'!'  # 0x21
END = b'\r'  # 0x0D
COMMA = b","  # 0x2c


class Command(enum.Enum, bytes):
    GET_RANGE = b"Md1"
    SW_HW_INFO = b"Iv1"
    SELF_TEST = b"Tb1"
    LPCL_MODE = b"Tl1"


class RangingStatus(enum.Enum, bytes):
    VALID = b'v'
    ERROR = b'R'
    UNKNOWN = 0


class LPCLMode(enum.IntEnum):
    DEACTIVATE = 0
    LEVEL_1 = 1
    LEVEL_2 = 2
    LEVEL_3 = 3
    LEVEL_4 = 4
    LEVEL_5 = 5
    LEVEL_6 = 6


class VectronixRangeFinder:
    def __init__(self, read, write):
        self._read = read
        self._write = write

    def send_command(self, command: Command, lpcl_mode: LPCLMode = None):
        opcode = COMMA + str(lpcl_mode).encode('ascii') if lpcl_mode else b""
        buffer = ACK + command + opcode + END
        self._write(buffer)

    def read_response(self):
        while True:
            response = self._read(1)
            if response == END:
                continue
            if response == NACK:
                raise ValueError("Invalid command")
            if response == ACK:
                response += self._read(RANGING_RESPONSE_LEN - 1)
                if len(response) != 11 or response[-1] != 0x0D:  # Validate response length and <CR> at the end
                    raise ValueError("Invalid response format")

            return response

    @staticmethod
    def parse_range(response: bytes):
        status, measured_range, checksum = response[0:1], response[1:8], response[8:10]

        VectronixRangeFinder.check_crc(response)

        response = {
            'range': None,
            'status': None,
            'error': None,
        }

        if status == RangingStatus.VALID:
            response = {
                'range': int(measured_range.decode('ascii')) / 100,
                'status': RangingStatus.VALID,
                'error': None,
            }
        else:
            response = {
                'range': None,
                'status': status == RangingStatus.ERROR or RangingStatus.UNKNOWN,
                'error': response[4:8],
            }

        return response

    @staticmethod
    def check_crc(response: bytes):
        # Extract the data and CRC from the response
        data = response[:8]
        crc_received = response[-3:-1].decode('utf-8')  # Decode received CRC

        # Calculate the CRC from the data
        crc_calculated = f"{sum(data) & 0xFF:02X}"  # Convert to 2-character hex
        # return crc_calculated == crc_received
        if not crc_received == crc_calculated:
            raise ValueError("Invalid CRC")


if __name__ == "__main__":
    import serial

    uart = serial.Serial(timeout=1)

    lrf = VectronixRangeFinder(uart.read, uart.write)
