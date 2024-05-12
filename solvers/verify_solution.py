import argparse
import json
from bap.instance import Instance


def check_solution(instance: str, solution: str) -> None:
    with open(solution) as f:
        s = json.load(f)
        s = s['ships']

    i = Instance(instance_file=instance)

    for s1 in s:
        idx1 = s1['data_ship_id']
        length1 = i.ship_length[idx1]
        proc1 = i.processing_time[idx1]
        earliest1 = i.arrival_time[idx1]
        mooring1 = s1['mooring_time']
        loc1 = s1['mooring_position']

        if mooring1 < earliest1:
            print(f"Ship {idx1}. Invalid berthing time {mooring1} < {earliest1} arrival time.")

        if loc1 > i.quay_length - length1:
            print(f"Ship {idx1}. Invalid berthing position {loc1} > {i.quay_length} (quay length) - {length1} (ship length).")

        for s2 in s:
            idx2 = s2['data_ship_id']

            if idx2 <= idx1:
                continue

            length2 = i.ship_length[idx2]
            proc2 = i.processing_time[idx2]
            mooring2 = s2['mooring_time']
            loc2 = s2['mooring_position']

            if (loc1 <= loc2 < loc1 + length1 and mooring1 <= mooring2 < mooring1 + proc1) or \
               (loc2 <= loc1 < loc2 + length2 and mooring2 <= mooring1 < mooring2 + proc2):
                print(f"Ships {idx1} and {idx2} overlap.")
                print(f"Ship {idx1}. Berthing time: {mooring1}, departure time: {mooring1 + proc1}.")
                print(f"Ship {idx1}. Berthing position: {loc1}, berthing end pos: {loc1 + length1}.")
                print(f"Ship {idx2}. Berthing time: {mooring2}, departure time: {mooring2 + proc2}.")
                print(f"Ship {idx2}. Berthing position: {loc2}, berthing end pos: {loc2 + length2}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='verify_solution',
        description='Verifies if a solution is feasible'
    )

    parser.add_argument(
        '-i', '--instance', action='store', help='Path to the instance file'
    )
    parser.add_argument(
        '-s', '--solution', action='store', help='Path to the solution file'
    )

    args = parser.parse_args()

    check_solution(args.instance, args.solution)