import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Tuple, Union

import requests

_BASE_URL = "https://spliit.app/api/trpc"


class SplitMode(str, Enum):
    EVENLY = "EVENLY"
    BY_SHARES = "BY_SHARES"
    BY_PERCENTAGE = "BY_PERCENTAGE"
    BY_AMOUNT = "BY_AMOUNT"


def _current_timestamp() -> str:
    now = datetime.now(timezone.utc)
    return (
        now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    )


@dataclass
class SpliitClient:
    """
    Minimal client for Spliit's hosted instance (spliit.app), covering only
    the operations this tool needs: reading a Group's details and creating
    an Expense.

    Vendored locally rather than depending on the `spliit-api-client` PyPI
    package (see ADR 0002's amendment): every published version of that
    package is unusable for this project - 0.1.2 through 0.1.5 ship empty
    wheels with no code, and 0.1.0/0.1.1 crash on import under Python 3.9
    (this project's target interpreter) because they unconditionally do
    `from datetime import datetime, UTC`, and `datetime.UTC` only exists in
    Python 3.11+. This client mirrors the working parts of 0.1.1's
    `spliit.client.Spliit`, fixed to run on Python 3.9, against Spliit's
    undocumented tRPC endpoints directly.
    """

    group_id: str
    base_url: str = _BASE_URL

    def get_group(self) -> Dict:
        params_input = {
            "0": {"json": {"groupId": self.group_id}},
            "1": {"json": {"groupId": self.group_id}},
        }
        params = {"batch": "1", "input": json.dumps(params_input)}

        response = requests.get(
            f"{self.base_url}/groups.get,groups.getDetails", params=params
        )
        response.raise_for_status()
        return response.json()[0]["result"]["data"]["json"]["group"]

    def add_expense(
        self,
        title: str,
        paid_by: str,
        paid_for: Union[List[str], List[Tuple[str, int]]],
        amount: int,
        category: int = 0,
        notes: str = "",
        split_mode: SplitMode = SplitMode.EVENLY,
    ) -> str:
        paid_for_format = []
        if split_mode == SplitMode.EVENLY:
            for participant_id in paid_for:
                paid_for_format.append(
                    {"participant": participant_id, "shares": 1}
                )
        else:
            for participant_id, shares in paid_for:
                paid_for_format.append(
                    {"participant": participant_id, "shares": shares}
                )

        json_data = {
            "0": {
                "json": {
                    "groupId": self.group_id,
                    "expenseFormValues": {
                        "expenseDate": _current_timestamp(),
                        "title": title,
                        "category": category,
                        "amount": amount,
                        "paidBy": paid_by,
                        "paidFor": paid_for_format,
                        "splitMode": split_mode.value,
                        "saveDefaultSplittingOptions": False,
                        "isReimbursement": False,
                        "documents": [],
                        "notes": notes,
                    },
                    "participantId": "None",
                },
                "meta": {
                    "values": {
                        "expenseFormValues.expenseDate": ["Date"],
                    },
                },
            },
        }

        response = requests.post(
            f"{self.base_url}/groups.expenses.create",
            params={"batch": "1"},
            json=json_data,
        )
        response.raise_for_status()
        return response.content.decode()
