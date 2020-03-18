# -*- coding: utf-8 -*-
import re
import argparse

sch_part_re = re.compile(r"L (?:keyboard_parts:KEYSW|Device:D) (K_.*)")
sch_ref_re = re.compile(r"F 0 \"((?:K|D)_.*)\" (?:H|V)\s+\d+\s+\d+\s+\d+\s+\d+ (?:R|C) CNN")
pcb_net_re = re.compile(r"^\s*\((?:net \d+|add_net) \"Net-\(((?:K|D)_.*)-Pad\d+\)\"\)")
pcb_ref_re = re.compile(r"^\s*\(fp_text reference ((?:K|D)_.*) \(at [0-9\.\-]+ [0-9\.\-]+\s*[0-9\.\-]*\) \(layer [A-Z].*\)")

def get_new_name(name):
    """Generate a properly annotated component reference

    Takes a reference name generated from kbpcb and appends 
    a number on the end so that the annotator won't try to update it.

    Special cases:
     - Space key reference is presumably generated with a trailing space
       but it seems that kicad will strip it, so SPC is added
     - Unicode chars are used for arrow keys, these are replaced with 
       the words spelled out using ASCII chars
    """
    new_name = name + "_0"
    if name.endswith("_"):
        new_name = name + "SPC_0"
    new_name = new_name.replace("↑", "UP")
    new_name = new_name.replace("↓", "DOWN")
    new_name = new_name.replace("←", "LEFT")
    new_name = new_name.replace("→", "RIGHT")
    return new_name


def main(sch_name, sch_out_name, pcb_name, pcb_out_name):
    print(f"Reading {sch_name}")
    with open(sch_name, "r") as f:
        sch = f.readlines()

    with open(sch_out_name, "w") as f:
        for l in sch:
            part_match = sch_part_re.match(l)
            ref_match = sch_ref_re.match(l)
            match = None
            if part_match:
                # print("Part match found")
                match = part_match
            elif ref_match:
                # print("Reference match found")
                match = ref_match
            if not match:
                f.write(l)
                continue
            name = match.group(1)
            new_name = get_new_name(name)
            #print(f"Updating {name} to {new_name}")
            l = l.replace(name, new_name)
            f.write(l)
    print(f"Output written to {sch_out_name}")

    print(f"Reading {pcb_name}")
    with open(pcb_name, "r") as f:
        pcb = f.readlines()

    with open(pcb_out_name, "w") as f:
        for l in pcb:
            net_match = pcb_net_re.match(l)
            ref_match = pcb_ref_re.match(l)
            match = None
            if net_match:
                # print("Net match found")
                match = net_match
            elif ref_match:
                # print("Reference match found")
                match = ref_match
            if not match:
                f.write(l)
                continue
            name = match.group(1)
            # print(f"Updating {name} to {new_name}")
            new_name = get_new_name(name)
            l = l.replace(name, new_name)
            f.write(l)
    print(f"Output written to {pcb_out_name}")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Post process kbpcb outputs to prevent reannotation")
    parser.add_argument(
        "-i", "--input", 
        help="input filename with no extension (default: 'keyboard-layout')",
        default="keyboard-layout")
    parser.add_argument(
        "-o", "--output", 
        help="output filename with no extension (default: 'keyboard-layout-out')",
        default="keyboard-layout-out")
    args = parser.parse_args()
    if args.input == args.output:
        raise ValueError("Input and output filenames must be different")
    sch_name = args.input + ".sch"
    sch_out_name = args.output + ".sch"
    pcb_name = args.input + ".kicad_pcb"
    pcb_out_name = args.output + ".kicad_pcb"
    main(sch_name, sch_out_name, pcb_name, pcb_out_name)