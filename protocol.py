import enum
import struct

START_OF_COMMAND = 0x3E  # "<" Start of command
UPPER_CASE_LETTERS = range(0x41, 0x5a, 1)
LOWER_CASE_LETTERS = range(0x61, 0x7a, 1)
NUMBER = range(0x30, 0x39, 1)
END_OF_COMMAND = 0x0D

VALID_COMMAND_RESPONSE = ACK = 0x3C
INVALID_COMMAND_RESPONSE = NACK = 0x21


class CommandBuilder:
    def __init__(self):
        # Format definitions for struct
        self.base_format = ">c2scc"  # '>' (start), uppercase + lowercase letters, optional number, '<CR>'
        self.extended_format = ">c2sdsdc"  # '>' (start), uppercase + lowercase letters, optional number,
        # digit, optional comma, second digit, '<CR>'

    def build_basic_command(self, uppercase, lowercase, number=None):
        """
        Build a basic command structure.
        """
        start = b">"
        end = b"\r"
        # Build the binary command
        if number is not None:
            number_bytes = str(number).encode('ascii')
            packed_data = struct.pack(
                self.base_format,
                start,
                f"{uppercase}{lowercase}".encode('ascii'),
                number_bytes,
                end
            )
        else:
            packed_data = struct.pack(
                ">c2sc",
                start,
                f"{uppercase}{lowercase}".encode('ascii'),
                end
            )
        return packed_data

    def build_extended_command(self, uppercase, lowercase, first_param, second_param=None):
        """
        Build an extended command structure.
        """
        start = b">"
        end = b"\r"
        comma = b"," if second_param is not None else b""
        # Build the binary command
        if second_param is not None:
            packed_data = struct.pack(
                self.extended_format,
                start,
                f"{uppercase}{lowercase}".encode('ascii'),
                float(first_param),
                comma,
                float(second_param),
                end,
            )
        else:
            packed_data = struct.pack(
                ">c2sdsc",  # Format without the second parameter and comma
                start,
                f"{uppercase}{lowercase}".encode('ascii'),
                float(first_param),
                end,
            )
        return packed_data


class DistanceMeasurement:
    def __init__(self):
        # Input command for range measurement
        self.range_request = ">Md1\r".encode('ascii')

    @staticmethod
    def parse_response(response):
        """
        Parses the response from the device and extracts distance measurement data.

        Response format:
        1. Z (1 byte): 'v' for valid distance or 'R' for error.
        2. XXXXXX (7 bytes): Measured range value.
        3. YY (2 bytes): Checksum.
        4. <CR> (1 byte): End character (ASCII 0x0D).

        Each response line is 11 characters.
        """
        if len(response) != 11 or response[-1] != 0x0D:  # Validate response length and <CR> at the end
            raise ValueError("Invalid response format")

        # Unpack the response
        status, measured_range, checksum = response[0:1], response[1:8], response[8:10]

        # Convert checksum to hexadecimal
        # checksum_value = int(checksum.decode('ascii'), 16)

        measured_range_value = None
        error_code = None
        # Interpret status
        if status == b'v':
            range_status = "Valid"
            measured_range_value = int(measured_range.decode('ascii')) / 100
        elif status == b'R':
            range_status = "Error"
            error_code = response[4:8]
        else:
            range_status = "Unknown"
            error_code = response[4:8]

        # Convert range value to integer

        return {
            "Status": range_status,
            "Measured Range": measured_range_value or error_code,  # Convert to meters
            "Checksum": DistanceMeasurement.check_crc(response),
        }

    @staticmethod
    def check_crc(response: bytes):
        # Extract the data and CRC from the response
        data = response[:8]
        crc_received = response[-3:-1].decode('utf-8')  # Decode received CRC

        # Calculate the CRC from the data
        crc_calculated = f"{sum(data) & 0xFF:02X}"  # Convert to 2-character hex
        return crc_calculated == crc_received





def check_base_command_build(builder):
    # Basic command
    basic_command = builder.build_basic_command(uppercase="A", lowercase="b", number=5)
    print("Basic Command:", basic_command)

    # Basic command no num
    basic_command = builder.build_basic_command(uppercase="A", lowercase="b")
    print("Basic Command:", basic_command)


def check_extended_command_build(builder):
    # Extended command with two parameters
    extended_command = builder.build_extended_command(uppercase="X", lowercase="y", first_param=123,
                                                      second_param=456)
    print("Extended Command:", extended_command)

    # Extended command with only one parameter
    extended_command_single_param = builder.build_extended_command(uppercase="Z", lowercase="p", first_param=789)
    print("Extended Command (Single Param):", extended_command_single_param)


def check_responses(builder, parser):
    range_command = builder.build_basic_command(*'Md1')
    print("Range Command:", range_command, range_command == b'>Md1\r')

    strongest_return = b'v0108750DB\r'
    second_strongest_return = b'R000E301BB\r'
    weakest_return = b'R000E301BB\r'
    print("Range command response",
          parser.parse_response(strongest_return),
          parser.parse_response(strongest_return)["Measured Range"] == 1087.5)
    print("Range command response", parser.parse_response(b'v1234550DA\r'))
    print("Range command response", parser.parse_response(b'v0222200CE\r'))
    print("Range command response", parser.parse_response(second_strongest_return))
    print("Range command response", parser.parse_response(weakest_return))


# Example Usage
if __name__ == "__main__":
    builder = CommandBuilder()
    parser = DistanceMeasurement()

    check_base_command_build(builder)
    check_responses(builder, parser)

    # check_extended_command_build(builder)
