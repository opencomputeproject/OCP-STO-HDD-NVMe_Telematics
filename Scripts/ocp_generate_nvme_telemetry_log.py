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
# 1/6/2023 - Put <spaces> in the ASCI table for unused locations
#          - Sorted the tables in the Strings table to meet requirements
# 4/9/2023 - Conversion to f-strings
#          - Remove superfluous syntax
#          - Reduce dictionary lookups
#          - Deduplicate code
#          - Reformat code with Black

import json
import sys
import random
from random import choice
from random import randbytes
import argparse
import os

# global variables

version = 2.2

time = random.randint(0, (2 ** 48) - 1)

ocp_ver = "2.5r24"

sample_json = (
    "{\n"
    '"Timestamp" : {\n'
    '    "_comment" : "Defines a time that is incremented every time a timestamp is generated.",\n'
    '    "start time" : 10203040506\n'
    "},\n"
    '"Profiles"  : {\n'
    '    "_comment" : "Defines the number of OCP Profile to report being supported.",\n'
    '    "Number of Profiles" : 10,\n'
    '    "_comment" : "Defines the reported current profile within the Nnumber of Profiles supported.",\n'
    '    "Profile Selected" : 2\n'
    "},\n"
    '"Data Area 1": {\n'
    '    "_comment" : "Define the size of Data Area 1 in bytes (while changeable, thisis a fixed value.",\n'
    '     "size" : 16384\n'
    "},\n"
    '"Data Area 2": {\n'
    '    "_comment" : "Define the size of Data Area 2 in bytes.",\n'
    '     "size" : 16384\n'
    "},\n"
    '"Data Area 3": {\n'
    '    "_comment" : "Define the size of Data Area 3 in bytes. The value of zero is valid",\n'
    '     "size" : 0\n'
    "},\n"
    '"Data Area 4": {\n'
    '    "_comment" : "Define the size of Data Area 4 in bytes. The value of zero is valid.",\n'
    '     "size" : 0\n'
    "},\n"
    '"Namespaces": {\n'
    '    "_comment" : "Define the number of namespaces.",\n'
    '     "number" : 2\n'
    "},\n"
    '"Statistics" : {\n'
    '    "_comment"  : "Define the set of OCP defined Statistics to be reported. A random value is selected between the minimum and maximum values.",\n'
    '    "_comment1" : "The script will randomly select if vendor specific data is added and will define an VU identifier.",\n'
    '    "_comment2" : "The set below is the statistic identifiers defined by OCP Specification ' + ocp_ver + '.",\n'
    '    "OCP Defined" : {\n'
    '     "Outstanding Admin Commands" : {\n'
    '         "Identifier" : 1,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-2",\n'
    '         "Definition" : "Number of outstanding Admin commands submitted by the host which have not been processed by the controller. Pulled from Submission Queue but not yet pushed to the Completion Queue. This count shall not include Asynchronous Event Request (AER) commands.",\n'
    '         "Data Area" : 1},\n'
    '     "Host Write Bandwidth" : {\n'
    '         "Identifier" : 2,\n'
    '         "Value Max" : 100,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-3",\n'
    '         "Definition" : "The percentage of the current write bandwidth allowed to the NAND backend due to host writes.",\n'
    '         "Data Area" : 1},\n'
    '     "GC Write Bandwidth" : {\n'
    '         "Identifier" : 3,\n'
    '         "Value Max" : 100,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-4",\n'
    '         "Definition" : "The percentage of the current write bandwidth allowed to the NAND backend due to internal writes. STATI-2 and STATI-3 shall add to 100%.",\n'
    '         "Data Area" : 1},\n'
    '     "Active Namespaces" : {\n'
    '         "Identifier" : 4,\n'
    '         "Value Max" : 128,\n'
    '         "Value Min" : 1,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-5",\n'
    '         "Definition" : "Shall be the number of Active Namespaces attached to the NVM subsystem.",\n'
    '         "Data Area" : 1},\n'
    '     "Internal Write Workload" : {\n'
    '         "Identifier" : 5,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 5,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-6",\n'
    '         "Definition" : "Number of outstanding LBAs corresponding to the Internal Write Queue Depth (STATI-7).",\n'
    '         "Data Area" : 1},\n'
    '     "Internal Read Workload" : {\n'
    '         "Identifier" : 6,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 5,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-7",\n'
    '         "Definition" : "Number of outstanding LBAs corresponding to the Internal Read Queue Depth (STATI-8).",\n'
    '         "Data Area" : 1},\n'
    '     "Internal Write Queue Depth" : {\n'
    '         "Identifier" : 7,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 5,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-8",\n'
    '         "Definition" : "Number of outstanding Write commands submitted by the host which have not been processed by the controller. Pulled from Submission Queue but not yet pushed to the Completion Queue.",\n'
    '         "Data Area" : 1},\n'
    '     "Internal Read Queue Depth" : {\n'
    '         "Identifier" : 8,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 5,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-9",\n'
    '         "Definition" : "Number of outstanding Read commands submitted by the host which have not been processed by the controller. Pulled from Submission Queue but not yet pushed to the Completion Queue.",\n'
    '         "Data Area" : 1},\n'
    '     "Pending Trim LBA Count" : {\n'
    '         "Identifier" : 9,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 5,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-10",\n'
    '         "Definition" : "From a device perspective this is the current number of LBAs pending completion of the background trim process due to host Dataset Management commands.",\n'
    '         "Data Area" : 1},\n'
    '     "Host Trim LBA Request Count" : {\n'
    '         "Identifier" : 10,\n'
    '         "Value Max" : 32000,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-11",\n'
    '         "Definition" : "Number of LBAs that have been requested by Dataset Management commands since last Telemetry Log collection.",\n'
    '         "Data Area" : 1},\n'
    '     "Current NVMe Power State" : {\n'
    '         "Identifier" : 11,\n'
    '         "Value Max" : 31,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-12",\n'
    '         "Definition" : "Currently set NVMe Power State Descriptor at the time of this Telemetry Log collection.",\n'
    '         "Data Area" : 1},\n'
    '     "Current DSSD Power State" : {\n'
    '         "Identifier" : 12,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-13",\n'
    '         "Definition" : "Currently set DSSD Power State Descriptor at the time of this Telemetry Log collection.",\n'
    '         "Data Area" : 1},\n'
    '     "Program Fail Count" : {\n'
    '         "Identifier" : 13,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-14",\n'
    '         "Definition" : "The number of program operation failure events for the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "Erase Fail Count" : {\n'
    '         "Identifier" : 14,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-15",\n'
    '         "Definition" : "The number of erase operation failure events for the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "Read Disturb Writes" : {\n'
    '         "Identifier" : 15,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 4,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-16",\n'
    '         "Definition" : "Number of bytes written due to read disturb relocations for the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "Retention Writes" : {\n'
    '         "Identifier" : 16,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 4,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-17",\n'
    '         "Definition" : "Number of bytes written due to retention relocation for the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "Wear Leveling Writes" : {\n'
    '         "Identifier" : 17,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 4,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-18",\n'
    '         "Definition" : "Number of bytes written due to wear leveling for the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "Read Recovery Writes" : {\n'
    '         "Identifier" : 18,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-19",\n'
    '         "Definition" : "Number of bytes written due to read recovery for the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "GC Writes" : {\n'
    '         "Identifier" : 19,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 1,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-20",\n'
    '         "Definition" : "Number of bytes written due to garbage collection since last Telemetry Log collection using by reading either host-initiated or controller-initiated log.",\n'
    '         "Data Area" : 1},\n'
    '     "SRAM Correctable Count" : {\n'
    '         "Identifier" : 20,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-21",\n'
    '         "Definition" : "Total number of correctable errors due to device SRAM single error correction over the device lifetime.",\n'
    '         "Data Area" : 1},\n'
    '     "DRAM Correctable Count" : {\n'
    '         "Identifier" : 21,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-22",\n'
    '         "Definition" : "Total number of correctable errors due to device DRAM single error correction over the life of the device.",\n'
    '         "Data Area" : 1},\n'
    '     "SRAM Uncorrectable Count" : {\n'
    '         "Identifier" : 22,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-23",\n'
    '         "Definition" : "Total number of uncorrectable errors due to device SRAM double error detection.",\n'
    '         "Data Area" : 1},\n'
    '     "DRAM Uncorrectable Count" : {\n'
    '         "Identifier" : 23,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-24",\n'
    '         "Definition" : "Total number of uncorrectable errors due to device DRAM double error detection.",\n'
    '         "Data Area" : 1},\n'
    '     "Data Integrity Error Count" : {\n'
    '         "Identifier" : 24,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-25",\n'
    '         "Definition" : "Total number of data integrity errors due to FTL metadata integrity checks.",\n'
    '         "Data Area" : 1},\n'
    '     "Read Retry Error Count" : {\n'
    '         "Identifier" : 25,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-26",\n'
    '         "Definition" : "The number of reads for the device lifetime performed on the flash because of error correction (e.g., Read retries, LDPC iterations, etc.).",\n'
    '         "Data Area" : 1},\n'
    '     "PERST Events Count" : {\n'
    '         "Identifier" : 26,\n'
    '         "Value Max" : 16384,\n'
    '         "Value Min" : 0,\n'
    '         "Dword Size" : 1,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-27",\n'
    '         "Definition" : "Number of PERST events processed by the NVM Subsystem for the lifetime of the device. This count shall only increment if the CC.EN bit is set to 1b.",\n'
    '         "Data Area" : 1},\n'
    '     "Max Die Bad Block" : {\n'
    '         "Identifier" : 27,\n'
    '         "Value Max" : 655370,\n'
    '         "Value Min" : 655370,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-28",\n'
    '         "Definition" : "This information is based on a single die which has the largest number of bad blocks.",\n'
    '         "Data Area" : 1},\n'
    '     "Max NAND Channel Bad Block" : {\n'
    '         "Identifier" : 28,\n'
    '         "Value Max" : 720907,\n'
    '         "Value Min" : 720907,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-29",\n'
    '         "Definition" : "This information is based on the dies in a single NAND channel which has the largest number of bad blocks.",\n'
    '         "Data Area" : 1},\n'
    '     "Minimum NAND Channel Bad Block" : {\n'
    '         "Identifier" : 29,\n'
    '         "Value Max" : 786444,\n'
    '         "Value Min" : 786444,\n'
    '         "Dword Size" : 2,\n'
    '         "Behavior Type" : 4,\n'
    '         "Namespace" : 0,\n'
    '         "Requirement" : "STATI-30",\n'
    '         "Definition" : "This information is based on the dies in a single NAND channel which has the smallest number of bad blocks.",\n'
    '         "Data Area" : 1}\n'
    "     },\n"
    '     "Vendor Defined" : {\n'
    '         "_comment"  : "Define the set of OCP Vendor Statistics to be reported. A random value is selected between the minimum and maximum values.",\n'
    '         "Specific Fields" : {\n'
    '             "Vendor ID 1" : {\n'
    '                 "Identifier" : 32768,\n'
    '                 "Value Max" : 16384,\n'
    '                 "Value Min" : 0,\n'
    '                 "Dword Size" : 2,\n'
    '                 "Behavior Type" : 4,\n'
    '                 "Namespace" : 0,\n'
    '                 "Requirement" : "STATI-31",\n'
    '                 "Definition" : "Vendor defined 1",\n'
    '                 "Data Area" : 1},\n'
    '             "Vendor ID 2" : {\n'
    '                 "Identifier" : 45056,\n'
    '                 "Value Max" : 16384,\n'
    '                 "Value Min" : 0,\n'
    '                 "Dword Size" : 2,\n'
    '                 "Behavior Type" : 4,\n'
    '                 "Namespace" : 1,\n'
    '                 "Requirement" : "STATI-31",\n'
    '                 "Definition" : "Vendor defined 2",\n'
    '                 "Data Area" : 1},\n'
    '             "Vendor ID 3" : {\n'
    '                 "Identifier" : 65535,\n'
    '                 "Value Max" : 16384,\n'
    '                 "Value Min" : 0,\n'
    '                 "Dword Size" : 1,\n'
    '                 "Behavior Type" : 4,\n'
    '                 "Namespace" : 2,\n'
    '                 "Requirement" : "STATI-31",\n'
    '                 "Definition" : "Vendor defined 3",\n'
    '                 "Data Area" : 1}\n'
    "        },\n"
    '        "_comment"  : "Define the number of random vendor defined statistics to be generated. Everything is randon, incluing the Data Area location.",\n'
    '        "Random Fields" : 100\n'
    "        }\n"
    "},\n"
    '"Debug FIFOs" : {\n'
    '    "1" : {\n'
    '         "_comment"   : "Define each FIFO to be included in the Telemetry Host-Initiated log page. FIFO sizes can be zero or not included.",\n'
    '         "_comment1"  : "The name is limited to characters. Be careful to choose the size of the FIFOs as they must be able to fit within the Data Area.",\n'
    '         "_comment2"  : "The number of events included is up to the maximum defines. Any unused area of the FIFO is zero filled.",\n'
    '         "name" : "Name of FIFO 1",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "2" : {\n'
    '         "name" : "Name of FIFO 2",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 2},\n'
    '    "3" : {\n'
    '         "name" : "Name of FIFO 3",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "4" : {\n'
    '         "name" : "Name of FIFO 4",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 2},\n'
    '    "5" : {\n'
    '         "name" : "Name of FIFO 5",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 2},\n'
    '    "6" : {\n'
    '         "name" : "Name of FIFO 6",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 2},\n'
    '    "7" : {\n'
    '         "name" : "Name of FIFO 7",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "8" : {\n'
    '         "name" : "Name of FIFO 8",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 2},\n'
    '    "9" : {\n'
    '         "name" : "Name of FIFO 9",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 2},\n'
    '    "10" : {\n'
    '         "name" : "Name of FIFO 10",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "11" : {\n'
    '         "name" : "Name of FIFO 11",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "12" : {\n'
    '         "name" : "Name of FIFO 12",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "13" : {\n'
    '         "name" : "Name of FIFO 13",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "14" : {\n'
    '         "name" : "Name of FIFO 14",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "15" : {\n'
    '         "name" : "Name of FIFO 15",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1},\n'
    '    "16" : {\n'
    '         "name" : "Name of FIFO 16",\n'
    '         "size" : 1024,\n'
    '         "Max Events" : 40,\n'
    '         "Data Area" : 1}\n'
    "}\n"
    "}\n"
)

