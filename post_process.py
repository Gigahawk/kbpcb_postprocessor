# -*- coding: utf-8 -*-
import re
import argparse

sch_part_re = re.compile(r"L (?:keyboard_parts:KEYSW|Device:D) (K_.*)")
sch_ref_re = re.compile(r"F 0 \"((?:K|D)_.*)\" (?:H|V)\s+(\d+)\s+(\d+)\s+\d+\s+\d+ (?:R|C) CNN")
sch_keysw_re = re.compile(r"F\s+2\s+\"(MX_Alps_Hybrid:MX-[0-9\.]+U(?:-NoLED|))\"\s+H\s+\d+\s+\d+\s+\d+\s+\d+\s+C\s+CNN")
sch_pos_re = re.compile(r"P\s+(\d+)\s+(\d+)")
pcb_net_re = re.compile(r"^\s*\((?:net \d+|add_net) \"Net-\(((?:K|D)_.*)-Pad\d+\)\"\)")
pcb_ref_re = re.compile(r"^\s*\(fp_text reference ((?:K|D)_.*) \(at [0-9\.\-]+ [0-9\.\-]+\s*[0-9\.\-]*\) \(layer [A-Z].*\)")
LED_OFFSET = 0

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

def get_new_keysw(keysw, led):
    if led:
        keysw = keysw.replace("-NoLED", "")
    return keysw

def get_led_comp(name, keysw, posx, posy):
    led_comp = f"""$Comp
L keyboard_parts:KEYSW {name}
U 2 1 5E751ADB
P {posx} {posy}
F 0 "{name}" H {posx} {posy + 131} 60  0000 C CNN
F 1 "KEYSW" H {posx} {posy - 150} 60  0001 C CNN
F 2 "{keysw}" H {posx} {posy} 60  0001 C CNN
F 3 "" H {posx} {posy} 60  0000 C CNN
	2    {posx} {posy}
	0    -1    -1    0
$EndComp
"""
    return led_comp

def process_component(comp, led, led_sym, led_sym_offset=1000):
    part_match = sch_part_re.search(comp)
    ref_match = sch_ref_re.search(comp)
    keysw_match = sch_keysw_re.search(comp)
    posx, posy = get_component_pos(comp)

    part_ref = part_match.group(1)
    ref = ref_match.group(1)
    part_ref_line = part_match.group(0)
    ref_line = ref_match.group(0)
    keysw = keysw_match.group(1) if keysw_match else None

    new_part_ref = get_new_name(part_ref)
    new_ref = get_new_name(ref)
    new_part_ref_line = part_ref_line.replace(part_ref, new_part_ref)
    new_ref_line = ref_line.replace(ref, new_ref)
    if keysw:
        new_keysw = get_new_keysw(keysw, led)
    
    comp = comp.replace(part_ref_line, new_part_ref_line)
    comp = comp.replace(ref_line, new_ref_line)
    if keysw:
        comp = comp.replace(keysw, new_keysw)
    
    if led_sym and keysw:
        led_comp = get_led_comp(new_ref, new_keysw, posx, posy + led_sym_offset)
        comp += "\n" + led_comp
    return comp

def get_component_pos(comp):
    pos_match = sch_pos_re.search(comp)
    posx = int(pos_match.group(1))
    posy = int(pos_match.group(2))

    return posx, posy

def get_comp_indices(sch):
    starts = []
    ends = []
    for idx, l in enumerate(sch):
        if l.startswith("$Comp"):
            starts.append(idx)
        elif l.startswith("$EndComp"):
            ends.append(idx)
    return list(zip(starts, ends))

def update_sch(sch, comp_idxs, led, led_sym):
    max_posy = float("-inf")
    for start, end in comp_idxs:
        comp = "\n".join(sch[start:end+1])
        _, posy = get_component_pos(comp)
        if posy > max_posy:
            max_posy = posy


    edits = []
    led_sym_offset = max_posy + LED_OFFSET
    for start, end in comp_idxs:
        comp = "".join(sch[start:end+1])
        comp = process_component(
            comp, led, led_sym, led_sym_offset).splitlines(keepends=True)
        edits.append((start, end, comp))
    
    # Sort so that largest line number is first
    edits = sorted(edits, key=lambda x: -x[0])

    for start, end, comp in edits:
        del sch[start:end+1]
        sch[start:start] = comp
    return sch

def main(sch_name, sch_out_name, pcb_name, pcb_out_name, led, led_sym):
    print(f"Reading {sch_name}")
    with open(sch_name, "r") as f:
        sch = f.readlines()

    comp_idxs = get_comp_indices(sch)
    sch = update_sch(sch, comp_idxs, led, led_sym)

    with open(sch_out_name, "w") as f:
        f.writelines(sch)
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
    parser.add_argument(
        "--led", help="Use footprint with LED pads",
        action="store_true")
    parser.add_argument(
        "--led_sym", 
        help=(
            "Add LED symbols to schematic "
            "(Requires custom kicad_lib_tmk, see "
            "https://github.com/Gigahawk/kicad_lib_tmk)"),
        action="store_true")
    args = parser.parse_args()
    if args.input == args.output:
        raise ValueError("Input and output filenames must be different")
    sch_name = args.input + ".sch"
    sch_out_name = args.output + ".sch"
    pcb_name = args.input + ".kicad_pcb"
    pcb_out_name = args.output + ".kicad_pcb"
    led = args.led
    led_sym = args.led_sym
    main(sch_name, sch_out_name, pcb_name, pcb_out_name, led, led_sym)