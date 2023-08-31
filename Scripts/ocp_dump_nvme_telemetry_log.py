# *****************************************************************************
#
#          COPYRIGHT 2022-2023 SAMSUNG ELECTRONICS CO., LTD.
#                          ALL RIGHTS RESERVED
#
#   Permission is hereby granted to licensees of Samsung Electronics
#   Co., Ltd. products to use or abstract this computer program for the
#   sole purpose of implementing a product based on Samsung
#   Electronics Co., Ltd. products. No other rights to reproduce, use,
#   or disseminate this computer program, whether in part or in whole,
#   are granted.
#
#   Samsung Electronics Co., Ltd. makes no representation or warranties
#   with respect to the performance of this computer program, and
#   specifically disclaims any responsibility for any damages,
#   special or consequential, connected with the use of this program.
#
# *****************************************************************************
#
# History:
#
# 1/4/2023 - Initial script based on OCP Datacenter NVMe SSD SPecification v2.5 with comments from Mike Allison
# 1/5/2023 - Added the -v commandline option to version of this script
#          - The Data Area 1 FIFO information was changed start/end to start/size
# 1/6/2023 - Validated <spaces> are in the ASCI table for unused locations
#          - Validated the sorting of Strings tables
# 4/9/2023 - General refactor
#          - Fixed bug detecting 'critical_warning'
#          - Formatted with Black


import sys
import argparse
import os

version = 2.2
ocp_ver = "2.5r24"