# Get a time and make sure time is always incrementing
#
# Input: None
#
# Output: A integer time that is more than the time last time this function was invoked.
def get_time():
    global time

    time += 1
    if time > 2 ** 48:
        time = 0

    return time


# This function generates a NVMe Host- or Controller-Initiated Telemetry 512 byte header
#
# Input:
#         da1_size  : Size in bytes of Data Area 1
#         da2_size  : Size in bytes of Data Area 2
#         da3_size  : Size in bytes of Data Area 3
#         da4_size  : Size in bytes of Data Area 4
#         host      : Host-initiated if True else Controller-initiated
#
# Output: A bytearray of an NVMe Host- or Controller-Initiated log page header
def nvme_telemetry_host_controller_initiated_header(da1_size, da2_size, da3_size, da4_size, host):
    # Compute the data area last blocks
    if (da1_size % 512) != 0:
        sys.exit("Data Area 1 size not a multiple of 512")
    else:
        da1_last_block = da1_size // 512
        if da1_last_block >= 2 ** 16:
            sys.exit("Data Area 1 last block is to big")

    if (da2_size % 512) != 0:
        sys.exit("Data Area 2 size not a multiple of 512")
    else:
        da2_last_block = da1_last_block + da2_size // 512
        if da2_last_block >= 2 ** 16:
            sys.exit("Data Area 2 last block is to big")

    if (da3_size % 512) != 0:
        sys.exit("Data Area 3 size not a multiple of 512")
    else:
        da3_last_block = da2_last_block + da3_size // 512
        if da3_last_block >= 2 ** 16:
            sys.exit("Data Area 3 last block is to big")

    if (da4_size % 512) != 0:
        sys.exit("Data Area 4 size not a multiple of 512")
    else:
        da4_last_block = da3_last_block + da4_size // 512
        if da4_last_block >= 2 ** 32:
            sys.exit("Data Area 4 last block is to big")

    reserved = 0
    if host:
        reason_str = "This is the reason for the host initiated dump"
        header = (7).to_bytes(1, "little")                      #      00  Log Identifier
    else:
        reason_str = "This is the reason for the controller initiated dump"
        header = (8).to_bytes(1, "little")                      #      00  Log Identifier

    header += reserved.to_bytes(4, "little")                    #   04:01  Reserved
    header += bytearray([1, 2, 3])                              #   07:05  IEEE OUI Identifier
    header += da1_last_block.to_bytes(2, "little")              #   09:08  Data Area 1 Last Block
    header += da2_last_block.to_bytes(2, "little")              #   11:10  Data Area 2 Last Block
    header += da3_last_block.to_bytes(2, "little")              #   13:12  Data Area 3 Last Block
    header += reserved.to_bytes(2, "little")                    #   15:14  Reserved
    header += da4_last_block.to_bytes(4, "little")              #   19:16  Data Area 4 Last Block

    if host:
        header += reserved.to_bytes((379 - 20 + 1), "little")   #  379:20  Reserved
        header += random.randint(0, 2).to_bytes(1, "little")    #  380     Telemetry Host-Initiated Scope
        header += random.randint(0, 255).to_bytes(1, "little")  #  381     Telemetry Host Initiated Generation Number
        header += random.randint(0, 1).to_bytes(1, "little")    #  382     Telemetry Controller Initiated Data Available
    else:
        header += reserved.to_bytes((380 - 20 + 1), "little")   #  380:20  Reserved
        header += random.randint(0, 2).to_bytes(1, "little")    #  381     Telemetry Controller-Initiated Scope
        header += (1).to_bytes(1, "little")                     #  382     Telemetry Controller-Initiated Data Available

    header += random.randint(0, 255).to_bytes(1, "little")      #  383     Telemetry Controller Initiated Generation Number
    header += reason_str.encode()                               #  511:384 Reason string
    header += reserved.to_bytes((511 - 384 + 1) - len(reason_str), "little")
    return header


