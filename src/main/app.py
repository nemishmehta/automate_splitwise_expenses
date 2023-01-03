import csv
from typing import Dict, List, Tuple, Union

import splitwise
from dotenv import dotenv_values
from splitwise import Splitwise
from splitwise.expense import Expense, ExpenseUser


class UploadExpense:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.config = dotenv_values(".env")
        self.consumer_key: str = self.config["CONSUMER_KEY"]
        self.consumer_secret: str = self.config["CONSUMER_SECRET"]
        self.api_key: str = self.config["API_KEY"]
        self.splitwise_obj = Splitwise(
            self.consumer_key,
            self.consumer_secret,
            api_key=self.api_key,
        )
        self.user_id: str = None
        self.user_friends: Dict[int, str] = dict()
        self.user_groups: Dict[int, str] = dict()
        self.user_groups_members: Dict[str, List[int]] = dict()
        self.categories: Dict[str, int] = dict()
        self.all_sub_categories: Dict[str, Dict[str, int]] = dict()
        self.expenses: List[Dict[str, str]] = list()

    def run_pipeline(self) -> None:
        """
        Method to run the entire pipeline.
        """

        (
            self.user_id,
            self.user_friends,
            self.user_groups,
            self.user_groups_members,
        ) = self.get_user_info()
        user_personal_expense_group_id: int = (
            self.choose_personal_expense_group()
        )
        (
            self.categories,
            self.all_sub_categories,
        ) = self.get_categories_and_sub_categories()

        self.expenses = self.get_csv_file_contents()

        print("\nExpense Upload")
        print(f"\nThere are in total {len(self.expenses)} expenses.")
        count: int = 0
        for expense in self.expenses:

            total_expense: float = round(float(expense["amount"]), 2)
            count += 1
            print(f"\nExpense {count}\n")
            for key, val in expense.items():
                print(f"{key}: {val}")

            confirm_data: str = None

            while confirm_data != "":
                expense_info: Dict[
                    str, Union[str, float, splitwise.category.Category, int]
                ] = self.collect_data(
                    user_personal_expense_group_id, total_expense
                )
                print("\n")
                for key, val in expense.items():
                    if (
                        key == "sub_category_obj"
                        or key == "group_id"
                        or key == "friend_id"
                    ):
                        continue
                    else:
                        print(f"{key}: {val}")
                for key, val in expense_info.items():
                    if (
                        key == "sub_category_obj"
                        or key == "group_id"
                        or key == "friend_id"
                    ):
                        continue
                    else:
                        print(f"{key}: {val}")
                confirm_data = input(
                    (
                        "\nPress Enter to confirm data or any other key to "
                        "re-enter data - "
                    )
                )
            if expense_info["group_id"] == user_personal_expense_group_id:
                self.upload_expense_personal_group(
                    expense, expense_info, total_expense
                )
            else:
                self.upload_expense_other_groups(
                    expense, expense_info, total_expense
                )

    def get_user_info(
        self,
    ) -> Tuple[int, Dict[int, str], Dict[int, str], Dict[int, List[int]]]:
        """
        Connect to splitwise and get user's id, friends, groups and groups
        members.

        Returns:
            Tuple[int, Dict[int, str], Dict[int, str], Dict[int, List[int]]]:
            user_id, friends, groups, groups_members
        """
        user_id: int = self.splitwise_obj.getCurrentUser().getId()

        friends: Dict[int, str] = dict()
        friends_obj = self.splitwise_obj.getFriends()
        for friend in friends_obj:
            friends[friend.getId()] = friend.getFirstName()

        groups: Dict[int, str] = dict()
        groups_obj = self.splitwise_obj.getGroups()
        groups_members: Dict[int, List[int]] = dict()
        for group in groups_obj:
            group_name = group.getName()
            group_id = group.getId()
            groups[group_id] = group_name

            group_members_obj = [
                member
                for member in self.splitwise_obj.getGroup(
                    group_id
                ).getMembers()
            ]
            groups_members[group_id] = [
                member.getId() for member in group_members_obj
            ]
        return user_id, friends, groups, groups_members

    def choose_personal_expense_group(self) -> int:
        """
        If applicable choose a group for personal expense

        Returns:
            int: Personal expenses group id if it exists.
        """
        user_input = input(
            (
                "\nPress Enter if you have a group to store personal expenses "
                "or press any other key if you don't have such a group - "
            )
        )

        if user_input == "":
            personal_expense_group_id: int = None

            while personal_expense_group_id not in self.user_groups.keys():
                print("\n")
                for index, group in enumerate(self.user_groups.values()):
                    print(f"{index} - {group}")

                try:
                    personal_group_index: int = input(
                        (
                            "\nHere are your groups. Enter the number "
                            "of the personal expense group - "
                        )
                    )
                    personal_expense_group_id: int = list(
                        self.user_groups.keys()
                    )[int(personal_group_index)]

                    if (
                        len(
                            self.user_groups_members[personal_expense_group_id]
                        )
                        == 1
                        and self.user_groups_members[
                            personal_expense_group_id
                        ][0]
                        == self.user_id
                    ):
                        return personal_expense_group_id
                    else:
                        personal_expense_group_id: int = None
                        print(
                            (
                                "\nThe chosen group contains more than one "
                                "person. Please a different group.\n"
                            )
                        )
                except ValueError:
                    print("\nPlease enter a valid number.")
                except IndexError:
                    print("\nPlease enter a value within the given list.")
        else:
            return None

    def get_categories_and_sub_categories(
        self,
    ) -> Tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
        """
        Returns a dictionary of available categories and their ids.

        Returns:
            Tuple[Dict[str, int], Dict[str, Dict[str, int]]]: Returns a
            dictionary of categories and their ids and a dictionary of
            sub-categories and their ids for each category.
        """
        categories: Dict[str, int] = dict()
        all_sub_categories: Dict[str, Dict[str, int]] = dict()
        categories_obj = self.splitwise_obj.getCategories()

        for category in categories_obj:
            category_name = category.getName()
            categories[category_name] = category.getId()

            sub_categories_obj = category.getSubcategories()
            sub_category_for_category: Dict[
                str, splitwise.category.Category
            ] = dict()
            for sub_category in sub_categories_obj:
                sub_category_for_category[
                    sub_category.getName()
                ] = sub_category

            all_sub_categories[category_name] = sub_category_for_category

        return categories, all_sub_categories

    def get_csv_file_contents(self) -> List[Dict[str, str]]:
        """
        Open csv file and save all expenses in a list of dictionaries.

        Returns:
            List[Dict[str, str]]: list of dictionaries containing all
            expenses.
        """
        with open(self.file_path, "r") as csv_file:
            csv_reader = csv.DictReader(csv_file, delimiter=";")
            all_expenses = [row for row in csv_reader]

        return all_expenses

    def collect_data(
        self, user_personal_expense_group_id: int, total_expense: float
    ) -> Dict[str, Union[str, float, splitwise.category.Category, int]]:
        """
        Method to upload expense on Splitwise.

        Args:
            user_personal_expense_group_id (int): group id for personal expense
            group
            total_expense (float): total expense amount
        Returns:
            Dict[
                str, Union[str, float, splitwise.category.Category, int]]:
                Dictionary containing data to create expense
        """
        # user_input_friends_count = input(
        #     (
        #         "\nPress Enter if you want to split the expenses with only "
        #         "one friend or press any other key if you want to "
        #         "split each expense with a different friend - "
        #     )
        # )

        # if user_input_friends_count == "":
        #     friend_name, friend_id = self.choose_friend()

        (
            sub_category_name,
            sub_category_obj,
        ) = self.choose_sub_category()

        group_name, group_id = self.choose_group(
            user_personal_expense_group_id
        )

        if group_id == user_personal_expense_group_id:
            expense_info = {
                "sub_category_name": sub_category_name,
                "sub_category_obj": sub_category_obj,
                "group_name": group_name,
                "group_id": group_id,
            }
            return expense_info
        else:
            friend_name, friend_id = self.choose_friend(group_id)
            chosen_split_type: str = self.choose_split_type()

            if chosen_split_type == "=":
                user_1_share, user_2_share = self.split_equally(total_expense)
            elif chosen_split_type == "|":
                (
                    user_1_share,
                    user_2_share,
                ) = self.split_by_exact_amount(total_expense)
            elif chosen_split_type == "%":
                user_1_share, user_2_share = self.split_by_percentage(
                    total_expense
                )
            expense_info = {
                "sub_category_name": sub_category_name,
                "sub_category_obj": sub_category_obj,
                "group_name": group_name,
                "group_id": group_id,
                "friend_name": friend_name,
                "friend_id": friend_id,
                "user_1_share": user_1_share,
                "user_2_share": user_2_share,
            }
            return expense_info

    def choose_friend(self, group_id: int) -> Tuple[str, int]:
        """
        Select a friend with whom you want to split the expense

        Args:
            group_name (str): Name of the chosen group
        Returns:
            str: chosen_friend_name
            int: chosen_friend_id
        """
        chosen_friend_id: int = None
        chosen_friend_name: str = None
        while chosen_friend_id is None or chosen_friend_name is None:
            for index, group_member_id in enumerate(
                self.user_groups_members[group_id]
            ):
                if group_member_id == self.user_id:
                    continue
                else:
                    chosen_friend_name = self.user_friends[group_member_id]
                    print(f"{index} - {chosen_friend_name}")

            try:
                friend_num_index = int(
                    input(
                        (
                            "\nHere are your friends in this group. Enter the "
                            "number of the friend with whom you want to "
                            "split the expense - "
                        )
                    )
                )
                chosen_friend_id = self.user_groups_members[group_id][
                    friend_num_index
                ]
                chosen_friend_name = self.user_friends[chosen_friend_id]

            except ValueError:
                print("\nPlease enter a valid number.")
            except IndexError:
                print("\nPlease enter a value within the given list.")
            except KeyError:
                print("\nPlease enter a value within the given list.")
        print(chosen_friend_name)
        return chosen_friend_name, chosen_friend_id

    def choose_group(
        self, user_personal_expense_group_id: int
    ) -> Tuple[str, int]:
        """
        Select the group under which the expense will be stored.

        Args:
            user_personal_expense_group_id (int): group id for personal expense
            group

        Returns:
            Tuple[str, int]: group name and group id
        """
        chosen_group_id: int = None

        while chosen_group_id is None:
            print("\n")
            for index, group in enumerate(self.user_groups.values()):
                print(f"{index} - {group}")

            try:
                chosen_group_index: int = int(
                    input(
                        (
                            "\nHere are your groups. "
                            "Enter the number of the group "
                            "under which you want to list the expense - "
                        )
                    )
                )
                if (
                    len(
                        list(self.user_groups_members.values())[
                            chosen_group_index
                        ]
                    )
                    == 1
                    and user_personal_expense_group_id is None
                ):
                    print(
                        (
                            "\nYou are the only member of this group. "
                            "Please choose another group."
                        )
                    )
                else:
                    chosen_group_name = list(self.user_groups.values())[
                        chosen_group_index
                    ]
                    chosen_group_id = list(self.user_groups.keys())[
                        chosen_group_index
                    ]
            except ValueError:
                print("\nPlease enter a valid number.")
            except IndexError:
                print("\nPlease enter a value within the given list.")

        return chosen_group_name, chosen_group_id

    def choose_sub_category(self) -> Tuple[str, splitwise.category.Category]:
        """
        Choose relevant sub-category from available and return their id

        Returns:
            Tuple[str, splitwise.category.Category]: sub-category name and
            sub-category object
        """
        chosen_category: str = self.choose_category()
        chosen_sub_category: str = ""
        sub_category_list: List[str] = [
            sub_category
            for sub_category in self.all_sub_categories[chosen_category]
        ]

        while chosen_sub_category not in sub_category_list:
            print("\n")
            for index, sub_category in enumerate(sub_category_list):
                print(f"{index} - {sub_category}")
            try:
                chosen_sub_category_index: int = int(
                    input(
                        (
                            "\nHere are the available sub-categories for this "
                            "category. Enter the number of the most relevant "
                            "sub-category. - "
                        )
                    )
                )
                chosen_sub_category = sub_category_list[
                    chosen_sub_category_index
                ]
            except ValueError:
                print("\nPlease enter a valid number.")
            except IndexError:
                print("\nPlease enter a value within the given list.")

        chosen_sub_category_obj = self.all_sub_categories[chosen_category][
            chosen_sub_category
        ]

        return chosen_sub_category, chosen_sub_category_obj

    def choose_category(self) -> str:
        """
        Choose relevant category from available and return their name

        Returns:
            str: category name
        """
        categories_list: List[str] = [
            category for category in self.categories.keys()
        ]
        category_name: str = ""

        while category_name not in categories_list:
            print("\n")
            for index, category in enumerate(categories_list):
                print(f"{index} - {category}")
            try:
                chosen_category_index: int = int(
                    input(
                        (
                            "\nHere are the available categories. Enter the "
                            "number of the most relevant category. - "
                        )
                    )
                )
                category_name = categories_list[chosen_category_index]
            except ValueError:
                print("\nPlease enter a valid number.")
            except IndexError:
                print("\nPlease enter a value within the given list.")

        return category_name

    def choose_split_type(self) -> str:
        """
        Choose between splitting equally, by exact amount or percentage.

        Returns:
            str: chosen split type (=, |, %)
        """
        possible_split_types: List[str] = ["=", "|", "%"]
        chosen_split_type: str = ""

        while chosen_split_type not in possible_split_types:
            chosen_split_type = input(
                (
                    "\nChoose one of the following options to split the "
                    "expense: (equally: =, exact amount: |, percentage: %) "
                    "- "
                )
            )
            if chosen_split_type not in possible_split_types:
                print("\nPlease choose between =, | and %")

        return chosen_split_type

    def split_equally(self, total_expense: float) -> Tuple[str, str]:
        """
        Split total expense amount equally between two users and return split
        amount.

        Args:
            total_expense (float): total expense amount

        Returns:
            Tuple[str, str]: user 1 and user 2 split
        """
        user_1_share = str(round(total_expense / 2, 2))
        user_2_share = str(round(total_expense / 2, 2))

        return user_1_share, user_2_share

    def split_by_exact_amount(self, total_expense: float) -> Tuple[str, str]:
        """
        Split total expense amount by exact amount between two users and
        return split amount.

        Args:
            total_expense (float): total expense amount

        Returns:
            Tuple[str, str]: user 1 and user 2 split
        """
        print(f"\nTotal expense amount = {total_expense}")
        user_2_share: float = 0
        while not 0 < user_2_share <= total_expense:
            try:
                user_2_share = round(
                    float(input("\nEnter the amount owed by your friend - ")),
                    2,
                )
                if not 0 < user_2_share <= total_expense:
                    print(f"\nEnter an amount between 0 and {total_expense}")
                user_1_share: float = round(total_expense - user_2_share, 2)

            except ValueError:
                print("\nPlease enter a valid number.")

        return str(user_1_share), str(user_2_share)

    def split_by_percentage(self, total_expense: float) -> Tuple[str, str]:
        """
        Split total expense amount by percentage between two users and
        return split amount.

        Args:
            total_expense (float): total expense amount

        Returns:
            Tuple[str, str]: user 1 and user 2 split
        """
        user_2_share_percent: float = 0
        while not 0 < user_2_share_percent <= 100:
            try:
                user_2_share_percent = round(
                    float(
                        input("\nEnter the percentage owed by your friend - ")
                    ),
                    2,
                )
                if not 0 < user_2_share_percent <= 100:
                    print("\nEnter a percentage between 0 and 100")
            except ValueError:
                print("\nPlease enter a valid percentage.")

        user_2_share: float = round(
            (total_expense * user_2_share_percent) / 100, 2
        )
        user_1_share: float = round(total_expense - user_2_share, 2)

        return str(user_1_share), str(user_2_share)

    def upload_expense_personal_group(
        self,
        expense: Dict[str, str],
        expense_info: Dict[
            str, Union[str, float, splitwise.category.Category, int]
        ],
        total_expense: float,
    ) -> None:
        """
        Upload expense to personal group.

        Args:
            expense (Dict[str, str]): dictionary containing date, amount,
            description and currency.
            expense_info (Dict[ str, Union[str, float,
            splitwise.category.Category, int] ]): dictionary containing
            sub-category name, object, group name & id, friend name & id, and
            their share.
            total_expense (float): total expense amount.
        """
        splitwise_expense = Expense()
        splitwise_expense.setCost(total_expense)
        splitwise_expense.setCategory(expense_info["sub_category_obj"])
        splitwise_expense.setDescription(expense["description"])
        splitwise_expense.setDate(expense["date"])
        splitwise_expense.setCurrencyCode(expense["currency"])
        splitwise_expense.setGroupId(expense_info["group_id"])
        user1 = ExpenseUser()
        user1.setId(self.user_id)
        user1.setPaidShare(total_expense)
        user1.setOwedShare(total_expense)
        splitwise_expense.addUser(user1)
        nExpense, errors = self.splitwise_obj.createExpense(splitwise_expense)
        if not errors:
            print("\nExpense successfully added to Splitwise.")
        else:
            print(errors.getErrors())

    def upload_expense_other_groups(
        self,
        expense: Dict[str, str],
        expense_info: Dict[
            str, Union[str, float, splitwise.category.Category, int]
        ],
        total_expense: float,
    ) -> None:
        """
        Upload expense to groups other than personal group.

        Args:
            expense (Dict[str, str]): dictionary containing date, amount,
            description and currency.
            expense_info (Dict[ str, Union[str, float,
            splitwise.category.Category, int] ]): dictionary containing
            sub-category name, object, group name & id, friend name & id, and
            their share.
            total_expense (float): total expense amount.
        """
        splitwise_expense = Expense()
        splitwise_expense.setCost(total_expense)
        splitwise_expense.setCategory(expense_info["sub_category_obj"])
        splitwise_expense.setDescription(expense["description"])
        splitwise_expense.setDate(expense["date"])
        splitwise_expense.setCurrencyCode(expense["currency"])
        splitwise_expense.setGroupId(expense_info["group_id"])
        user1 = ExpenseUser()
        user1.setId(self.user_id)
        user1.setPaidShare(total_expense)
        user1.setOwedShare(expense_info["user_1_share"])
        user2 = ExpenseUser()
        user2.setId(expense_info["friend_id"])
        user2.setPaidShare("0.0")
        user2.setOwedShare(expense_info["user_2_share"])
        splitwise_expense.addUser(user1)
        splitwise_expense.addUser(user2)
        nExpense, errors = self.splitwise_obj.createExpense(splitwise_expense)
        if not errors:
            print("\nExpense successfully added to Splitwise.")
        else:
            print(errors.getErrors())


test_class = UploadExpense("src/data/clean/test_data_raw_clean.csv")
test_class.run_pipeline()