# Parse the strings log file and return a dictionary of the form:
#
# Input:
#
#      strings : byte array of the entire string log file
#
# Output a dictionary containing the string log information
#
#      data = {'statistics' : {'hex(identifier)'                    : {'identifier'  : identifier,       # for all static identifiers in the string log page
#                                                                      'string'      : ASCII string}},
#              'events'     : {'hex(event_class) + hex(identifier)' : {'class'       : event_class,      # for all event identifiers in the string log page
#                                                                      'identifier'  : identifier,
#                                                                      'string'      : ASCII string}},
#              'vu events'  : 'hex(identifier)"                     : {'identifier'  : identifier,       # for all vu event identifiers in the string log page
#                                                                      'string'      : ASCII string}}}
#              'length'     : <length of the strings log page
def parse_strings(strings):
    print("Parsing String log page ...")

    s_len = len(strings)
    data = {"length": s_len}

    # The string log has to be atleast 432 bytes in length
    if s_len < 432:
        sys.exit(f"Strings log page size of {s_len} is less than the size of the header.")

    log_ver = strings[0]
    if log_ver != 1:
        sys.exit(f"Log Page Version of {log_ver} is not the correct value.")

    reserved = int.from_bytes(strings[1:15], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 15:1 are not cleared to 0h.")

    guid = int.from_bytes(strings[16:32], "little")
    if guid != 0xB13A83691A8F408B9EA495940057AA44:
        sys.exit(f"GUID value is not the correct value: 0x{guid:x}")

    size_dw = int.from_bytes(strings[32:39], "little")
    size = size_dw * 4
    if size != s_len:
        sys.exit(f"Log page dword size size value of {size_dw} idoes not match the size of the string log read of {s_len}")

    reserved = int.from_bytes(strings[40:63], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 15:1 are not cleared to 0h.")

    statistics_start_dw = int.from_bytes(strings[64:71], "little")
    statistics_start = statistics_start_dw * 4
    statistics_size_dw = int.from_bytes(strings[72:79], "little")
    statistics_size = statistics_size_dw * 4

    if statistics_size_dw != 0:
        if statistics_start != 432:
            sys.exit(f"Statistics Identifier String Table Start value is invalid: {statistics_start_dw}({statistics_start})")
        if (statistics_start + statistics_size) > s_len:
            sys.exit(f"Statistics Identifier String Table Size value is invalid: {statistics_size_dw}")
        statistics_start = 432  # set this value as events should start after the header
        if (statistics_size % 16) != 0:
            sys.exit(f"Statistics Identifier String Table Size value is not a multiple of 16: {statistics_size_dw}")

    event_start_dw = int.from_bytes(strings[80:87], "little")
    event_start = event_start_dw * 4
    event_size_dw = int.from_bytes(strings[88:95], "little")
    event_size = event_size_dw * 4

    if event_size_dw != 0:
        if event_start_dw != (statistics_start_dw + statistics_size_dw):
            sys.exit(f"Event Identifier String Table Start value is invalid: {event_start_dw}")
        if (event_start + event_size) > s_len:
            sys.exit(f"Event Identifier String Table Size value is invalid: {event_size_dw}")
        if (event_size % 16) != 0:
            sys.exit(f"Event Identifier String Table Size value is not a multiple of 16: {event_size}")

    vu_event_start_dw = int.from_bytes(strings[96:103], "little")
    vu_event_start = vu_event_start_dw * 4
    vu_event_size_dw = int.from_bytes(strings[104:111], "little")
    vu_event_size = vu_event_size_dw * 4

    if vu_event_size_dw != 0:
        if vu_event_start_dw != (event_start_dw + event_size_dw):
            sys.exit(f"VU Event Identifier String Table Start value is invalid: {event_start_dw}")
        if (vu_event_start + vu_event_size) > s_len:
            sys.exit(f"VU Event Identifier String Table Size value is invalid: {event_size_dw}")
        if (vu_event_size % 16) != 0:
            sys.exit(f"Event Identifier String Table Size value is not a multiple of 16: {vu_event_size}")

    ascii_start_dw = int.from_bytes(strings[112:119], "little")
    ascii_start = ascii_start_dw * 4
    ascii_size_dw = int.from_bytes(strings[120:127], "little")
    ascii_size = ascii_size_dw * 4

    if ascii_start_dw != (vu_event_start_dw + vu_event_size_dw):
        sys.exit(f"ASCII Table Start value is invalid: {ascii_start_dw}")

    if (ascii_start + ascii_size) > s_len:
        sys.exit(f"ASCII Table Size value is invalid: {ascii_size_dw}")

    # Extract the FIFO names of up to 16 characters
    data["fifo"] = {}
    for x in range(1, 16):
        fifo_val = int.from_bytes(strings[128 + ((x - 1) * 16) : 143 + ((x - 1) * 16)], "little")
        if fifo_val == 0:
            fifo_name = f"FIFO {x}"
        else:
            fifo_name = str(strings[128 + ((x - 1) * 16) : 143 + ((x - 1) * 16)])

        data["fifo"][str(x)] = {"name": fifo_name}

    reserved = int.from_bytes(strings[431:384], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 431:376 are not cleared to 0h.")

    # Parse statistics strings
    last_identifier = 0
    if statistics_size_dw > 0:
        print("Parsing String log page ... Statistics Identifiers Table")

        data["statistics"] = {}
        current_stat = statistics_start
        end_stat = current_stat + statistics_size

        while current_stat < end_stat:
            identifier = int.from_bytes(strings[current_stat : current_stat + 2], "little")
            if identifier < 0x8000:
                sys.exit(f"Statistic Identifier 0x{identifier:x} is not a vendor unique value.")

            if identifier < last_identifier:
                sys.exit(f"Idententifiers are not sorted current identifier: 0x{identifier:x} previous identifier: 0x{last_identifier:x}")
            elif identifier == last_identifier:
                sys.exit(f"Identicle idententifiers in the table: 0x{identifier:x}")

            reserved = strings[current_stat + 2]
            if reserved != 0:
                sys.exit(f"Statistic Identifier 0x{identifier:x} reserved field value of {reserved} is not cleared to 0h.")

            stat_len = strings[current_stat + 3] + 1  # convert 0's based number
            stat_offset_dw = int.from_bytes(strings[current_stat + 4 : current_stat + 12], "little")
            stat_offset = stat_offset_dw * 4

            if stat_offset_dw >= (ascii_size_dw):
                sys.exit(f"Statistic Identifier 0x{identifier:x} offset field value of {stat_offset_dw} is not within the ASCII Table.")

            if (stat_offset + stat_len) >= (ascii_size):
                sys.exit(f"Statistic Identifier 0x{identifier:x} size field value of {stat_len - 1} is not within the ASCII table.")

            reserved = int.from_bytes(strings[current_stat + 12 : current_stat + 16], "little")
            if reserved != 0:
                sys.exit(f"Statistic Identifier 0x{identifier:x} reserved field value of {reserved} is not cleared to 0h.")

            data["statistics"][hex(identifier)] = {
                "identifier": identifier,
                "string": str(strings[ascii_start + stat_offset : ascii_start + stat_offset + stat_len]),
            }

            # Validate the unused string locations are spaces
            mod = (ascii_start + stat_offset + stat_len) % 4
            if mod != 0:
                for x in range(4 - mod):
                    if int(strings[ascii_start + stat_offset + stat_len + x]) != 0x20:
                        sys.exit(
                            f"Unused ASCII table character is not set to <space> after the string: {data['statistics'][hex(identifier)]['string']}"
                        )

            current_stat += 16

    # Parse event strings
    if event_size_dw > 0:
        print("Parsing String log page ... Event Identifiers Table")

        data["events"] = {}
        current_event = event_start
        end_event = current_event + event_size

        previous_debug_class = 0

        while current_event < end_event:
            debug_class = strings[current_event]
            if (debug_class) < 0x80:
                sys.exit(f"Event class of 0x{debug_class:x} is not a vendor unique value.")

            if debug_class < previous_debug_class:
                sys.exit(
                    f"Debug class values are not sorted current debug class: 0x{debug_class:x} previous debug class: 0x{previous_debug_class:x}"
                )
            elif debug_class > previous_debug_class:
                previous_debug_class = debug_class

            identifier = int.from_bytes(strings[current_event + 1 : current_event + 3], "little")

            if identifier < last_identifier:
                sys.exit(f"Idententifiers are not sorted current identifier: 0x{identifier:x} previous identifier: 0x{last_identifier:x}")
            elif identifier == last_identifier:
                sys.exit(f"Identicle idententifiers in the table: 0x{identifier:x}")

            event_len = strings[current_event + 3] + 1  # convert 0's based number
            event_offset_dw = int.from_bytes(strings[current_event + 4 : current_event + 12], "little")
            event_offset = event_offset_dw * 4

            if event_offset_dw >= (ascii_size_dw):
                sys.exit(f"Event Identifier 0x{identifier:x} offset field value of {event_offset_dw} is not within the ASCII table.")

            if (event_offset + event_len) >= (ascii_size):
                sys.exit(f"Event Identifier 0x{identifier:x} size field value of {event_len - 1} is not within the ASCII table.")

            reserved = int.from_bytes(strings[current_event + 12 : current_event + 16], "little")
            if reserved != 0:
                sys.exit(f"Event Identifier 0x{identifier:x} reserved field value in bytes 15:12 are not cleared to 0h.")

            data["events"][hex(debug_class) + hex(identifier)] = {
                "class": debug_class,
                "identifier": identifier,
                "string": str(strings[ascii_start + event_offset : ascii_start + event_offset + event_len]),
            }

            # Validate the unused string locations are spaces
            mod = (ascii_start + event_offset + event_len) % 4
            if mod != 0:
                for x in range(4 - mod):
                    if int(strings[ascii_start + event_offset + event_len + x]) != 0x20:
                        sys.exit(
                            f"Unused ASCII table character is not set to <space> after the string: {data['events'][hex(debug_class) + hex(identifier)]['string']}"
                        )

            current_event += 16

    # Parse VU event strings
    if vu_event_size_dw > 0:
        print("Parsing String log page ... Vender Unique (VU) Event Identifiers Table")

        data["vu_events"] = {}
        current_vu_event = vu_event_start
        end_vu_event = current_vu_event + vu_event_size

        previous_debug_class = 0

        while current_vu_event < end_vu_event:
            debug_class = strings[current_vu_event]
            if (debug_class < 1) or (debug_class > 9):
                sys.exit(f"VU Event byte 0 is not a valid VU Header class: {debug_class}")

            if debug_class < previous_debug_class:
                sys.exit(
                    f"Debug class values are not sorted current debug class: 0x{debug_class:x} previous debug class: 0x{previous_debug_class:x}"
                )
            elif debug_class > previous_debug_class:
                previous_debug_class = debug_class

            identifier = int.from_bytes(strings[current_vu_event + 1 : current_vu_event + 3], "little")

            if identifier < last_identifier:
                sys.exit(f"Idententifiers are not sorted current identifier: 0x{identifier:x} previous identifier: 0x{last_identifier:x}")
            elif identifier == last_identifier:
                sys.exit(f"Identicle idententifiers in the table: 0x{identifier:x}")

            vu_event_len = strings[current_vu_event + 3] + 1  # convert 0's based number
            vu_event_offset_dw = int.from_bytes(strings[current_vu_event + 4 : current_vu_event + 12], "little")
            vu_event_offset = vu_event_offset_dw * 4

            if vu_event_offset_dw > (ascii_size_dw):
                sys.exit(f"VU Event Identifier 0x{identifier:x} offset value of {vu_event_offset_dw} is not within the ASCII table.")

            if (vu_event_offset + vu_event_len) > ascii_size:
                sys.exit(f"VU Event Identifier 0x{identifier:x} size value of {event_len - 1} is not within the ASCII table.")

            reserved = int.from_bytes(strings[current_vu_event + 12 : current_vu_event + 16], "little")
            if reserved != 0:
                sys.exit(f"VU Event Identifier 0x{identifier:x} reserved field value in bytes 15:12 are not cleared to 0h.")

            data["vu_events"][hex(debug_class) + hex(identifier)] = {
                "class": debug_class,
                "identifier": identifier,
                "string": str(strings[ascii_start + vu_event_offset : ascii_start + vu_event_offset + vu_event_len]),
            }
            # Validate the unused string locations are spaces
            mod = (ascii_start + vu_event_offset + vu_event_len) % 4
            if mod != 0:
                for x in range(4 - mod):
                    if int(strings[ascii_start + vu_event_offset + vu_event_len + x]) != 0x20:
                        sys.exit(
                            f"Unused ASCII table character is not set to <space> after the string: {data['vu_events'][hex(debug_class) + hex(identifier)]['string']}"
                        )

            current_vu_event += 16

    return data


# Parse and print the VU Reason Code
#
# Input:
#      reason : bytearray of the reason code
#
# Output: None
def parse_vu_reason_code(reason):
    print("\t\tReason Identifier: ")

    reason_start = 384
    err_id = int.from_bytes(reason[0:64], "little")
    print(f"\t\t\tError ID: 0x{err_id:x}")

    file_id = int.from_bytes(reason[64:72], "little")
    print(f"\t\t\tFile ID: 0x{file_id:x}")

    line_num = int.from_bytes(reason[72:74], "little")
    print(f"\t\t\tLine Number ID: {line_num}")

    flags = reason[74]
    if (flags & 0x01) != 0:
        print("\t\t\tLine Number is valid")
    else:
        print("\t\tLine Number is not valid")
    if (flags & 0x02) != 0:
        print("\t\t\tFile ID is valid")
    else:
        print("\t\t\tFile ID is not valid")
    if (flags & 0x04) != 0:
        print("\t\t\tError ID is valid")
    else:
        print("\t\tError ID is not valid")
    if (flags & 0x08) != 0:
        print("\t\t\tVU Reason Extension is valid")
    else:
        print("\t\tVU Reason Extension is not valid")
    if (flags & 0xF0) != 0:
        sys.exit("Reserved field in the Reason Idenifier byte 74 is not cleared to 0h")

    reserved = int.from_bytes(reason[75:96], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 75:95 are not cleared to 0h.")

    vu_reason_code = int.from_bytes(reason[96:128], "little")
    print(f"\t\t\tVU Reason Extension: 0x{vu_reason_code:x}")


# NVMe Telemetry scopestrings
telemetry_scope_str = [
    "Not Reported",  # 0
    "Controller",  # 1
    "NVM subsystem",  # 2
]

# Parse and print the NVMe Telemetry log page header
#
# Input:
#      telemetry_header : bytearray of the Telemetry log page header
#      tel_len          : length of telemetry
#
# Output:
#
#     (Data Area 1 Last Block, Data Area 2 Last Block, Data Area 3 Last Block, Data Area 4 Last Block)


def parse_telemetry_header(telemetry_header, tel_len):
    # Validate the header size
    if len(telemetry_header) != 512:
        sys.exit(f"Invalid Telemetry log page header size: {len(telemetry_header)}.")

    # Validate the telemetry header
    log_id = telemetry_header[0]
    if log_id != 7 and log_id != 8:
        sys.exit(f"Telemetry Log Identifier of {log_id} is not the correct value.")

    if log_id == 7:
        print("\nParsng Telemetry Host-Initiated Log Page ... \n")
    else:
        print("\nParsng Telemetry Controller-Initiated Log Page ... \n")
    print("\tLog Page Header:\n")

    reserved = int.from_bytes(telemetry_header[1:5], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 4:1 are not cleared to 0h.")

    ieee = int.from_bytes(telemetry_header[5:8], "little")
    print(f"\t\tIEEE OUI Identifier (IEEE): 0x{ieee:x}")

    data_area_1_last_block = int.from_bytes(telemetry_header[8:10], "little")
    if (512 + (data_area_1_last_block * 512)) > tel_len:
        sys.exit(f"Data Area 1 size {data_area_1_last_block * 512} is larger than telemetry data.")
    print(f"\t\tTelemetry Host-Initiated Data Area 1 Last Block: {data_area_1_last_block}")

    if data_area_1_last_block != 32:
        sys.exit(f"Data Area 1 size not per OCP spec of 16K bytes: {data_area_1_last_block}")

    data_area_2_last_block = int.from_bytes(telemetry_header[10:12], "little")
    if (512 + (data_area_2_last_block * 512)) > tel_len:
        sys.exit(f"Data Area 2 size {data_area_1_last_block * 512} is larger than telemetry data.")
    print(f"\t\tTelemetry Host-Initiated Data Area 2 Last Block: {data_area_2_last_block}")

    data_area_3_last_block = int.from_bytes(telemetry_header[12:14], "little")
    if (512 + (data_area_3_last_block * 512)) > tel_len:
        sys.exit(f"Data Area 3 size {data_area_3_last_block * 512} is larger than telemetry data.")
    print(f"\t\tTelemetry Host-Initiated Data Area 3 Last Block: {data_area_3_last_block}")

    reserved = int.from_bytes(telemetry_header[14:16], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 15:14 are not cleared to 0h.")

    data_area_4_last_block = int.from_bytes(telemetry_header[16:20], "little")
    if (512 + (data_area_4_last_block * 512)) > tel_len:
        sys.exit(f"Data Area 4 size {data_area_4_last_block * 512} is larger than telemetry data.")
    print(f"\t\tTelemetry Host-Initiated Data Area 4 Last Block: {data_area_4_last_block}")

    # Parse the remaining header based on the telemtry log type
    if log_id == 7:  # NVMe Telemetry Host-Initiated log Page
        reserved = int.from_bytes(telemetry_header[20:380], "little")
        if reserved != 0:
            sys.exit("Reserved bytes 379:20 are not cleared to 0h.")

        host_scope = telemetry_header[380]
        if host_scope > 2:
            sys.exit(f"Telemetry Host-Initiated Scope has an invalid number of : {host_scope}")
        print(f"\t\tTelemetry Host-Initiated Scope: {telemetry_scope_str[host_scope]}")

        host_gen_num = telemetry_header[381]
        print(f"\t\tTelemetry Host-Initiated Data Generation Number: {host_gen_num}")

        data_available = telemetry_header[382]
        if data_available > 1:
            sys.exit(f"Telemetry Controller-Initiated Data Available has an invalid number of : {data_available}")
        print(f"\t\tTelemetry Controller-Initiated Data Available: {data_available}")

        controller_gen_num = telemetry_header[383]
        print(f"\t\tTelemetry Controller-Initiated Data Generation Number: {controller_gen_num}")
    else:  # NVMe Telemetry Controller-Initiated log Page
        reserved = int.from_bytes(telemetry_header[20:381], "little")
        if reserved != 0:
            sys.exit("Reserved bytes 380:20 are not cleared to 0h.")

        controller_scope = telemetry_header[381]
        if controller_scope > 2:
            sys.exit(f"Telemetry Controller-Initiated Scope has an invalid number of : {controller_scope}")
        print(f"\t\tTelemetry Controller-Initiated Scope: {telemetry_scope_str[controller_scope]}")

        data_available = telemetry_header[382]
        if data_available == 1:
            print("\t\tTelemetry Controller-Initiated Data Available: Available")
        elif data_available == 0:
            sys.exit("Telemetry Controller-Initiated Data Available states no data exists")
        else:
            sys.exit(f"Telemetry Controller-Initiated Data Available has an invalid number of : {data_available}")

        controller_gen_num = telemetry_header[383]
        print(f"\t\tTelemetry Controller-Initiated Data Generation Number: {controller_gen_num}")

    parse_vu_reason_code(telemetry_header[384:512])

    return (data_area_1_last_block, data_area_2_last_block, data_area_3_last_block, data_area_4_last_block)


# Parse and print NVMe Timestamp
#
# Input:
#      timestamp  : bytearray of a NVMe timestamp
#      pre_test   : text to print first (i.e., tabs for example)
#
# Output: None
#
def parse_nvm_timestamp(timestamp, pre_text):
    if len(timestamp) != 8:
        sys.exit("Timestamp byte array is not 8 bytes in length.")

    print(f"{pre_text}\t\tTimestamp: ")
    time = int.from_bytes(timestamp[0:6], "little")
    print(f"{pre_text}\t\t\tTime: {time}")

    attr = timestamp[6]

    if (attr & 0xF0) != 0:
        sys.exit("Reserved field in the timestamp byte 6 is not cleared to 0h")
    if (attr & 0x01) != 0:
        print(
            f"{pre_text}\t\t\tThe controller may have stopped counting during vendor specific intervals after the Timestamp value was initialized."
        )
    else:
        print(f"{pre_text}\t\t\tThe controller counted time in milliseconds continuously since the Timestamp value was initialized.")
    timestamp_origin = attr >> 1
    if timestamp_origin == 0:
        print(f"{pre_text}\t\t\tThe Timestamp field was initialized to 0h by a Controller Level Reset")
    elif timestamp_origin == 1:
        print(f"{pre_text}\t\t\tThe Timestamp field was initialized with a Timestamp value using a Set Features command")
    else:
        print(f"{pre_text}\t\t\tThe Timestamp Origin field has an invalid value: {timestamp_origin}")

    reserved = timestamp[7]
    if reserved != 0:
        sys.exit("Reserved byte 7 in the Timestamp is not cleared to 0h.")


# Parse and print the SMART / Health Information log page (Log Identifier 02h)
#
# Input:
#      smart  : bytearray of a NVMe SMART / Health Information log page
#
# Output: None
#
def parse_smart_health_info(smart):
    if len(smart) != 512:
        sys.exit("Size of the input bytearray for the NVMe SMART / Health Information log page is not 512 bytes.")

    print("\t\tSMART / Health Information log page 02h:")
    critical_warning = smart[0]
    if critical_warning == 0:
        print("\t\t\tNo critical warnings")
    else:
        if critical_warning & 0x01:
            print("\t\t\tAvailable spare capacity warning.")
        if critical_warning & 0x02:
            print("\t\t\tCritical temperature warning.")
        if critical_warning & 0x04:
            print("\t\t\tCritical reliability warning.")
        if critical_warning & 0x08:
            print("\t\t\tMedia in read-only warning.")
        if critical_warning & 0x10:
            print("\t\t\tVolatile memory backup device failure warning.")
        if critical_warning & 0x20:
            print("\t\t\tPersistent Memory Region warning.")
        if critical_warning & 0xC0:
            sys.exit("Reserved bits 7:6 in byte 0 is not cleared to 0h.")

    comp_temp = int.from_bytes(smart[1:3], "little")
    print(f"\t\t\tComposite Temperature: {comp_temp} Kelvin.")

    av_spare = smart[3]
    if av_spare > 100:
        sys.exit(f"Available Spare value of {av_spare} is invalid.")
    print(f"\t\t\tAvailable Spare: {av_spare}%.")

    av_spare = smart[4]
    if av_spare > 100:
        sys.exit(f"Available Spare Threshold value of {av_spare} is invalid.")
    print(f"\t\t\tAvailable Spare Threshold: {av_spare}%.")

    used = smart[5]
    print(f"\t\t\tPercent Used: {used}%.")

    critical_warning = smart[6]
    if critical_warning == 0:
        print("\t\t\tNo Endurance Group Summary critical warnings")
    else:
        if critical_warning & 0x01:
            print("\t\t\tEndurance Group Summary available spare capacity warning.")
        if critical_warning & 0x02:
            sys.exit("Reserved bit 1 in byte 6 is not cleared to 0h.")
        if critical_warning & 0x04:
            print("\t\t\tEndurance Group Summary critical reliability warning.")
        if critical_warning & 0x08:
            print("\t\t\tEndurance Group Summary namespace in read-only warning.")
        if critical_warning & 0xF0:
            sys.exit("Reserved bits 7:4 in byte 6 is not cleared to 0h.")

    reserved = int.from_bytes(smart[7:32], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 7:31 are not cleared to 0h.")

    data_units_read = int.from_bytes(smart[32:48], "little")
    print(f"\t\t\tData Units Read: {data_units_read}")

    data_units_written = int.from_bytes(smart[48:64], "little")
    print(f"\t\t\tData Units Written: {data_units_written}")

    host_read_commands = int.from_bytes(smart[64:80], "little")
    print(f"\t\t\tHost Read Command: {host_read_commands}")

    host_write_commands = int.from_bytes(smart[80:96], "little")
    print(f"\t\t\tHost Write Command: {host_write_commands}")

    busy = int.from_bytes(smart[96:112], "little")
    print(f"\t\t\tController Busy Time: {busy}")

    ps = int.from_bytes(smart[112:128], "little")
    print(f"\t\t\tPower Cycles: {ps}")

    poh = int.from_bytes(smart[128:144], "little")
    print(f"\t\t\tPower On Hours: {poh}")

    shut = int.from_bytes(smart[144:160], "little")
    print(f"\t\t\tUnsafe Shutdowns: {shut}")

    err = int.from_bytes(smart[160:176], "little")
    print(f"\t\t\tMedia and Data Integrity Errors: {err}")

    err = int.from_bytes(smart[176:192], "little")
    print(f"\t\t\tNumber of Error Information Log Entries: {err}")

    time = int.from_bytes(smart[192:196], "little")
    print(f"\t\t\tWarning Composite Temperature Time: {time}")

    time = int.from_bytes(smart[196:200], "little")
    print(f"\t\t\tCritical Composite Temperature Time: {time}")

    temp = int.from_bytes(smart[200:202], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 1 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 1: {temp} Kelvin.")

    temp = int.from_bytes(smart[202:204], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 2 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 2: {temp} Kelvin.")

    temp = int.from_bytes(smart[204:206], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 3 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 3: {temp} Kelvin.")

    temp = int.from_bytes(smart[206:208], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 4 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 4: {temp} Kelvin.")

    temp = int.from_bytes(smart[208:210], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 5 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 5: {temp} Kelvin.")

    temp = int.from_bytes(smart[210:212], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 6 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 6: {temp} Kelvin.")

    temp = int.from_bytes(smart[212:214], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 7 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 7: {temp} Kelvin.")

    temp = int.from_bytes(smart[214:216], "little")
    if temp == 0:
        print("\t\t\tTemperature Sensor 8 is not supported.")
    else:
        print(f"\t\t\tTemperature Sensor 8: {temp} Kelvin.")

    cnt = int.from_bytes(smart[216:220], "little")
    print(f"\t\t\tThermal Management Temperature 1 Transition Count: {cnt}")

    cnt = int.from_bytes(smart[220:224], "little")
    print(f"\t\t\tThermal Management Temperature 2 Transition Count: {cnt}")

    time = int.from_bytes(smart[224:228], "little")
    print(f"\t\t\tTotal Time for Thermal Management Temperature 1: {time}")

    time = int.from_bytes(smart[228:232], "little")
    print(f"\t\t\tTotal Time for Thermal Management Temperature 2: {time}")

    reserved = int.from_bytes(smart[232:512], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 511:232 are not cleared to 0h.")


# Parse and print the OCP SMART / Health Information Extension log page (Log Identifier C0h)
#
# Input:
#      smart  : bytearray of a OCP SMART / Health Information Extendion log page
#
# Output: None
#
def parse_smart_health_info_extension(smart):
    print(f"smart: {type(smart)}\n")
    if len(smart) != 512:
        sys.exit("Size of the input bytearray for the OCP SMART / Health Information Extension log page is not 512 bytes.")

    print("\t\tSMART / Health Information Extention log page C0h")

    cnt = int.from_bytes(smart[0:16], "little")
    print(f"\t\t\tPhysical Media Units Written: {cnt}")

    cnt = int.from_bytes(smart[16:32], "little")
    print(f"\t\t\tPhysical Media Units Read: {cnt}")

    cnt = int.from_bytes(smart[32:38], "little")
    print(f"\t\t\tBad User NAND Blocks Raw Count: {cnt}")

    norm = int.from_bytes(smart[38:40], "little")
    if norm > 100:
        sys.exit(f"Bad User NAND Blocks Normalized Value of {norm}% is invalid.")
    print(f"\t\t\tBad User NAND Blocks Normalized Value: {norm}")

    cnt = int.from_bytes(smart[40:46], "little")
    print(f"\t\t\tBad System NAND Blocks Raw Count: {cnt}")

    norm = int.from_bytes(smart[46:48], "little")
    if norm > 100:
        sys.exit(f"Bad System NAND Blocks Normalized Value of {norm}% is invalid.")
    print(f"\t\t\tBad System NAND Blocks Normalized Value: {norm}")

    cnt = int.from_bytes(smart[48:56], "little")
    print(f"\t\t\tXOR Recovery Count: {cnt}")

    cnt = int.from_bytes(smart[56:64], "little")
    print(f"\t\t\tUncorrectable Read Error Count: {cnt}")

    cnt = int.from_bytes(smart[64:72], "little")
    print(f"\t\t\tSoft ECC Error Count: {cnt}")

    cnt = int.from_bytes(smart[72:80], "little")
    print(f"\t\t\tEnd to End Correction Counts: {cnt}")

    used = smart[80]
    print(f"\t\t\tSystem Data % Used: {used}%.")

    cnt = int.from_bytes(smart[81:88], "little")
    print(f"\t\t\tRefresh Counts: {cnt}")

    cnt = int.from_bytes(smart[88:92], "little")
    print(f"\t\t\tMaximum User Data Erase Count: {cnt}")

    cnt = int.from_bytes(smart[92:96], "little")
    print(f"\t\t\tMinimum User Data Erase Count: {cnt}")

    cnt = smart[96]
    print(f"\t\t\tNumber of thermal throttling events: {cnt}")

    status_str = ["unthrottled", "first level throttle", "2nd level throttle", "3rd level throttle"]
    status = smart[97]
    if status > 4:
        sys.exit(f"Current Throttling Status value of {status} is invalid.")
    print(f"\t\t\tCurrent Throttling Status: {status_str[status]}")

    print("\t\t\tDSSD Specification Version:")

    ver = smart[98]
    if ver != 0:
        sys.exit(f"DSSD Specification Version - Errta Version value of {ver} is invalid.")
    print(f"\t\t\t\tErrta Version:{ver}")

    ver = int.from_bytes(smart[99:101], "little")
    if ver != 0:
        sys.exit(f"DSSD Specification Version - Point Version value of {ver} is invalid.")
    print(f"\t\t\t\tPoint Version:{ver}")

    ver = int.from_bytes(smart[101:103], "little")
    if ver != 5:
        sys.exit(f"DSSD Specification Version - Minor Version value of {ver} is invalid.")
    print(f"\t\t\t\tMinor Version:{ver}")

    ver = smart[103]
    if ver != 2:
        sys.exit(f"DSSD Specification Version - Major Version value of {ver} is invalid.")
    print(f"\t\t\t\tMajor Version:{ver}")

    cnt = int.from_bytes(smart[104:112], "little")
    print(f"\t\t\tPCIe Correctable Error Count: {cnt}")

    cnt = int.from_bytes(smart[112:116], "little")
    print(f"\t\t\tIncomplete Shutdowns: {cnt}")

    reserved = int.from_bytes(smart[116:120], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 119:116 are not cleared to 0h.")

    cnt = smart[120]
    if cnt > 100:
        sys.exit(f"% Free Blocks value of {cnt}% is invalid.")
    print(f"\t\t\t% Free Blocks: {cnt}%.")

    reserved = int.from_bytes(smart[121:128], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 127:121 are not cleared to 0h.")

    cnt = int.from_bytes(smart[128:130], "little")
    print(f"\t\t\tCapacitor Health: {cnt}%.")

    errata = smart[130]
    print(f"\t\t\tNVMe Errata Version: {chr(errata)}.")

    reserved = int.from_bytes(smart[131:136], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 135:131 are not cleared to 0h.")

    cnt = int.from_bytes(smart[136:144], "little")
    print(f"\t\t\tUnaligned I/O: {cnt}")

    cnt = int.from_bytes(smart[144:152], "little")
    print(f"\t\t\tSecurity Version Number: 0x{cnt:x}")

    cnt = int.from_bytes(smart[152:160], "little")
    print(f"\t\t\tTotal NUSE: {cnt}")

    cnt = int.from_bytes(smart[160:176], "little")
    print(f"\t\t\tPLP Start Count: {cnt}")

    cnt = int.from_bytes(smart[176:192], "little")
    print(f"\t\t\tEndurance Estimate: {cnt}")

    cnt = int.from_bytes(smart[192:200], "little")
    print(f"\t\t\tPCIe Link Retraining Count: {cnt}")

    cnt = int.from_bytes(smart[200:208], "little")
    print(f"\t\t\tPower State Change Count: {cnt}")

    ver = int.from_bytes(smart[208:224], "little")
    print(f"\t\t\tHardware Version:{ver}")

    reserved = int.from_bytes(smart[224:494], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 493:224 are not cleared to 0h.")

    ver = int.from_bytes(smart[494:496], "little")
    if ver != 3:
        sys.exit(f"Log Page Version value of {ver} is invalid.")
    print(f"\t\t\tLog Page Version:{ver}")

    guid = int.from_bytes(smart[496:512], "little")
    if guid != 0xAFD514C97C6F4F9CA4F2BFEA2810AFC5:
        sys.exit(f"GUID value is not the correct value: 0x{guid:x}")
    print(f"\t\t\tLog Page GUID:0x{guid:x}")


# Parse and print the FIFO information in Data Area 1
#
# Input:
#      fifo_array  : bytearray of the data area 1 FIFO information specifying the data area, start and end.
#
# Output: A disctionary of FIFOs location within Data Area 1 & 2
#
#     {'<fifo #>' : {'data area' : data area number,
#                    'start_dw'  : Dword start location for the FIFO in the data area
#                    'end_dw'    : Dword end location for the FIFO in the data area}
def get_fifo_data(fifo_array):
    fifo_area_str = ["Does not exist", "Data Area 1", "Data Area 2"]
    fifo = {}

    for x in range(1, 17):
        fifo_area = fifo_array[x - 1]
        if fifo_area > 2:
            sys.exit(f"Event FIFO {x} Data Area value of {fifo_area} is invalid.")

        fifo[str(x)] = {"data area": fifo_area}

        print(f"\t\tEvent FIFO {x}: {fifo_area_str[fifo_area]}")

    for x in range(1, 17):
        offset_fifo_start_dw = 16 + ((x - 1) * 16)

        fifo_start_dw = int.from_bytes(fifo_array[offset_fifo_start_dw : offset_fifo_start_dw + 8], "little")
        fifo_size_dw = int.from_bytes(fifo_array[offset_fifo_start_dw + 8 : offset_fifo_start_dw + 16], "little")

        fifo[str(x)]["start dw"] = fifo_start_dw
        fifo[str(x)]["size dw"] = fifo_size_dw

        print(f"\t\tEvent FIFO {x} Start (Dword): 0x{fifo_start_dw:x} (0x{fifo_start_dw * 4:x})")
        print(f"\t\tEvent FIFO {x} Size (Dword): 0x{fifo_size_dw:x} (0x{fifo_size_dw * 4:x})")

    return fifo


# Parse and print the statistics
# fmt: off
# OCP defined strings for identifiers 1-29
stats_ocp_str = ["Error, this entry does not exist.",  # 0
                 "Outstanding Admin Commands",         # 1
                 "Host Write Bandwidth",               # 2
                 "GC Write Bandwidth",                 # 3
                 "Active Namespaces",                  # 4
                 "Internal Write Workload",            # 5
                 "Internal Read Workload",             # 6
                 "Internal Write Queue Depth",         # 7
                 "Internal Read Queue Depth",          # 8
                 "Pending Trim LBA Count",             # 9
                 "Host Trim LBA Request Count",        # 10
                 "Current NVMe Power State",           # 11
                 "Current DSSD Power State",           # 12
                 "Program Fail Count",                 # 13
                 "Erase Fail Count",                   # 14
                 "Read Disturb Writes",                # 15
                 "Retention Writes",                   # 16
                 "Wear Leveling Writes",               # 17
                 "Read Recovery Writes",               # 18
                 "GC Writes",                          # 19
                 "SRAM Correctable Count",             # 20
                 "DRAM Correctable Count",             # 21
                 "SRAM Uncorrectable Count",           # 22
                 "DRAM Uncorrectable Count",           # 23
                 "Data Integrity Error Count",         # 24
                 "Read Retry Error Count",             # 25
                 "PERST Events Count",                 # 26
                 "Max Die Bad Block",                  # 27
                 "Max NAND Channel Bad Block",         # 28
                 "Minimum NAND Channel Bad Block",     # 29
]

# OCP defined behavior type definitions
behavior_type_str = ["Error, this entry does not exist.",                                                       # 0
                     "Saturating Counter - No  Reset Persistent - No  Power Cycle/PERST Persistent - No",       # 1
                     "Saturating Counter - No  Reset Persistent - Yes Power Cycle/PERST Persistent - Yes",      # 2
                     "Saturating Counter - Yes Reset Persistent - Yes Power Cycle/PERST Persistent - No",       # 3
                     "Saturating Counter - Yes Reset Persistent - Yes Power Cycle/PERST Persistent - Yes",      # 4
                     "Saturating Counter - Yes Reset Persistent - No  Power Cycle/PERST Persistent - No",       # 5
                     "Saturating Counter - No  Reset Persistent - Yes Power Cycle/PERST Persistent - No",       # 6
]

# OCP defined dword values for identifiers 1-29
dw_values = [1,     # 0
             1,     # 1
             1,     # 2
             1,     # 3
             1,     # 4
             2,     # 5
             2,     # 6
             1,     # 7
             1,     # 8
             2,     # 9
             2,     # 10
             1,     # 11
             1,     # 12
             2,     # 13
             2,     # 14
             4,     # 15
             4,     # 16
             4,     # 17
             2,     # 18
             2,     # 19
             1,     # 20
             1,     # 21
             1,     # 22
             1,     # 23
             1,     # 24
             1,     # 25
             1,     # 26
             2,     # 27
             2,     # 28
             2,     # 29
]
# fmt: on

# Parse and print a single statistic descriptor
#
# Input:
#      data area  : integer specify which data area the static was defined
#      statistics : bytearray of the remaining statistics descriptors to parse
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#      pre_string : alignment string
#
# Output: The length, in bytes, of the statistic descriptor at statistics[0]
def parse_a_statistic(data_area, statistics, strings, pre_string):
    offset = 0
    stat_len = len(statistics)

    # If the identifier is 0h, then end of the list of statistics
    identifier = int.from_bytes(statistics[offset : offset + 2], "little")
    if identifier == 0:
        sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} is invalid.")
    if (identifier > 29) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} is invalid.")

    if identifier >= 0x8000:
        idx = hex(identifier)
        if (idx in strings["statistics"]) == False:
            sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} does not exist in the Strings log page.")

    behavior_type = statistics[offset + 2]
    if (behavior_type == 0) or (behavior_type > 6):
        sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} behavior type value of {behavior_type} is invalid.")

    namespace = statistics[offset + 3]

    dw_len = int.from_bytes(statistics[offset + 4 : offset + 6], "little")
    if identifier < 30:
        if dw_len != dw_values[identifier]:
            sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} dword length value of {dw_len} is invalid.")
    if dw_len == 0:
        sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} dword length value of 0h is invalid.")
    if (offset + 4 + dw_len * 4) > stat_len:
        sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} dword length value of {dw_len} is invalid.")

    reserved = int.from_bytes(statistics[offset + 6 : offset + 8], "little")
    if reserved != 0:
        sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} reserved bytes 7:6 are not 0h.")

    # Determine the description
    if identifier < 0x8000:
        description = stats_ocp_str[identifier]
    else:
        description = strings["statistics"][hex(identifier)]["string"]

    print(f"\t\t{pre_string}Identifier        : 0x{identifier:x} ({identifier})")
    print(f"\t\t\t{pre_string}Behavior Type : {behavior_type} ({behavior_type_str[behavior_type]})")

    if namespace >= 128:
        print(f"\t\t\t{pre_string}Namespace     : {namespace & 127}")
    else:
        print(f"\t\t\t{pre_string}Namespace     : Not specified")

    print(f"\t\t\t{pre_string}Description   : {description}")

    # Special case some OCP fields
    if identifier == 0x1B:
        worst_per = statistics[offset + 8]
        if worst_per > 100:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} worst die % of bad blocks  value of {worst_per} is invalid."
            )
        reserved = statistics[offset + 9]
        if reserved != 0:
            sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved byte 1 is not 0h.")
        worst_raw = int.from_bytes(statistics[offset + 10 : offset + 12], "little")
        reserved = int.from_bytes(statistics[offset + 12 : offset + 16], "little")
        if reserved != 0:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved bytes 7:3 are not 0h."
            )

        print(f"\t\t\t{pre_string}Worst Die % of Bad Black         : {worst_per}%")
        print(f"\t\t\t{pre_string}Worst Die Raw Number of Bad Black: {worst_raw}")
    elif identifier == 0x1C:
        worst_per = statistics[offset + 8]
        if worst_per > 100:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} worst NAND Channel % of bad blocks  value of {worst_per} is invalid."
            )
        reserved = statistics[offset + 9]
        if reserved != 0:
            sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved byte 1 is not 0h.")
        worst_raw = int.from_bytes(statistics[offset + 10 : offset + 812], "little")
        reserved = int.from_bytes(statistics[offset + 12 : offset + 16], "little")
        if reserved != 0:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved bytes 7:4 are not 0h."
            )

        print(f"\t\t\t{pre_string}Worst NAND Channel % of Bad Black         : {worst_per}%")
        print(f"\t\t\t{pre_string}Worst NAND Channel Raw Number of Bad Black: {worst_raw}")
    elif identifier == 0x1D:
        best_per = statistics[offset + 8]
        if best_per > 100:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} worst NAND Channel % of bad blocks  value of {worst_per} is invalid."
            )
        reserved = statistics[offset + 9]
        if reserved != 0:
            sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved byte 1 is not 0h.")
        best_raw = int.from_bytes(statistics[offset + 10 : offset + 12], "little")
        reserved = int.from_bytes(statistics[offset + 12 : offset + 16], "little")
        if reserved != 0:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved bytes 7:4 are not 0h."
            )

        print(f"\t\t\t{pre_string}Best NAND Channel % of Bad Black         : {best_per}%")
        print(f"\t\t\t{pre_string}Best NAND Channel Raw Number of Bad Black: {best_raw}")
    else:
        value = int.from_bytes(statistics[offset + 8 : offset + 8 + (dw_len * 4)], "little")
        print(f"\t\t\t{pre_string}Value         : {value}")

    return 8 + (dw_len * 4)


# Parse the statistics for an area
#
# Input:
#      data area  : integer specify which data area the static was defined
#      statistics : bytearray of the statistics descriptors to parse
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_statistics(data_area, statistics, strings):
    offset = 0
    stat_len = len(statistics)

    print(f"\n\tData Area {data_area} Statistics:\n")
    while (offset + 8) < stat_len:  # The header for the Statistics Descriptor needs to exist
        offset += parse_a_statistic(data_area, statistics[offset:], strings, "")


# OCP defined class types
class_type_str = [
    "Reserved",
    "Timestamp",
    "PCIe Debug",
    "NVMe Debug",
    "Reset Debug",
    "Boot Sequence",
    "Firmware Assert",
    "Temperature",
    "Media",
    "Media Wear",
    "Static Snapshot",
]

# OCP defined Timestamp Event Identifiers
timestamp_ocp_id = [
    "Timestamp Host Command Issued",
    "Timestamp Snapshot",
    "Timestamp is Power on Hours",
]

# Parse and print a timestamp debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Timestamp event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_timestamp(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 3) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Timestamp event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size < 2:
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Timestamp event dword size value of {dw_size} is invalid.")

    if dw_size > 2:
        vu_id = int.from_bytes(event[12:14], "little")
        idx = hex(1) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(
                f"Data Area {data_area} FIFO {fifo_num} Timestamp event VU Identifier 0x{vu_id:x} does not exist in the string log file"
            )
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[14 : 14 + ((dw_size - 2) * 4)], "little")

    print("\t\t\tTimespamp Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} ({timestamp_ocp_id[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} (Vendor Unique)")

    parse_nvm_timestamp(event[4:12], "\t\t")

    if dw_size > 2:
        print(f"\t\t\t\tVU Identifier : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data       : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definition : 0x{vu_value:x}")


# OCP defined PCIe event identifiers
pcie_ocp_id = [
    "Link Up",
    "Link Down",
    "PCIe Error Detected",
    "PERST Asserted",
    "PERST De-asserted",
    "Refclk Stable",
    "Vmain Stable",
    "Link Speed and Width Negotiated",
]

# OCP defined PCIe event state changes
pcie_ocp_state = [
    "Unchanged",
    "Link Speed Changed",
    "Link Width Changed",
]

# OCP defined PCIe event link speeds
pci_ocp_link_speed = [
    "Reserved",
    "PCIe Gen1",
    "PCIe Gen2",
    "PCIe Gen3",
    "PCIe Gen4",
    "PCIe Gen5",
    "PCIe Gen6",
    "PCIe Gen7",
]


# OCP defined PCIe event link widths
pci_ocp_link_width = [
    "Reserved",
    "x1",
    "x2",
    "x4",
    "x8",
    "x16",
]

# Parse and print a PCIe debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a PCIe event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_pcie(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 7) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} PCIe event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size < 1:
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} PCIe event dword size value of {dw_size} is invalid.")

    if identifier == 7:
        state = event[4]
        if state > 2:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} PCIe event State Changed Flag value of {state} is invalid.")

        speed = event[5]
        if (speed == 0) or (speed > 7):
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} PCIe event Link Speed value of {speed} is invalid.")

        width = event[6]
        if (width == 0) or (width > 5):
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} PCIe event Link Width value of {width} is invalid.")

        reserved = event[7]
        if reserved != 0:
            sys.exit(f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved byte 7is not 0h.")
    else:
        reserved = int.from_bytes(event[4:8], "little")
        if reserved != 0:
            sys.exit(
                f"Data Area {data_area} statistic Identifier 0x{identifier:x} {stats_ocp_str[identifier]} reserved bytes 7:4 are not 0h."
            )

    if dw_size > 1:
        vu_id = int.from_bytes(event[8:10], "little")
        idx = hex(2) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} PCIe event VU Identifier 0x{vu_id:x} does not exist in the string log file")
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[10 : 10 + ((dw_size - 1) * 4)], "little")

    print("\t\t\tPCIe Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier        : 0x{identifier:x} ({pcie_ocp_id[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier        : 0x{identifier:x} (Vendor Unique)")

    if identifier == 7:
        print(f"\t\t\t\tState Change Flags: {state}({pcie_ocp_state[state]})")
        print(f"\t\t\t\tLink Speed        : {speed}({pci_ocp_link_speed[speed]})")
        print(f"\t\t\t\tLink Width        : {width}({pci_ocp_link_width[width]})")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier     : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data           : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definition     : {description}")


