import argparse
from pathlib import Path

from src.spliit.backend import SpliitExpenseBackend
from src.spliit.who_am_i import WhoAmI

WHO_AM_I_PATH = Path(__file__).resolve().parents[2] / "who_am_i.json"

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "One-time-per-Group setup: record which Participant is you, "
            "so the tool knows whose Paid Share to fill in as the Payer."
        )
    )
    parser.add_argument("--group-id", required=True)
    args = parser.parse_args()

    backend = SpliitExpenseBackend(group_ids=[args.group_id])
    participants = backend.list_participants(args.group_id)

    if not participants:
        print(f"Group {args.group_id} has no Participants.")
    else:
        print("Participants:")
        for index, participant in enumerate(participants, start=1):
            print(f"  {index}. {participant.name}")

        choice = int(input("Which Participant are you? (number): "))
        chosen = participants[choice - 1]

        who_am_i = WhoAmI(WHO_AM_I_PATH)
        who_am_i.set(args.group_id, chosen.id)
        print(f"Saved: you are {chosen.name} in Group {args.group_id}.")