# Generate a NVMe Timestamp
#
# Input: bytearrary to add time to
#
# Output: NVMe Timestamp added to byte arrary
def nvme_timestamp(data_struct):
    local_time = get_time()
    data_struct += local_time.to_bytes(6, "little")  # 05:00 Timestamp
    data_struct += (2).to_bytes(1, "little")         # 06    Attributes
    data_struct += (0).to_bytes(1, "little")         # 07    Reserved


# Generate random data for data area
#
# Input:
#         data_area : Data Area being created
#         size      : Size, in bytes of the data area to be created
#
# Output: Bytearray contabing a random data for a Data Area
def generate_data_area(data_area, size):
    print(f"Generating Data Area {data_area}:")
    if size > 0:
        return randbytes(size)
    return bytearray()


# Generate a statistics descriptor
#
# Input:
#         statistic  : A dictiuonary for a specific statistic
#         name       : ASCII string name of the statistic
#         namespaces : Number of namespaces allowed
#
# Output: Bytearray contabing a statics descriptor with random data generated for the data
def generate_statistic(statistic, name, namespaces):

    # Validate the statistic identifier
    identifier = statistic["Identifier"]
    if (identifier < 0) or (identifier >= 2 ** 16):
        sys.exit(f"Statistic {name}has an invalid Identifier value{identifier}")

    # Validate the behavior type
    behavior_type = statistic["Behavior Type"]
    if (behavior_type < 1) or (behavior_type >= 7):
        sys.exit(f"Statistic {name}has an invalid Behavior Type value{behavior_type}")

    # Validate the namespace - a Namespace of 0h means no namespace is specified
    namespace = statistic["Namespace"]

    if namespace > namespaces:
        sys.exit(f"Statistic {name}has an invalid namespace value as {namespace}")
    if namespace > 127:
        sys.exit(f"Statistic {name}has namespace value that does not fit into 7 bits {namespace}")
    if namespace != 0:
        namespace |= 0x80

    # Validate the Dword Size type
    # Only supporting 32 byte sized statistics
    dw_size = statistic["Dword Size"]
    if (dw_size < 1) or (dw_size >= 9):
        sys.exit(f"Statistic {name}has an invalid Dword size value{dw_size}")

    # Validate the min/max values
    maximum = statistic["Value Max"]
    minimum = statistic["Value Min"]
    if maximum < minimum:
        sys.exit("Statistic " + name + "has an invalid Min/Max values Max: " + maximum + " Min : " + minimum)

    descriptor = bytearray()
    descriptor += identifier.to_bytes(2, "little")     # 1:0 Static Identifier
    descriptor += behavior_type.to_bytes(1, "little")  #   2 Statistic Info
    descriptor += namespace.to_bytes(1, "little")      #   3 NS Info
    descriptor += dw_size.to_bytes(2, "little")        # 5:4 Statistic Data Size
    descriptor += bytearray(2)                         # 7:6 Reserved

    # Generate the value  - special case a few OCP defined values
    if identifier in (0x1B, 0x1C, 0x1D):
        if dw_size != 2:
            sys.exit(f"Statistic {name} has an invalid dword size value: {dw_size}")

        descriptor += random.randint(0, 100).to_bytes(1, "little")
        descriptor += (0).to_bytes(1, "little")
        descriptor += random.randint(0, (2 ** 16) - 1).to_bytes(2, "little")
        descriptor += (0).to_bytes(4, "little")
    else:
        descriptor += random.randint(minimum, maximum).to_bytes((dw_size * 4), "little")

    # Validate the Dword Size type
    if (dw_size < 1) or (dw_size >= 9):
        sys.exit(f"Statistic {name} has an invalid Behavior Type value {dw_size}")

    return_data = {"Identifier": identifier, "Descriptor": descriptor, "String": statistic["Definition"]}

    return return_data


# Generate the statistics information
#
# Input:
#         ocp_data : A dictiuonary containing ther JSON input data and the set of statistics
#
# Output: A dictionary containing all of the statistics with the format:
#
#      statistics = {'Data Area 1'              : {'<hex(identifier)> : {'Identifier' : identifier,      # This is a list of identifiers
#                                                                        'Descriptor' : statistics descriptor,
#                                                                        'String'     : definition to go into Stings log page}
#                    'Data Area 2'              : {'<hex(identifier)> : {'Identifier' : identifier,      # This is a list of identifiers
#                                                                        'Descriptor' : statistics descriptor,
#                                                                        'String'     : definition to go into Stings log page}}
#                     'Data Area 1 Table'       : Data Area 1 Table
#                     'Data Area 2 Table'       : Data Area 2 Table
#                     'Data Area 1 Identifiers' : array of identifier for random snapshot selections
#                     'Data Area 2 Identifiers' : array of identifier for random snapshot selections
#
def get_statistics(ocp_data):

    statistics = {
        "Namespaces": (0),
        "Data Area 1": {},
        "Data Area 2": {},
        "Data Area 1 Table": bytearray(),
        "Data Area 2 Table": bytearray(),
        "Data Area 1 Identifiers": [],
        "Data Area 2 Identifiers": [],
    }

    # Keep track of the number of namespaces supported
    namespaces = ocp_data["Namespaces"]["number"]
    statistics["Namespaces"] = namespaces

    # Loop through the OCP Defined statistics
    for stat, stat_value in ocp_data["Statistics"]["OCP Defined"].items():
        if stat_value["Data Area"] == 1:
            _area = "Data Area 1"
        elif stat_value["Data Area"] == 2:
            _area = "Data Area 2"
        else:
            sys.exit(f"Statistics {stat} has an invalid Data Area value of {stat_value['Data Area']}")

        stat_data = generate_statistic(stat_value, stat, namespaces)

        # Validate the Identifier is not already used.
        identifier = stat_data["Identifier"]
        if hex(identifier) in statistics[_area]:
            sys.exit(f"Statistic '{stat}' and '{key}' have the same identifier value of {stat_data['Identifier']}")

        # Validate the Identifier value - Just checking range
        if (identifier < 1) or (identifier > 29):
            sys.exit(f"Statistic '{stat}' has an invalid identifier value of {stat_data['Identifier']}")

        statistics[_area][hex(identifier)] = stat_data
        statistics[f"{_area} Identifiers"].append(hex(identifier))

    # Generate the random statistics

    # Create the list of already used values
    used_values = []
    for stat, stat_value in ocp_data["Statistics"]["Vendor Defined"]["Specific Fields"].items():
        used_values.append(stat_value["Identifier"])

    # Loop through the number of random statistics
    for x in range(ocp_data["Statistics"]["Vendor Defined"]["Random Fields"]):

        # Pick the fields for the random statistic
        identifier = choice(list(set(range(0x8000, 0xFFFF)) - set(used_values)))
        behavior_type = random.randint(1, 6)
        namespace = random.randint(0, namespaces)
        dword_size = random.randint(1, 8)
        max_value = random.randint(0, (2 ** (dword_size * 4)) - 1)
        min_value = random.randint(0, max_value)
        data_area = random.randint(1, 2)
        definition = f"Random Statistic Variable number {x} {identifier}"
        used_values.append(identifier)

        ocp_data["Statistics"]["Vendor Defined"]["Specific Fields"][definition] = {
            "Identifier": identifier,
            "Value Max": max_value,
            "Value Min": min_value,
            "Dword Size": dword_size,
            "Behavior Type": behavior_type,
            "Namespace": namespace,
            "Requirement": "STATI-31",
            "Definition": definition,
            "Data Area": data_area,
        }
    # Loop through the Vendor Defined statistics
    for stat, stat_value in ocp_data["Statistics"]["Vendor Defined"]["Specific Fields"].items():
        if stat_value["Data Area"] == 1:
            _area = "Data Area 1"
        elif stat_value["Data Area"] == 2:
            _area = "Data Area 2"
        else:
            sys.exit(f"Statistics {stat} has an invalid Data Area value of {stat_value['Data Area']}")

        stat_data = generate_statistic(stat_value, stat, namespaces)

        # Validate the Identifier is not already used.
        for key in statistics[_area]:
            if statistics[_area][key]["Identifier"] == stat_data["Identifier"]:
                sys.exit(f"Statistic '{stat}' and '{key}' have the same identifier value of {stat_data['Identifier']}")

        # Validate the Identifier value - Just checking range
        if (stat_data["Identifier"] < 0x8000) or (stat_data["Identifier"] > 0xFFFF):
            sys.exit(f"Statistic '{stat}' has an invalid identifier value of {stat_data['Identifier']}")

        identifier = stat_data["Identifier"]
        statistics[_area][hex(identifier)] = stat_data
        statistics[f"{_area} Identifiers"].append(hex(identifier))

    # Build the tables
    data_area_1_stat_table = bytearray()
    for _, value in statistics["Data Area 1"].items():
        data_area_1_stat_table += value["Descriptor"]

    data_area_2_stat_table = bytearray()
    for _, value in statistics["Data Area 2"].items():
        data_area_2_stat_table += value["Descriptor"]

    statistics["Data Area 1 Table"] = data_area_1_stat_table
    statistics["Data Area 2 Table"] = data_area_2_stat_table

    return statistics