# OCP defined NVMe event identifiers
nvme_ocp = [
    "CC.EN transitions from 0b to 1b",
    "CC.EN transitions from 1b to 0b",
    "CSTS.RDY transitions from 0b to 1b",
    "CSTS.RDY transitions from 1b to 0b",
    "Reserved",
    "Create I/O Submission Queue Command or Create I/O Completion Queue Command Processed",
    "Other Admin Queue Command Processed",
    "An Admin Command Returned a Non-zero Status Code",
    "An I/O Command Returned a Non-zero Status Code",
    "CSTS.CFS Set to 1b",
    "Admin Submission Queue Base Address Written (AQA) or Admi Completion Queue Based Address (ACQ) written",
    "Controller Configuration Register (CC) Changed except for the cases that are covered in 0000h and 0001h.",
    "Controller Status Register (CSTS) Changed except for the cases that are covered in 0002h and 0003h",
]

# Parse and print an NVMe debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a NVMe event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_nvme(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 12) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size < 2:
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event dword size value of {dw_size} is invalid.")

    if (identifier == 7) or (identifier == 8):
        opcode = event[4]
        status = int.from_bytes(event[5:7], "little")
        if (status & 0x8000) != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event status value of 0x{status:x} is invalid.")
        reserved = int.from_bytes(event[7:12], "little")
        if reserved != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event reserved value in bytes 11:7 are not 0h.")
    elif identifier == 0xB:
        cc = int.from_bytes(event[4:8], "little")
        reserved = int.from_bytes(event[8:12], "little")
        if reserved != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event reserved value in bytes 11:8 are not 0h.")
    elif identifier == 0xC:
        csr = int.from_bytes(event[4:8], "little")
        reserved = int.from_bytes(event[8:12], "little")
        if reserved != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event reserved value in bytes 11:8 are not 0h.")
    else:
        reserved = int.from_bytes(event[4:12], "little")
        if reserved != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event reserved value in bytes 11:4 are not 0h.")

    if dw_size > 2:
        vu_id = int.from_bytes(event[12:14], "little")
        idx = hex(3) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} NVMe event VU Identifier 0x{vu_id:x} does not exist in the string log file")
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[14 : 14 + ((dw_size - 2) * 4)], "little")

    print("\t\t\tNVMe Event:")

    # Calculate the spacing
    if identifier == 0xB:
        spacing = "                 "
    elif identifier == 0xC:
        spacing = "           "
    else:
        spacing = ""

    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier     {spacing}: 0x{identifier:x} ({nvme_ocp[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier     {spacing}: 0x{identifier:x} (Vendor Unique)")
    if (identifier == 7) or (identifier == 8):
        print(f"\t\t\t\tCommand Opcode {spacing}: 0x{opcode:x}")
        print(f"\t\t\t\tStatus Code    {spacing}: 0x{status:x}")
    elif identifier == 0xB:
        print(f"\t\t\t\tController Configuration Register: 0x{cc:x}")
    elif identifier == 0xC:
        print(f"\t\t\t\tController Status Register : 0x{csr:x}")

    if dw_size > 2:
        print(f"\t\t\t\tVU Identifier  {spacing}: 0x{vu_id:x}")
        print(f"\t\t\t\tVU data        {spacing}: 0x{vu_value:x}")
        print(f"\t\t\t\tVU definition  {spacing}: {description}")


# OCP defined reset event identifiers
reset_ocp = ["PCIe Conventional Hot Reset", "Main Power Cycle", "PERST#", "PCIe Function Level Reset", "NVM Subsystem Reset"]

# Parse and print a Reset debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Reset event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_reset(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 4) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Reset event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size > 0:
        vu_id = int.from_bytes(event[4:6], "little")
        idx = hex(4) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} Reset event VU Identifier 0x{vu_id:x} does not exist in the string log file")
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[6 : 6 + ((dw_size - 1) * 4)], "little")

    print("\t\t\tReset Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier   : 0x{identifier:x} ({reset_ocp[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier   : 0x{identifier:x} (Vendor Unique)")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier: 0x{vu_id:x}")
        print(f"\t\t\t\tVU data      : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definion  : {description}")


# OCP defined Boot Sequence event identifier
boot_ocp = [
    "Main Firmware Boot Complete",
    "FTL Load from NVM Complete",
    "FTL Rebuild Started",
    "FTL Rebuild Complete",
]

# Parse and print a Boot Sequence debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Boot Sequence event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_boot(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 3) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Boot Sequence event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size > 0:
        vu_id = int.from_bytes(event[4:6], "little")
        idx = hex(5) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(
                f"Data Area {data_area} FIFO {fifo_num} Boot Sequence event VU Identifier 0x{vu_id:x} does not exist in the string log file"
            )
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[6 : 6 + ((dw_size - 1) * 4)], "little")

    print("\t\tBoot Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} ({boot_ocp[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} (Vendor Unique)")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data       : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definion   : {description}")