debug_class_size = 1
event_id_size = 2

# Generate a Vendor Unique Identifier
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         vu_strings   : Information to generate vu string
#
# Output: A tuple containing
#
#      (<vu string name for identifier>, <identifier>)


def get_vu_id_event_info(fifo_number, event_number, vu_strings):

    vu_event_id = random.randint(0x0000, 0xFFFF)

    idx = hex(vu_event_id)
    name = f"Vendor Unique Identifier {fifo_number} {event_number} 0x{vu_event_id:x}"

    # Create the event if one does not already exist
    if idx not in vu_strings:
        vu_strings[idx] = {
            "name": name,
            "identifier": vu_event_id,
        }

    return (vu_strings[idx]["name"], vu_strings[idx]["identifier"])


# Generate a Vendor Unique Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a vendor unique event
#
#      {'name'        : string to identify the event,
#       'class'       : VU debug class,
#       'event id'    : vendor unique identifier,
#       'descriptor'  : event descriptot}
#
def vendor_unique_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    debug_class = random.randint(0x80, 0xFF)
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")                                       #    00 Debug VU Class

    (vu_name, vu_event) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
    event += vu_event.to_bytes(event_id_size, "little")                                             # 02:01 Debug VU Event

    vu_dwordsize = random.randint(1, 8)
    event += vu_dwordsize.to_bytes(1, "little")                                                     #    03 Event Data Size

    event += random.randint(0, (2 ** (vu_dwordsize * 4)) - 1).to_bytes(vu_dwordsize * 4, "little")  # **:04 Event Data

    return_data = {
        "name": f"Vendor Unique Event {fifo_number} {event_number} 0x{vu_event:x}",
        "class": debug_class,
        "event id": vu_event,
        "descriptor": event,
    }
    return return_data


# Generate a Static Snapshot Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Static Snapshot event
#
#      'name'        : string to identify the event,
#      'class'       : debug class,
#      'descriptor'  : event descriptor}
#
def static_snapshot_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 10
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #    00  Debug Event Class Code
    event += (0).to_bytes(3, "little")                         # 03:01 Reserved

    # Need to select a statistic identifier that is defined.

    # Select a data area to choose form

    if (len(statistics["Data Area 1 Identifiers"]) == 0) and (len(statistics["Data Area 2 Identifiers"]) == 0):
        sys.exit("Cannot randomly select a snapshot event, please define an event")
    elif (len(statistics["Data Area 1 Identifiers"]) > 0) and (len(statistics["Data Area 2 Identifiers"]) == 0):
        data_area = 1
    elif (len(statistics["Data Area 1 Identifiers"]) == 0) and (len(statistics["Data Area 2 Identifiers"]) > 0):
        data_area = 2
    else:
        data_area = random.randint(1, 2)

    # Select a statistics to snapshot - with the same data
    data_area_str = f"Data Area {data_area}"
    ran_idx = random.randint(0, len(statistics[f"{data_area_str} Identifiers"]) - 1)

    statistics[f"{data_area_str} Identifiers"]

    element = statistics[f"{data_area_str} Identifiers"][ran_idx]

    event += statistics[data_area_str][element]["Descriptor"]  # XX:04 Descriptor

    return_data = {
        "name": f"Static Snapshot Event {fifo_number} {event_number}",
        "class": debug_class,
        "descriptor": event,
    }
    return return_data


# Generate a Media Wear Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Media Wear event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def media_wear_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 9
    non_vu_size = 3
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")        #     00  Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = 0
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")              #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                      #     03 Event Id

    event += random.randint(0, 2 ** (32 - 1)).to_bytes(4, "little")  #  07:04 Host Terabytes Written
    event += random.randint(0, 2 ** (32 - 1)).to_bytes(4, "little")  #  11:08 Media Terabytes Written
    event += random.randint(0, 2 ** (32 - 1)).to_bytes(4, "little")  #  15:12 Host Terabytes Erased

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, 2 ** (vu_data_size_bytes * 8) - 1).to_bytes(vu_data_size_bytes, "little")

    # Build the return data
    return_data = {
        "name": f"Media Wear Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a Media Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Media event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def media_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 8
    non_vu_size = 0
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 5)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"Media Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a Temperature Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Temperature event
#
#      return_data = {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def temperature_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 7
    non_vu_size = 0
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 2)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"Temperature Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a Firmware Assert Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Firmware Assert event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def fw_assert_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 6
    non_vu_size = 0
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 6)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"FW Assert Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a Boot Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Boot Sequence event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def boot_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 5
    non_vu_size = 0
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 3)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"Boot Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a Reset Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Reset event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def reset_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 4
    non_vu_size = 0
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 4)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"Reset Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# NVMe valid opcode
nvme_admin_opcodes = [
    0x00,
    0x01,
    0x02,
    0x04,
    0x05,
    0x06,
    0x08,
    0x09,
    0x0A,
    0x0C,
    0x0D,
    0x10,
    0x11,
    0x14,
    0x15,
    0x18,
    0x19,
    0x1A,
    0x1C,
    0x1D,
    0x1E,
    0x20,
    0x24,
    0x7C,
    0x7F,
    0x80,
    0x81,
    0x82,
    0x84,
    0x86,
]

nvme_io_opcodes = [0x00, 0x01, 0x02, 0x04, 0x05, 0x08, 0x09, 0x0C, 0x0D, 0x0E, 0x11, 0x12, 0x15, 0x18, 0x19, 0x1D]


# Generate a NVMe Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a NVMe event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def nvme_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 3
    non_vu_size = 2
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")                                        #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 12)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")                                              #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 8)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                                                      #     03 Dword size

    if event_id == 7:
        event += nvme_admin_opcodes[random.randint(0, len(nvme_admin_opcodes) - 1)].to_bytes(1, "little")
        event += random.randint(1, 5).to_bytes(2, "little")                                          #  status #fix me can be more precise
        event += (0).to_bytes(5, "little")
    elif event_id == 8:
        event += nvme_io_opcodes[random.randint(0, len(nvme_io_opcodes) - 1)].to_bytes(1, "little")  #  opcode for I/O command
        event += random.randint(1, 5).to_bytes(2, "little")                                          #  status #fix me can be more precise
        event += (0).to_bytes(5, "little")
    elif event_id == 0xB:
        event += random.randint(0, (2 ** 32) - 1).to_bytes(4, "little")                              #  CC #fix me can be more precise
        event += (0).to_bytes(4, "little")
    elif event_id == 0xC:
        event += random.randint(0, (2 ** 32) - 1).to_bytes(4, "little")                              #  CSTS #fix me can be more precise
        event += (0).to_bytes(4, "little")
    else:
        event += (0).to_bytes(8, "little")

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"NVMe Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a PCIe Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a PCIe event
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def pcie_event(fifo_number, event_number, statistics, vu_strings):

    global debug_class_size
    global event_id_size
    debug_class = 2
    non_vu_size = 1
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 7)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 4)) + non_vu_size
    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size

    if event_id == 7:
        event += random.randint(0, 2).to_bytes(1, "little")    #  state changed
        event += random.randint(1, 7).to_bytes(1, "little")    #  link speed
        event += random.randint(1, 5).to_bytes(1, "little")    #  link width
        event += (0).to_bytes(1, "little")                     #  reserved
    else:
        event += (0).to_bytes(4, "little")

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"PCIe Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


# Generate a Timestamp Debug Event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for a Timestamp
#
#                    {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def timestamp_event(fifo_number, event_number, statistics, vu_strings):
    global debug_class_size
    global event_id_size
    debug_class = 1
    non_vu_size = 2
    event = bytearray()
    event += debug_class.to_bytes(debug_class_size, "little")  #     00 Debug Event Class
    if random.randint(0, 1) == 0:
        event_id = random.randint(0, 2)
    else:
        event_id = random.randint(0x8000, 0xFFFF)
    event += event_id.to_bytes(event_id_size, "little")        #  02:01 Event Id

    vu_dwordsize = (random.randint(0, 1) * random.randint(1, 4)) + non_vu_size

    event += vu_dwordsize.to_bytes(1, "little")                #     03 Dword size
    nvme_timestamp(event)

    if vu_dwordsize > non_vu_size:
        (vu_name, vu_event_id) = get_vu_id_event_info(fifo_number, event_number, vu_strings)
        event += vu_event_id.to_bytes(2, "little")
        vu_data_size_bytes = ((vu_dwordsize - non_vu_size) * 4) - 2
        event += random.randint(0, (2 ** (vu_data_size_bytes * 8)) - 1).to_bytes(vu_data_size_bytes, "little")

    return_data = {
        "name": f"Timestamp Event {fifo_number} {event_number}",
        "class": debug_class,
        "event id": event_id,
        "descriptor": event,
    }

    if vu_dwordsize > non_vu_size:
        return_data["vu_event"] = vu_event_id
        return_data["vu_string"] = vu_name

    return return_data