# OCP defined Firmware Assert event identifiers
fa_assert_ocp = [
    "Assert in NVMe Processing Code",
    "Assert in Media Code",
    "Assert in Security Code",
    "Assert in Background Services Code",
    "FTL Rebuild Failed",
    "FTL Data Mismatch",
    "Assert in Other Code",
]

# Parse and print a Firmware Assert debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Firmware Assert event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_fw_assert(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 6) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Firmware Assert event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size > 0:
        vu_id = int.from_bytes(event[4:6], "little")
        idx = hex(6) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(
                f"Data Area {data_area} FIFO {fifo_num} Firmware Assert event VU Identifier 0x{vu_id:x} does not exist in the string log file"
            )
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[6 : 6 + ((dw_size - 1) * 4)], "little")

    print("\t\t\tFirmware Assert Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x}({fa_assert_ocp[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} (Vendor Unique)")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data       : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definion   : {description}")


# OCP defined Temperature event identifiers
temp_ocp = [
    "Composite Temperature decreases to (WCTEMP - 2)",
    "Composite Temperature increases to WCTEMP",
    "Composite Temperature increases to reach CCTEMP",
]

# Parse and print a Temperature debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Temperature event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_temp(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 2) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Temperature event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size > 0:
        vu_id = int.from_bytes(event[4:6], "little")
        idx = hex(7) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(
                f"Data Area {data_area} FIFO {fifo_num} Temperature event VU Identifier 0x{vu_id:x} does not exist in the string log file"
            )
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[6 : 6 + ((dw_size - 1) * 4)], "little")

    print("\t\t\tTemperature Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier : 0x{identifier:x} ({temp_ocp[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier : 0x{identifier:x} (Vendor Unique)")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data       : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definion   : {description}")