event_functions = [
    timestamp_event,
    pcie_event,
    nvme_event,
    reset_event,
    boot_event,
    fw_assert_event,
    temperature_event,
    static_snapshot_event,
    vendor_unique_event,
]

# Genertate an event
#
# Input:
#         fifo_number  : FIFO that the event is to exist
#         event_number : number of event in the FIFO
#         statistics   : Dictionary of statistics
#         vu_strings   : Information to generate vu strings in the string log
#
# Output: A dictionary entry for an event
#
#      return_data = {'name'        : string to identify the event,
#                     'class'       : debug class,
#                     'descriptor'  : event descriptor,
#      <optional>     'vu_event'    : Unique Vendor ID,
#      <optional>     'vu_string'   : String for vendor id}
#
def get_event(fifo_number, event_number, statistics, vu_event):
    return event_functions[random.randint(0, len(event_functions) - 1)](fifo_number, event_number, statistics, vu_event)


# Generate the fifo information
#
# Input:
#         ocp_data     : Parsed data read from JSON file
#         statistics   : Dictionary of statistics
#
# Output: A dictionary entry for the fifos
#
#      {'Data Area 1' : {<FIFO #> : {'name'        : string to identify the event,
#                                    'class'       : debug class,
#                                    'descriptor'  : event descriptor,
#                     <optional>     'vu_event'    : Unique Vendor ID,
#                     <optional>     'vu_string'   : String for vendor id}, ... },}
#      {'Data Area 2' : {<FIFO #> : {'name'        : string to identify the event,
#                                    'class'       : debug class,
#                                    'descriptor'  : event descriptor,
#                     <optional>     'vu_event'    : Unique Vendor ID,
#                     <optional>     'vu_string'   : String for vendor id}, ...}, ...}}
#
def get_fifo(ocp_data, statistics):

    vu_strings = {}

    fifo = {"Data Area 1": {}, "Data Area 2": {}}

    # Loop through the defined FIFO
    for stat, stat_value in ocp_data["Debug FIFOs"].items():

        fifo_area = bytearray()
        if stat_value["size"] > 0:

            # Extract the FIF0 #
            fifo_number = int(stat)

            data_area_value = stat_value["Data Area"]
            if (data_area_value < 0) or (data_area_value > 2):
                sys.exit(f"FIFO '{stat_value['name']}' has invalid Data Area value of {data_area_value}")
            data_area = f"Data Area {data_area_value}"

            if stat not in fifo[data_area]:
                fifo[data_area][stat] = {"Events": {}, "name": stat_value["name"]}

            # Loop through the events for this FIFO

            fifo_area = bytearray()
            for x in range(stat_value["Max Events"]):

                # Get an event
                event = get_event(fifo_number, x, statistics, vu_strings)

                # Append the event to the FIFO, if there is room
                if (len(event) + len(fifo_area)) > stat_value["size"]:
                    break

                fifo_area += event["descriptor"]

                fifo[data_area][stat]["Events"][str(x)] = event

        # Fill in the FIFO area to the size of the FIFO

        if (stat_value["size"] - len(fifo_area)) > 0:
            fifo_area += bytearray(stat_value["size"] - len(fifo_area))

        if stat not in fifo[data_area]:
            fifo[data_area][stat] = {}

        fifo[data_area][stat]["area"] = fifo_area

    return fifo


# Convert hex string to bytearray
#
# Input:
#         string  : hex string
#         bytes   : # of bytes in the string
#         order   : 'little' or 'big'
#
# Output: bytearray of value of hex string
#
def hex_str_2_bytes(string, bytes, order):

    hex_data = string.decode("hex")
    return hex_data.to_bytes(bytes, order)