# OCP defined Media event identifiers
media_ocp = [
    "XOR (or equivalent) Recovery Invoked",
    "Uncorrectable Media Error",
    "Block Marked Bad Due to Program Error",
    "Block Marked Bad Due to Erase Error",
    "Block Marked Bad Due to Read Error",
    "Plane Failure Event",
]

# Parse and print a Media debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Media event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_media(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 5) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Media event Identifier value of 0x{identifier:x} is invalid.")

    if dw_size > 0:
        vu_id = int.from_bytes(event[4:6], "little")
        idx = hex(8) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} Media event VU Identifier 0x{vu_id:x} does not exist in the string log file")
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[6 : 6 + ((dw_size - 1) * 4)], "little")

    print("\t\t\tMedia Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} ({media_ocp[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier    : 0x{identifier:x} (Vendor Unique)")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data       : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definion   : {description}")


# Parse and print a Media Wear debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      identifier : integer of event identifier
#      dw_size    : integer containing the event Dword size
#      event      : bytearray of the remaining events to parse where the first event is a Media Wear event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_media_wear(data_area, fifo_num, identifier, dw_size, event, strings):
    if (identifier > 0) and (identifier < 0x8000):
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Media Wear Identifier value of 0x{identifier:x} is invalid.")

    if dw_size < 3:
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Media Wear dword size value of {dw_size} is invalid.")

    if identifier == 0:
        host_tr_w = int.from_bytes(event[4:8], "little")
        media_tr_w = int.from_bytes(event[8:12], "little")
        media_tr_e = int.from_bytes(event[12:16], "little")
    else:
        reserved = int.from_bytes(event[4:16], "little")
        if reserved != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} Media Wear Identifier 0x{identifier:x} bytes 15:4 are not 0h.")

    if dw_size > 3:
        vu_id = int.from_bytes(event[16:18], "little")
        idx = hex(9) + hex(vu_id)
        if (idx in strings["vu_events"]) == False:
            sys.exit(
                f"Data Area {data_area} FIFO {fifo_num} Media Wear event VU Identifier 0x{vu_id:x} does not exist in the string log file"
            )
        else:
            description = strings["vu_events"][idx]["string"]
        vu_value = int.from_bytes(event[18 : 18 + ((dw_size - 1) * 4)], "little")

    print("\t\t\tMedia Wear Event:")
    if identifier < 0x8000:
        print(f"\t\t\t\tIdentifier             : 0x{identifier:x} ({pcie_ocp_id[identifier]})")
    else:
        print(f"\t\t\t\tIdentifier             : 0x{identifier:x} (Vendor Unique)")

    if identifier == 0:
        print(f"\t\t\t\tHost Terabytes Written : {host_tr_w}")
        print(f"\t\t\t\tMedia Terabytes Written: {media_tr_w}")
        print(f"\t\t\t\tMedia Terabytes Erased : {media_tr_e}")

    if dw_size > 1:
        print(f"\t\t\t\tVU Identifier          : 0x{vu_id:x}")
        print(f"\t\t\t\tVU data                : 0x{vu_value:x}")
        print(f"\t\t\t\tVU definion            : {description}")


# Parse and print Snapshot debug event
#
# Input:
#      data area  : integer specify which data area the static was defined
#      fifo_num:  : integer of the FIFO containing the event
#      event      : bytearray of the remaining events to parse where the first event is a Snapshot event
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_snapshot(data_area, fifo_num, event, strings):
    reserved = int.from_bytes(event[1:4], "little")
    if reserved != 0:
        sys.exit(f"Data Area {data_area} FIFO {fifo_num} Snapshot event bytes 3:1 are not 0h.")

    print("\t\t\tSnapshot Event:")

    # Ignore the offset
    offset = parse_a_statistic(data_area, event[4:], strings, "\t")


# Array of parsing functions for OCP defined Events except the Snapshot event
parse_ocp_event = [
    parse_timestamp,
    parse_pcie,
    parse_nvme,
    parse_reset,
    parse_boot,
    parse_fw_assert,
    parse_temp,
    parse_media_wear,
]

# Parse and print a FIFO
#
# Input:
#      data area  : integer specify which data area the static was defined
#      dw_size    : integer containing the event Dword size
#      data       : bytearray of the FIFO area
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_a_fifo(data_area, fifo_num, data, strings):
    offset = 0
    data_len = len(data)
    event_num = 1

    print(f"\n\tFIFO {fifo_num} data:\n")
    while (offset + 4) < data_len:  # The header for the Event Descriptor needs to exist
        class_type = data[offset]

        if class_type == 0:
            break

        print(f"\t\tEvent Entry {event_num}")
        if (class_type > 10) and (class_type < 0x80):
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} class type value of {class_type} is invalid.")

        if class_type != 0x10:
            identifier = int.from_bytes(data[offset + 1 : offset + 3], "little")
            dw_size = data[offset + 3]
            static_size = 4

        # Parse the event type
        if class_type < 0x9:
            parse_ocp_event[class_type - 1](data_area, fifo_num, identifier, dw_size, data[offset : offset + 4 + (dw_size * 4)], strings)
        elif class_type == 0x0A:
            # Need the size to extract the bytearray
            dw_size = int.from_bytes(data[offset + 8 : offset + 9])
            static_size = 12
            parse_snapshot(data_area, fifo_num, data[offset : offset + 12 + (dw_size * 4)], strings)
        else:
            # Parse Vendor unique
            identifier = int.from_bytes(data[offset + 1 : offset + 3], "little")
            dw_size = data[offset + 3]

            # make sure the VU string exists
            idx = hex(class_type) + hex(identifier)

            if (idx in strings["events"]) == False:
                sys.exit(f"Data Area {data_area} FIFO {fifo_num} class type value of {class_type} has no String log page definition.")

            description = strings["events"][idx]["string"]
            value = int.from_bytes(data[offset + 4 : offset + 4 + (dw_size * 4)], "little")

            print("\t\t\tVendor Unique Event:")
            print(f"\t\t\t\tVendor Class: 0x{class_type:x}")
            print(f"\t\t\t\tIdentifier  : 0x{identifier:x}")
            print(f"\t\t\t\tDescription : {description}")
            print(f"\t\t\t\tValue       : {value}")

        offset += static_size + (dw_size * 4)
        event_num += 1

    # Validate the remaining area of the fifo is zero filled
    if offset < data_len:
        reserved = int.from_bytes(data[offset:data_len], "little")
        if reserved != 0:
            sys.exit(f"Data Area {data_area} FIFO {fifo_num} unused locations are not 0h.")