# Generate the String Log
#
# Input:
#         statistics   : Dictionary of statistics
#         fifo         : FIFO information
#
# Output: Dictionary containing
#
#       {'size' : string_log_size,
#        'log'  : string_log}
#
def generate_string_log(statistics, fifo):

    strings = bytearray()
    static_identifier_string_table = bytearray()
    event_string_table = bytearray()
    vu_event_header_string_table = bytearray()

    stat_count = 0

    # Loop through Data Area 1 statistics and build the list of table entries

    print("Generating the Strings log page:")

    print("\tBuilding Statistics Identifier String Table...")

    table_data = {}

    for _area in ["Data Area 1", "Data Area 2"]:
        for _, stat_value in statistics[_area].items():
            if stat_value["Identifier"] >= 0x8000:
                # Build the Statics Identyifier string table entry
                table_entry = bytearray()
                identifier = stat_value["Identifier"]
                table_entry += identifier.to_bytes(2, "little")
                table_entry += (0).to_bytes(1, "little")
                if len(stat_value["String"]) > 256:
                    sys.exit(f"String too long : {stat_value['String']}")
                table_entry += (len(stat_value["String"]) - 1).to_bytes(1, "little")
                table_entry += (len(strings) // 4).to_bytes(8, "little")
                table_entry += (0).to_bytes(4, "little")

                id_string = stat_value["String"].encode()
                strings += id_string
                mod_num = len(id_string) % 4
                if mod_num != 0:
                    for x in range(4 - mod_num):
                        strings += (0x20).to_bytes(1, "little")

                table_data[hex(identifier)] = table_entry

                stat_count += 1

    # Now sort the statistics
    identifier_list = []
    for identifier in table_data:
        identifier_list.append(int(identifier, 16))
    identifier_list.sort()

    for identifier in identifier_list:
        static_identifier_string_table += table_data[hex(identifier)]

    print("\tBuilding Vendor Uniquie Events String Table...")
    vu_id_list = []
    table_data = {}
    # Loop through Data Area 1 FIFOs and build the list of table entries for VUs
    for _area in ["Data Area 1", "Data Area 2"]:
        for _, stat_value in fifo[_area].items():
            for _, event_value in stat_value["Events"].items():
                if event_value["class"] >= 0x80:
                    debug_class = event_value["class"]
                    identifier = event_value["event id"]
                    idx = hex(debug_class) + hex(identifier)

                    # Add entry if not already added
                    if idx not in vu_id_list:
                        # Build the Event Identyifier string table entry
                        table_entry = bytearray()
                        table_entry += (debug_class).to_bytes(1, "little")
                        table_entry += (identifier).to_bytes(2, "little")

                        if len(event_value["name"]) > 256:
                            sys.exit(f"String too long : {event_value['name']}")
                        table_entry += (len(event_value["name"]) - 1).to_bytes(1, "little")
                        table_entry += (len(strings) // 4).to_bytes(8, "little")
                        table_entry += (0).to_bytes(4, "little")

                        id_string = event_value["name"].encode()
                        strings += id_string
                        mod_num = len(id_string) % 4
                        if mod_num != 0:
                            for x in range(4 - mod_num):
                                strings += (0x20).to_bytes(1, "little")

                        if hex(debug_class) in table_data:
                            table_data[hex(debug_class)][hex(identifier)] = table_entry
                        else:
                            table_data[hex(debug_class)] = {hex(identifier): table_entry}

                        vu_id_list.append(idx)

    # Now sort the Vendor Unique Events based on debug class then identifier
    debug_class_list = []
    for debug_class in table_data:
        debug_class_list.append(int(debug_class, 16))
    debug_class_list.sort()

    for debug_class in debug_class_list:

        identifier_list = []
        for identifier in table_data[hex(debug_class)]:
            identifier_list.append(int(identifier, 16))
        identifier_list.sort()

        for identifier in identifier_list:
            event_string_table += table_data[hex(debug_class)][hex(identifier)]

    print("\tBuilding Vendor Uniquie Event VU Header Data String Table...")

    table_data = {}

    # Loop through Data Area 1 FIFOs and build the list of table entries for VU data in OCP defined events
    vu_header_ids = []
    for _area in ["Data Area 1", "Data Area 2"]:
        for _, stat_value in fifo[_area].items():
            for _, event_value in stat_value["Events"].items():
                if event_value["class"] < 9:
                    if "vu_string" in event_value:
                        class_type = event_value["class"]
                        vu_identifier = event_value["vu_event"]

                        # only build it is not already built
                        idx = hex(class_type) + hex(vu_identifier)
                        if idx not in vu_header_ids:

                            # Build the VU Event Data Header table entry
                            table_entry = bytearray()
                            table_entry = (class_type).to_bytes(1, "little")
                            table_entry += (vu_identifier).to_bytes(2, "little")
                            if len(event_value["vu_string"]) > 256:
                                sys.exit(f"VU Event String  too long : {event_value['vu_string']}")
                            table_entry += (len(event_value["vu_string"]) - 1).to_bytes(1, "little")
                            table_entry += (len(strings) // 4).to_bytes(8, "little")
                            table_entry += (0).to_bytes(4, "little")

                            id_string = event_value["vu_string"].encode()
                            strings += id_string
                            mod_num = len(id_string) % 4
                            if mod_num != 0:
                                for x in range(4 - mod_num):
                                    strings += (0x20).to_bytes(1, "little")

                            if hex(class_type) in table_data:
                                table_data[hex(class_type)][hex(vu_identifier)] = table_entry
                            else:
                                table_data[hex(class_type)] = {hex(vu_identifier): table_entry}

                            if len(table_entry) != 16:
                                sys.exit("VU Event table entry not the proper size")

                            vu_header_ids.append(idx)

    # Now sort the Vendor Unique VU Headers based on debug class then identifier
    debug_class_list = []
    for debug_class in table_data:
        debug_class_list.append(int(debug_class, 16))
    debug_class_list.sort()

    for debug_class in debug_class_list:

        identifier_list = []
        for identifier in table_data[hex(debug_class)]:
            identifier_list.append(int(identifier, 16))
        identifier_list.sort()

        for identifier in identifier_list:
            vu_event_header_string_table += table_data[hex(debug_class)][hex(identifier)]

    print("\tBuilding String log header...")

    hdr_sze = 432

    string_log = bytearray()
    string_log += (1).to_bytes(1, "little")                                                     #     0     Log Version
    string_log += (0).to_bytes(15, "little")                                                    #  15:1     Reserevd
    string_log += (0xB13A83691A8F408B9EA495940057AA44).to_bytes(16, "little")

    string_log_size = hdr_sze
    string_log_size += len(static_identifier_string_table)
    string_log_size += len(event_string_table)
    string_log_size += len(vu_event_header_string_table)
    string_log_size += len(strings)

    string_log += (string_log_size // 4).to_bytes(8, "little")                                  #  39:32    String Log Size
    string_log += bytearray(24)                                                                 #  63:40    Reserevd

    string_log += (hdr_sze // 4).to_bytes(8, "little")                                          #  71:64    Statistics Ident Start
    string_log += (len(static_identifier_string_table) // 4).to_bytes(8, "little")              #  79:72    Statistics Ident Size
    string_log += ((hdr_sze + len(static_identifier_string_table)) // 4).to_bytes(8, "little")  #  87:80    Event Ident Start
    string_log += (len(event_string_table) // 4).to_bytes(8, "little")                          #  95:88    Event Ident Size
    string_log += ((hdr_sze + len(static_identifier_string_table) + len(event_string_table)) // 4).to_bytes(
        8, "little"
    )                                                                                           # 103:96    VU Event Ident Start
    string_log += (len(vu_event_header_string_table) // 4).to_bytes(8, "little")                # 111:104    VU Event Ident Size
    string_log += (
        (
            hdr_sze
            + len(static_identifier_string_table)
            + len(event_string_table)                                                           # 119:112   ASCII Start
            + len(vu_event_header_string_table)
        )
        // 4
    ).to_bytes(8, "little")
    string_log += (len(strings) // 4).to_bytes(8, "little")                                     # 127:120   ASCII table size

    # Build the FIFO name list                                                                  # 383:128   FIFO names[1:16]
    for x in range(1, 17):
        if str(x) in fifo["Data Area 1"]:
            name = fifo["Data Area 1"][str(x)]["name"]
        elif str(x) in fifo["Data Area 2"]:
            name = fifo["Data Area 2"][str(x)]["name"]
        else:
            name = ""

        if len(name) > 16:
            sys.exit(f"FIFO {x} name is more than 16 characters: {name}")
        name_array = bytearray(name.encode("utf-8"))
        if len(name) != 16:
            name_array += bytearray(16 - len(name))
        string_log += name_array

    string_log += bytearray(431 - 384 + 1)                                                      # 431:384   Reserved
    print(f"\tStatistics Start : {len(string_log)} (0x{len(string_log) // 4:x})")
    string_log += static_identifier_string_table
    print(f"\tEvent Start : {len(string_log)} (0x{len(string_log) // 4:x})")
    string_log += event_string_table
    print(f"\tVU Event Start : {len(string_log)} (0x{len(string_log) // 4:x})")
    string_log += vu_event_header_string_table
    print(f"\tASCII Start : {len(string_log)} (0x{len(string_log) // 4:x})")
    string_log += strings
    print(f"\tString log size : {len(string_log)} (0x{len(string_log) // 4:x})")

    return {"size": string_log_size, "log": string_log}


# Get FIFO Data Area location
#
# Input:
#         fifo         : FIFO information
#         fifo_num     : FIFO number
#
# Output: Data Area location (i.e, 1 or 2) or 0 to mean FIFO does not exist
#
def get_fifo_location(fifo, fifo_num):

    if str(fifo_num) in fifo["Data Area 1"]:
        data_location = 1
    elif str(fifo_num) in fifo["Data Area 2"]:
        data_location = 2
    else:
        data_location = 0
    return int(data_location)


# Get FIFO start and end locations of the fifo
#
# Input:
#         statistics   : Dictionary of statistics
#         fifo         : FIFO information
#         fifo_num     : FIFO number
#
# Output: Touple of (start, size) in dwords
#
def get_fifo_start_end(statistics, fifo, fifo_num):

    # FIFOs are place in order in each data area after the statistics

    # Determine the data area
    if str(fifo_num) in fifo["Data Area 1"]:
        data_area = "Data Area 1"
        offset = 1536 + len(statistics["Data Area 1 Table"])  # from the start of the log page
    elif str(fifo_num) in fifo["Data Area 2"]:
        data_area = "Data Area 2"
        offset = len(statistics["Data Area 2 Table"])
    else:
        # Does not exist so clear the data;
        return (0, 0)

    # Add in the size of the statistics area

    # Loop through the FIFO's in order and determine the start and end sizes
    if fifo_num > 1:
        for x in range(1, fifo_num):
            fifo_str = str(x)
            if fifo_str in fifo[data_area]:
                offset += len(fifo[data_area][fifo_str]["area"])

    start = offset // 4
    size = len(fifo[data_area][str(fifo_num)]["area"])

    return (start, size)


# Generate a dummy SMART / Information log page 02h
#
# Input: None
#
# Output: bytearray containing a dummy dummy SMART / Information log page 02h
#
def get_log_02():

    data = bytearray()
    data += random.randint(0, (2 ** 6) - 1).to_bytes(1, "little")        #     000  Critical Warning
    data += random.randint(255, 305).to_bytes(2, "little")               # 002:001  Composite (0F to 90F)
    data += random.randint(0, 100).to_bytes(1, "little")                 #     003  Available spare
    data += random.randint(0, 100).to_bytes(1, "little")                 #     004  Available spare threshold
    data += random.randint(0, 100).to_bytes(1, "little")                 #     005  percentage used
    data += bytearray(1)                                                 #     006  Endurance Group Critical Warning
    data += bytearray(25)                                                # 031:007  Resereved
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 047:032  Data Units Read
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 063:048  Data Units Written
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 079:064  Host Read Commands
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 095:080  Host Write Commands
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 111:096  Host Busy time
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 127:112  Power Cycles
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 143:128  Power On Hours
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 159:144  Unsafe Shutdown
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 175:160  Media and Data Integrity Errors
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")  # 191:176  Error Information Entries
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")    # 195:192  Warning Composite Temperate Time
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")    # 199:196  Critical Composite Temperate Time
    data += random.randint(255, 305).to_bytes(2, "little")               # 201:200  Temperature Sensor 1
    data += random.randint(255, 305).to_bytes(2, "little")               # 203:202  Temperature Sensor 2
    data += random.randint(255, 305).to_bytes(2, "little")               # 205:204  Temperature Sensor 3
    data += random.randint(255, 305).to_bytes(2, "little")               # 207:206  Temperature Sensor 4
    data += random.randint(255, 305).to_bytes(2, "little")               # 209:208  Temperature Sensor 5
    data += random.randint(255, 305).to_bytes(2, "little")               # 211:210  Temperature Sensor 6
    data += random.randint(255, 305).to_bytes(2, "little")               # 213:212  Temperature Sensor 7
    data += random.randint(255, 305).to_bytes(2, "little")               # 215:214  Temperature Sensor 8
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")    # 219:216  Thermal Management Temperature 1 Transition Count
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")    # 223:220  Thermal Management Temperature 2 Transition Count
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")    # 227:224  Total Time For Thermal Management Temperature 1
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")    # 231:228  Total Time For Thermal Management Temperature 2
    data += bytearray(280)                                               # 511:232  Reserved

    if len(data) != 512:
        sys.exit(f"SMART / Health Information log page 02h wrong size: {len(data)}")

    return data


# Generate a dummy SMART / Health Information Extentipon log page C0h
#
# Input: None
#
# Output: bytearray containing a dummy dummy SMART / Information Extentipon log page C0h
#
def get_log_c0():
    data = bytearray()
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")     # 015:000 Physical Media Units Written
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")     # 031:016 Physical Media Units Read
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(6, "little")       # 037:032 Bad User NAND Blocks Raw Count
    data += random.randint(0, 100).to_bytes(2, "little")                    # 039:038 Bad User NAND Blocks Normalized value
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(6, "little")       # 045:040 Bad System NAND Blocks Raw Count
    data += random.randint(0, 100).to_bytes(2, "little")                    # 047:046 Bad System NAND Blocks Normalized value
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 055:048 XOR Recovery Count
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 063:056 Uncorrectable Read Error Count
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 071:064 Soft ECC Error Count
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 079:072 End to End Correction Counts
    data += random.randint(0, 2 ** (1 * 8) - 1).to_bytes(1, "little")       #     080 System Data % Used
    data += random.randint(0, 2 ** (7 * 8) - 1).to_bytes(7, "little")       # 087:081 System Data % Used
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 095:088 User Data Erase Counts
    data += random.randint(0, 2 ** (1 * 8) - 1).to_bytes(1, "little")       #     096 Thermal Throttling Count
    data += random.randint(0, 3).to_bytes(1, "little")                      #     097 Thermal Throttling Status
    data += (0).to_bytes(1, "little")                                       #     098 DSSD Specification Version Errata
    data += (0).to_bytes(2, "little")                                       # 100:099 DSSD Specification Version Point Version
    data += (5).to_bytes(2, "little")                                       # 102:101 DSSD Specification Version Minor Version
    data += (2).to_bytes(1, "little")                                       #     103 DSSD Specification Version Major Version
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 111:104 PCIe Correctable Error Count
    data += random.randint(0, 2 ** (4 * 8) - 1).to_bytes(4, "little")       # 115:112 Incomplete Shutdowns
    data += bytearray(4)                                                    # 119:116 Reserved
    data += random.randint(0, 100).to_bytes(1, "little")                    #     120 % Free Blocks
    data += bytearray(7)                                                    # 127:121 Reserved
    data += random.randint(0, 2 ** (2 * 8) - 1).to_bytes(2, "little")       # 129:128 Capacitor Health
    data += (99).to_bytes(1, "little")                                      #     130 NVMe Errata Version 'c'
    data += bytearray(5)                                                    # 135:131 Reserved
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 143:136 Unaligned I/O
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 151:144 Security Version Number
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 159:152 Total NUSE
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")     # 175:160 PLP Start Count
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")     # 191:176 Endurance Estimate
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 199:192 PCIe Link Retraining Count
    data += random.randint(0, 2 ** (8 * 8) - 1).to_bytes(8, "little")       # 207:200 Power State Change Count
    data += random.randint(0, 2 ** (16 * 8) - 1).to_bytes(16, "little")     # 223:208 Hardware Version
    data += bytearray(493 - 224 + 1)                                        # 493:224 Reserved
    data += (3).to_bytes(2, "little")                                       # 495:494 Log Page Version
    data += int(0xAFD514C97C6F4F9CA4F2BFEA2810AFC5).to_bytes(16, "little")  # 511:496 Log PAge GUID
    if len(data) != 512:
        sys.exit("SMART / Health Information Extension log page C0h wrong size")
    return data


# Generate Data Area 1
#
# Input:
#         ocp_data        : Parsed data read from JSON file
#         statistics      : Dictionary of statistics
#         fifo            : FIFO information
#         string_log_size : string log size in bytes
#
# Output: bytearray containing Data Area 1
#
def generate_data_area_1(ocp_data, statistics, fifo, string_log_size):
    print("Generating Data Area 1:")

    if ocp_data["size"] <= 1028:
        sys.exit("Data Area 1 Size too small as it must be larger than 2048 bytes")

    data_area_1 = bytearray()
    print(f"\tData Area 1 Header Offset : 0x{len(data_area_1):x}")
    data_area_1 += (3).to_bytes(2, "little")                                          #   1:0     Major Version
    data_area_1 += (1).to_bytes(2, "little")                                          #   3:2     minor Version
    data_area_1 += (0).to_bytes(4, "little")                                          #   7:4     Resereved
    nvme_timestamp(data_area_1)                                                       #  15:8     Timestamp
    data_area_1 += int(0xBA560A9C3043424CBC73719D87E64EFA).to_bytes(16, "little")     #  31:16    GUID
    number_profiles = random.randint(2, 10)
    data_area_1 += number_profiles.to_bytes(1, "little")                              #     32    Profiles
    data_area_1 += random.randint(1, number_profiles).to_bytes(1, "little")           #     33    Profile Selected
    data_area_1 += (0).to_bytes(6, "little")                                          #  39:34    Reserved
    data_area_1 += (string_log_size // 4).to_bytes(8, "little")                       #  47:40    Strng Log Size
    data_area_1 += (0).to_bytes(8, "little")                                          #  55:48    Reserved

    fw_verison_str = "FIRM: XX"
    data_area_1 += fw_verison_str.encode()                                            #   63:56   FW Version string
    data_area_1 += (0).to_bytes(32, "little")                                         #   95:64   Reserved
    data_area_1 += (2048 // 4).to_bytes(8, "little")                                  #  103:96   Data Area 1 Statistics start
    data_area_1 += (len(statistics["Data Area 1 Table"]) // 4).to_bytes(8, "little")  #  111:104  Data Area 1 Statistics size
    data_area_1 += (0).to_bytes(8, "little")                                          #  119:112  Data Area 2 Statistics start
    data_area_1 += (len(statistics["Data Area 2 Table"]) // 4).to_bytes(8, "little")  #  127:120  Data Area 2 Statistics size
    data_area_1 += (0).to_bytes(32, "little")                                         #  159:128  Reserved

    for x in range(1, 17):
        data_area_1 += get_fifo_location(fifo, x).to_bytes(1, "little")               #  175:160  FIFO 1 location

    for x in range(1, 17):
        (start, size) = get_fifo_start_end(statistics, fifo, x)
        data_area_1 += start.to_bytes(8, "little")                                    #  431:176  FIFO 1 dw start/size
        data_area_1 += (size // 4).to_bytes(8, "little")

    data_area_1 += bytearray(80)                                                      #  511:432  FIFO 15 dw end

    log_page = get_log_02()
    print(f"\t\tSmart / Health Information log page Offset : 0x{len(data_area_1):x} (Length : 0x{len(log_page):x})")
    data_area_1 += log_page                                                           # 1023:512  SMART / Health log page (02h)

    log_page = get_log_c0()
    print(f"\t\tSmart / Health Information Extended log page Offset : 0x{len(data_area_1):x} (Length : 0x{len(log_page):x})")
    data_area_1 += log_page                                                           # 1535:1024 SMART / Health Extended log page (C0h)

    print(f"\t\tData Area 1 Header Size : {len(data_area_1)} (0x{len(log_page):x})")

    if ocp_data["size"] < len(data_area_1) + len(statistics["Data Area 1 Table"]):
        sys.exit("Data Area 1 Size too small to include statistics area")

    print(f"\tStatistics Table Offset : 0x{len(data_area_1):x} (Length : 0x{len(statistics['Data Area 1 Table']):x})")
    data_area_1 += statistics["Data Area 1 Table"]

    for x in range(1, 17):
        fifo_str = str(x)
        if fifo_str in fifo["Data Area 1"]:
            if ocp_data["size"] < len(data_area_1) + len(fifo["Data Area 1"][fifo_str]["area"]):
                sys.exit(f"Data Area 1 Size too small to include FIFO {x}")

            print(f"\tFIFO {fifo_str} Offset : 0x{len(data_area_1):x} (Length : 0x{len(fifo['Data Area 1'][fifo_str]['area']):x})")
            data_area_1 += fifo["Data Area 1"][fifo_str]["area"]

    # zero fill the remainder of Data Area 1
    if ocp_data["size"] > len(data_area_1):
        print(f"\tZero Fill Offset : 0x{len(data_area_1):x} (Length : 0x{ocp_data['size'] - len(data_area_1):x})")
        data_area_1 += bytearray(ocp_data["size"] - len(data_area_1))

    print(f"\tData Area 1 Length: {len(data_area_1)} (0x{len(data_area_1):x})")

    return data_area_1


# Generate Data Area 2
#
# Input:
#         ocp_data     : Parsed data read from JSON file
#         statistics   : Dictionary of statistics
#         fifo         : FIFO information
#
# Output: bytearray containing Data Area 2
#
def generate_data_area_2(ocp_data, statistics, fifo):

    print("Generating Data Area 2:")

    # statistics
    data_area_2 = bytearray()

    print(f"\tStatistics Table Offset : 0x{len(data_area_2):x} (Length : 0x{len(statistics['Data Area 2 Table']):x})")
    if ocp_data["size"] < len(statistics["Data Area 2 Table"]):
        sys.exit("Data Area 2 Size too small to include statistics area")

    data_area_2 += statistics["Data Area 2 Table"]

    for x in range(1, 17):
        idx = str(x)
        if idx in fifo["Data Area 2"]:
            if ocp_data["size"] < len(data_area_2) + len(fifo["Data Area 2"][idx]["area"]):
                sys.exit(f"Data Area 2 Size too small to include FIFO {x}")

            print(f"\tFIFO {idx} Offset : 0x{len(data_area_2):x} (Length : 0x{len(fifo['Data Area 2'][idx]['area']):x})")
            data_area_2 += fifo["Data Area 2"][idx]["area"]

    # zero fill the remainder of the data area
    if ocp_data["size"] > len(data_area_2):
        print(f"\tZero Fill Offset : 0x{len(data_area_2):x} (Length : 0x{ocp_data['size'] - len(data_area_2):x})")
        data_area_2 += bytearray(ocp_data["size"] - (len(data_area_2)))

    print(f"\tData Area 2 Length: {len(data_area_2)} (0x{len(data_area_2):x})")
    return data_area_2


# Need a defult JSON file if the user does not specify a --telemetry option
json_default = "ocp_debug.json"

# Parse the input parameters
#
# Input: None
#
# Output: Input parameters
#
def parse_inputs():

    telemetry_default = "telemetry.bin"
    string_default = "string.bin"
    json_default = "ocp_debug.json"

    # Add the agruments
    parser = argparse.ArgumentParser(
        prog="ocp_generate_nvme_telemtry.py",
        description="This script uses a JSON file to define the settings for generating an NVMe(TM) Telemetry log page  "
        " and a OCP Strings log page based on the OCP Datacenter NVMe SSD specification " + ocp_ver + ". A sample JSON file can be "
        " generated using the -g option. If a JSON file is not specified, then information from the sample JSON file is used. "
        " This script by default generates an NVMe(TM) Telemetry Host-Initiated log page but the --controller (-c) "
        " commandline argument causes an NVMe(TM) Telemetry Controller-Initiated log page to be generated.",
        epilog="The generated Telemetry Host-Initiated log page while formated per the specifications contains random information.",
    )

    parser.add_argument(
        "-j",
        "--json",
        type=str,
        dest="json",
        required=False,
        metavar="<filename>",
        help="Specify JSON filename\n\n"
        + "If -g is specified on the commandline, then this defines the"
        + "output filename to contain a sample JSON file. If -g is not "
        + "specified on the commandline, then this defines the input filename "
        + json_default
        + "to contain a JSON file used to create the Telemetry and OCP Strings log pages.",
    )
    parser.add_argument(
        "-c",
        "--controller",
        action="store_true",
        default=False,
        dest="controller",
        required=False,
        help="Generate a Telemetry Controller-Initiated log page",
    )
    parser.add_argument(
        "-g",
        "--generate",
        action="store_true",
        dest="generate",
        required=False,
        help="Generate a sample JSON file.  If -t is not "
        + "specified on the commandline, then the output filename "
        + json_default
        + "to contain a JSON file used to create the Telemetry and OCP Strings log pages.",
    )
    parser.add_argument(
        "-t",
        "--telemetry",
        type=str,
        dest="telemetry",
        required=False,
        metavar="<filename>",
        default=telemetry_default,
        help="Telemetry log page filename."
        + "If -g is not specified on the commandline, then this defines the output filename"
        + "to contain the Telemetry Host-Initiated log page. If not specified then the filename '"
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
        default=string_default,
        help="OCP Strings log page (C9h) filename. "
        + "If -g is not specified on the commandline, then this defines the output filename"
        + "to contain the OCP Strings log page. If not specified then the filename '"
        + string_default
        + "' is used.",
    )
    parser.add_argument(
        "-r",
        "--random",
        type=int,
        dest="random",
        required=False,
        metavar="<value>",
        help="Specify the random seed value so that log pages with different content can be generated.",
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

elif args.generate:

    # Use the default filename if the -t option is not on the commandline
    if args.telemetry != None:
        filename = json_default
    else:
        filename = args.json

    # Generate a sample JSON file
    with open(filename, "w") as f:
        f.write(sample_json)
        f.close()

else:

    # Setup the random seed
    if args.random != None:
        seed = args.random
    else:
        seed = random.randrange(sys.maxsize)
    random.seed(seed)

    print(f"Random Seed: {seed}")
    # Parse the JSON information
    if args.json == None:
        print("Opening sample JSON\n")
        ocp_debug_data = json.loads(sample_json)
    else:
        print(f"Opening provided file: {args.json}")
        with open(args.json, "r") as f:
            ocp_debug_data = json.load(f)

    # initilize the fake timestamp
    global_time = ocp_debug_data["Timestamp"]

    # Fix variables that have limitations per the spec.
    if ("Host Write Bandwidth" in ocp_debug_data["Statistics"]["OCP Defined"]) and (
        "GC Write Bandwidth" in ocp_debug_data["Statistics"]["OCP Defined"]
    ):

        # Pick the value
        host_value = random.randint(
            ocp_debug_data["Statistics"]["OCP Defined"]["Host Write Bandwidth"]["Value Min"],
            ocp_debug_data["Statistics"]["OCP Defined"]["Host Write Bandwidth"]["Value Max"],
        )
        gc_value = 100 - host_value

        # Validate the value
        if (gc_value < ocp_debug_data["Statistics"]["OCP Defined"]["GC Write Bandwidth"]["Value Min"]) or (
            gc_value > ocp_debug_data["Statistics"]["OCP Defined"]["GC Write Bandwidth"]["Value Max"]
        ):
            sys.exit("Statistics 'Host Write Bandwidth' and 'GC Write Bandwidth' min\/max value range error")

        # Save the selected values
        ocp_debug_data["Statistics"]["OCP Defined"]["Host Write Bandwidth"]["Value Min"] = host_value
        ocp_debug_data["Statistics"]["OCP Defined"]["Host Write Bandwidth"]["Value Max"] = host_value
        ocp_debug_data["Statistics"]["OCP Defined"]["GC Write Bandwidth"]["Value Min"] = gc_value
        ocp_debug_data["Statistics"]["OCP Defined"]["GC Write Bandwidth"]["Value Max"] = gc_value

    # Generate the statistics information
    statistics = get_statistics(ocp_debug_data)

    # Generate the Fifo Information
    fifo = get_fifo(ocp_debug_data, statistics)

    # The only difference between the Telemetry Host-Initiated log page and the Telemetry COntroller-Initiated log page
    # if the header.
    header = nvme_telemetry_host_controller_initiated_header(
        ocp_debug_data["Data Area 1"]["size"],
        ocp_debug_data["Data Area 2"]["size"],
        ocp_debug_data["Data Area 3"]["size"],
        ocp_debug_data["Data Area 4"]["size"],
        args.controller,
    )

    # Generate the strings log page
    string_log = generate_string_log(statistics, fifo)

    # Need to generate Data Area 2 before Data Area 1 as data from Data Area 2 exists in data area 1
    data_area_2 = generate_data_area_2(ocp_debug_data["Data Area 2"], statistics, fifo)
    data_area_1 = generate_data_area_1(ocp_debug_data["Data Area 1"], statistics, fifo, string_log["size"])
    data_area_3 = generate_data_area(3, ocp_debug_data["Data Area 3"]["size"])
    data_area_4 = generate_data_area(4, ocp_debug_data["Data Area 4"]["size"])

    # Compute the offsets to each data area relative to the Telemetry Host-Initiated log page
    data_area_1_offset = len(header)
    data_area_2_offset = data_area_1_offset + len(data_area_1)
    data_area_3_offset = data_area_2_offset + len(data_area_2)
    data_area_4_offset = data_area_3_offset + len(data_area_3)

    # Print the offsets which are very helpful for debugging this script
    print("\nBuilding NVMe Host-Initiated Telemetry log page:")
    print(f"\tHeader Start : 0x{0:x}")
    print(f"\tData Area 1 : 0x{data_area_1_offset:x}")
    print(f"\tData Area 2 : 0x{data_area_2_offset:x}")
    if data_area_3_offset > data_area_2_offset:
        print(f"\tData Area 3 : 0x{data_area_3_offset:x}")
    else:
        print("\tData Area 3 : Does not exist")
    if data_area_4_offset > data_area_3_offset:
        print(f"\tData Area 4 : 0x{data_area_4_offset:x}")
    else:
        print("\tData Area 4 : Does not exist")

        # Write the Telemetry Host-Initiated log page
    with open(args.telemetry, "wb") as f:
        f.write(header)
        f.write(data_area_1)
        f.write(data_area_2)
        f.write(data_area_3)
        f.write(data_area_4)
        f.close()

    # Write the OCP Strings log page (log identifier C9h)
    with open(args.string, "wb") as f:
        f.write(string_log["log"])
        f.close()

# main