# Parse and print all the FIFOs in a data area
#
# Input:
#      data area  : integer specify which data area the static was defined
#      data       : bytearray of the the data area
#      fifo:      : disctionary of parsed FIFO information from Data Area 1
#      strings    : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
#
#    (<fifo information from data area 1>, stats_da_2_start_dw, stats_da_2_size_dw)
def parse_fifos(data_area, data, fifo, strings):
    # Loop through the FIFOs
    for x in range(1, 17):
        # Only parse the fifo if the FIFO exist in the specified data area
        if fifo[str(x)]["data area"] == data_area:
            # Parse the FIFO
            fifo_offset = fifo[str(x)]["start dw"] * 4
            fifo_size = fifo[str(x)]["size dw"] * 4

            parse_a_fifo(data_area, x, data[fifo_offset : fifo_offset + fifo_size], strings)


# Parse and print Data Area 1
#
# Input:
#      data_area_1    : bytearray of the the data area
#      strings        : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: Information on data 2 containined in data area 1
#
#    (<fifo information from data area 1>, stats_da_2_start_dw, stats_da_2_size_dw)
def parse_data_area_1(data_area_1, strings):
    print("\n\tData Area 1:\n")
    maj_ver = int.from_bytes(data_area_1[0:2], "little")
    if maj_ver != 3:
        sys.exit(f"Major Version of {maj_ver} is not the correct value.")
    print(f"\t\tMajor Version: {maj_ver}")

    min_ver = int.from_bytes(data_area_1[2:4], "little")
    if min_ver != 1:
        sys.exit(f"Minor Version of {min_ver} is not the correct value.")
    print(f"\t\tMinor Version: {min_ver}")

    reserved = int.from_bytes(data_area_1[4:8], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 7:4 are not cleared to 0h.")

    parse_nvm_timestamp(data_area_1[8:16], "")

    guid = int.from_bytes(data_area_1[16:32], "little")
    if guid != 0xBA560A9C3043424CBC73719D87E64EFA:
        sys.exit(f"Guid 0x{guid:x} is not the correct value.")
    print(f"\t\tGuid: 0x{guid:x}")

    profiles = data_area_1[32] + 1  # 0's based number
    print(f"\t\tNumber of profiles: {profiles}")

    selected_profiles = data_area_1[33] + 1  # 0's based number
    if selected_profiles > profiles:
        sys.exit(f"Selected Profile value of {selected_profiles} is not in the range of supported profiles: {profiles}")
    print(f"\t\tSelected Profile: {profiles}")

    reserved = int.from_bytes(data_area_1[34:40], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 39:34 are not cleared to 0h.")

    str_len = int.from_bytes(data_area_1[40:48], "little")
    if str_len != strings["length"] // 4:
        sys.exit(f"String Log Length of {str_len} does not match the length of the string log of {strings['length']}")
    print(f"\t\tString Log Size Dwords: {str_len}")

    reserved = int.from_bytes(data_area_1[48:56], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 55:48 are not cleared to 0h.")

    fw_ver = data_area_1[56:64].decode()
    print(f"\t\tFirmware Verison: {fw_ver}")

    reserved = int.from_bytes(data_area_1[64:96], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 95:64 are not cleared to 0h.")

    stats_da_1_start_dw = int.from_bytes(data_area_1[96:104], "little")
    stats_da_1_size_dw = int.from_bytes(data_area_1[104:111], "little")
    if ((stats_da_1_start_dw * 4) < 1536) or ((stats_da_1_start_dw * 4) > len(data_area_1)):
        sys.exit(f"Data Area 1 Statistics Start value of {stats_da_1_start_dw} is invalid.")
    if ((stats_da_1_start_dw + stats_da_1_size_dw) * 4) > len(data_area_1):
        sys.exit(f"Data Area 1 Statistics Size value of {stats_da_1_start_dw} is invalid.")

    print(
        f"\t\tData Area 1 Statistic Start (in Dwords): 0x{stats_da_1_start_dw:x} relative to the start of the Telemetry Host-Initiated log page"
    )
    print(f"\t\tData Area 1 Statistic Size (in Dwords): 0x{stats_da_1_size_dw:x}")

    # These are checked as part of data area 2 checking
    stats_da_2_start_dw = int.from_bytes(data_area_1[112:120], "little")
    stats_da_2_size_dw = int.from_bytes(data_area_1[120:128], "little")

    print(
        f"\t\tData Area 2 Statistic Start (in Dwords): 0x{stats_da_2_start_dw:x} relative to the start of the Telemetry Host-Initiated log page"
    )
    print(f"\t\tData Area 2 Statistic Size (in Dwords): 0x{stats_da_2_size_dw:x}")

    reserved = int.from_bytes(data_area_1[128:160], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 159:128 are not cleared to 0h.")

    fifo = get_fifo_data(data_area_1[160:432])

    # Validate the fifo data for data area 1
    for x in range(1, 17):
        idx = str(x)
        if fifo[idx]["data area"] == 1:
            offset_in_da_1 = (fifo[idx]["start dw"] * 4) - 512
            size_in_da_1 = fifo[idx]["size dw"] * 4
            if offset_in_da_1 > len(data_area_1):
                sys.exit(f"Event FIFO {idx}start is outside of data area 1.")
            if (offset_in_da_1 + size_in_da_1 - 1) > len(data_area_1):
                sys.exit(f"Event FIFO {idx}size is outside of data area 1.")

    reserved = int.from_bytes(data_area_1[432:512], "little")
    if reserved != 0:
        sys.exit("Reserved bytes 432:511 are not cleared to 0h.")

    parse_smart_health_info(data_area_1[512:1024])
    parse_smart_health_info_extension(data_area_1[1024:1536])

    # Parse the statistics
    parse_statistics(1, data_area_1[(stats_da_1_start_dw * 4) - 512 : ((stats_da_1_start_dw + stats_da_1_size_dw) * 4) - 512], strings)

    # Parse the FIFOs
    parse_fifos(1, data_area_1, fifo, strings)

    return (fifo, stats_da_2_start_dw, stats_da_2_size_dw)


# Parse and print Data Area 2
#
# Input:
#
#      stat_offset_dw : Dword offset to the Statistics Identifier Table in Data Area 2
#      stat_size_dw   : Dword size to the Statistics Identifier Table in Data Area 2
#      data_area_2    : bytearray of the the data area
#      fifo           : dictionsary to the FIFO information contained in data area 1
#      strings        : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_data_area_2(stat_offset_dw, stat_size_dw, data_area_2, fifo, strings):
    da2_len = len(data_area_2)

    # Validate the fifo data for data area 2
    for x in range(1, 17):
        idx = str(x)
        if fifo[idx]["data area"] == 2:
            offset_in_da_2 = fifo[idx]["start dw"] * 4
            size_in_da_2 = fifo[idx]["size dw"] * 4
            if offset_in_da_2 > da2_len:
                sys.exit(f"Event FIFO {idx}start is outside of data area 2.")
            if (offset_in_da_2 + size_in_da_2 - 1) > da2_len:
                sys.exit(f"Event FIFO {idx}size is outside of data area 2.")

    # Parse the statistics
    if (stat_offset_dw * 4) >= da2_len:
        sys.exit("Statistics start is outside of data area 2.")
    if ((stat_offset_dw + stat_size_dw) * 4) > da2_len:
        sys.exit("Statistics size is outside of data area 2.")

    parse_statistics(2, data_area_2[(stat_offset_dw * 4) : ((stat_offset_dw + stat_size_dw) * 4)], strings)

    # Parse the FIFOs
    parse_fifos(2, data_area_2, fifo, strings)


# Parse and print the Host-Initiated Telemetry log page
#
# Input:
#
#      telemetry      : bytearray of the telemetry data
#      strings        : dictionary of the parsed string log page contining the VU ASCII strings
#
# Output: None
def parse_telemetry(telemetry, strings):
    tel_len = len(telemetry)

    # Validate the header exists
    if len(telemetry) < 512:
        sys.exit(f"Telemetry log does is smaller than the defined NVMe header of 512 byte: {tel_len}")

    # Parse the header
    (data_area_1_last_block, data_area_2_last_block, data_area_3_last_block, data_area_4_last_block) = parse_telemetry_header(
        telemetry[0:512], tel_len
    )

    # Parse and print Data Area 1
    da1_offset = 512
    da1_size = data_area_1_last_block * 512

    (fifo, data_area_2_stat_start_dw, data_area_2_stat_size_dw) = parse_data_area_1(telemetry[da1_offset : da1_offset + da1_size], strings)
    # Parse and print Data Area 2
    da2_offset = da1_offset + da1_size
    da2_size = (data_area_2_last_block - data_area_1_last_block) * 512

    parse_data_area_2(data_area_2_stat_start_dw, data_area_2_stat_size_dw, telemetry[da2_offset : da2_offset + da2_size], fifo, strings)

    # Ignoring data area 3 and data area 4
    print("\n\tData Area 3: Ignored\n")
    print("\n\tData Area 4: Ignored\n")


# Parse the input parameters
#
# Input: None
#
# Output: Input parameters
#
def parse_inputs():
    telemetry_default = "telemetry.bin"
    string_default = "string.bin"

    # Add the agruments
    parser = argparse.ArgumentParser(
        prog="ocp_dump_nvme_telemtry.py",
        description="This script parses the inputed NVMe(TM) Telemetry  log page using the inputted OCP Strings log page "
        "to print vendor unique information. This script is based on the OCP Datacenter NVMe SSD specification " + ocp_ver + ".",
        epilog="The Telemetry Host-Initiated log page is based off of NVM Express Base SPecification 2.0c.",
    )

    parser.add_argument(
        "-t",
        "--telemetry",
        type=str,
        dest="telemetry",
        required=False,
        metavar="<filename>",
        default="telemetry.bin",
        help="Telemetry Host-Initiated log page filename. "
        + "Defines the input filename containing the Telemetry Host-Initiated log page. If not specified then the filename '"
        + telemetry_default
        + "' is used.",
    )
    parser.add_argument(
        "-s",
        "--string",
        type=str,
        dest="string",
        required=False,
        metavar="<filename>",
        default="string.bin",
        help="OCP Strings log page (C9h) filename. "
        + "Defines the input filename containing the OCP Strings log page. If not specified then the filename '"
        + string_default
        + "' is used.",
    )
    parser.add_argument(
        "-v", "--version", action="store_true", dest="list_ver", required=False, help="Specify the version of this script and exit."
    )

    # Parse the argument
    return parser.parse_args()


# Main part of the script
args = parse_inputs()
if args.list_ver:
    print(f"{os.path.basename(__file__)} version: {version}")
else:
    with open(args.string, mode="rb") as f:
        string_log = f.read()

    with open(args.telemetry, mode="rb") as f:
        telemetry_log = f.read()

    strings = parse_strings(string_log)
    parse_telemetry(telemetry_log, strings)
