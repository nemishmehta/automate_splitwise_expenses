import csv
from typing import Dict, List, Tuple

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
        self.user_friends: Dict[str, str] = dict()
        self.user_groups: Dict[str, str] = dict()
        self.user_groups_members: Dict[str, List[str]] = dict()
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
        (
            self.categories,
            self.all_sub_categories,
        ) = self.get_categories_and_sub_categories()

        self.expenses = self.get_csv_file_contents()
        self.upload_expenses()

    def get_user_info(
        self,
    ) -> Tuple[int, Dict[str, int], Dict[str, int], Dict[str, List[str]]]:
        """
        Connect to splitwise and get user's id, friends, groups and groups
        members.

        Returns:
            Tuple[int, Dict[str, int], Dict[str, int], Dict[str, List[str]]]:
            user_id, friends, groups, groups_members
        """
        user_id: int = self.splitwise_obj.getCurrentUser().getId()

        friends: Dict[str, int] = dict()
        friends_obj = self.splitwise_obj.getFriends()
        for friend in friends_obj:
            friends[friend.getFirstName()] = friend.getId()

        groups: Dict[str, int] = dict()
        groups_obj = self.splitwise_obj.getGroups()
        groups_members: Dict[str, str] = dict()
        for group in groups_obj:
            group_name = group.getName()
            group_id = group.getId()
            groups[group_name] = group_id

            group_members_obj = [
                member
                for member in self.splitwise_obj.getGroup(
                    group_id
                ).getMembers()
            ]
            groups_members[group_name] = [
                member.getFirstName() for member in group_members_obj
            ]

        return user_id, friends, groups, groups_members

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

    def upload_expenses(self) -> None:

        print("Expense Upload\n")
        print(f"There are in total {len(self.expenses)} expenses.\n")
        user_input = input(
            (
                "Press Enter if you want to do a bulk upload or "
                "press any other key if you want to review each expense - "
            )
        )

        if user_input == "":
            self.bulk_upload_expenses()
        else:
            self.upload_one_expense_at_a_time()

    def bulk_upload_expenses(self) -> None:
        # To do!
        print(
            (
                "To bulk upload expenses, we need to choose friend, group, and"
                " the splitting % between "
            )
        )

    def upload_one_expense_at_a_time(self) -> None:

        user_input_friends_count = input(
            (
                "\nPress Enter if you want to split the expenses with only one"
                " friend or press any other key if you want to "
                "split each expense with a different friend - "
            )
        )

        if user_input_friends_count == "":
            friend_name, friend_id = self.choose_friend()

        for expense in self.expenses:
            confirm_data: str = " "
            while confirm_data != "":
                date: str = expense["date"]
                total_expense: float = round(float(expense["amount"]), 2)
                description: str = expense["description"]
                currency: str = expense["currency"]
                print(
                    (
                        f"\nDate: {date}\nTotal Expense: {total_expense}"
                        f"\nDescription: {description}\nCurrency: {currency}"
                    )
                )
                if user_input_friends_count != "":
                    friend_name, friend_id = self.choose_friend()

                group_name, group_id = self.choose_group(friend_name)
                (
                    sub_category_name,
                    sub_category_obj,
                ) = self.choose_sub_category()

                chosen_split_type: str = self.choose_split_type()

                if chosen_split_type == "=":
                    user_1_share, user_2_share = self.split_equally(
                        total_expense
                    )
                elif chosen_split_type == "|":
                    user_1_share, user_2_share = self.split_by_exact_amount(
                        total_expense
                    )
                elif chosen_split_type == "%":
                    user_1_share, user_2_share = self.split_by_percentage(
                        total_expense
                    )

                print(
                    (
                        f"\nDate: {date}\nTotal Expense: {total_expense}"
                        f"\nDescription: {description}\nCurrency: {currency}"
                        f"\nGroup: {group_name}\nCategory: {sub_category_name}"
                        f"\nYour Share: {user_1_share}\n{friend_name}'s Share:"
                        f" {user_2_share}"
                    )
                )
                confirm_data = input(
                    (
                        "\nPress Enter to confirm data or any other key to "
                        "re-enter data - "
                    )
                )

            expense = Expense()
            expense.setCost(total_expense)
            expense.setCategory(sub_category_obj)
            expense.setDescription(description)
            expense.setDate(date)
            expense.setCurrencyCode(currency)
            expense.setGroupId(group_id)
            user1 = ExpenseUser()
            user1.setId(self.user_id)
            user1.setPaidShare(total_expense)
            user1.setOwedShare(user_1_share)
            user2 = ExpenseUser()
            user2.setId(friend_id)
            user2.setPaidShare("0.0")
            user2.setOwedShare(user_2_share)
            expense.addUser(user1)
            expense.addUser(user2)
            nExpense, errors = self.splitwise_obj.createExpense(expense)
            if not errors:
                print("\nExpense successfully added to Splitwise.")

    def choose_friend(self) -> Tuple[str, int]:
        """
        Select a friend with whom you want to split the expense

        Returns:
            str: friend_name
            int: friend_id
        """
        friend_id = ""

        while friend_id == "":
            friend_num_map: Dict[str, str] = dict()
            print("\n")
            for index, friend in enumerate(self.user_friends):
                friend_num_map[index] = friend
                print(f"{index} - {friend}")

            try:
                friend_num_index = int(
                    input(
                        (
                            "\nHere are your friends. Enter the number "
                            "of the friend with whom you want to "
                            "split the expense - "
                        )
                    )
                )
                friend_id: int = self.user_friends[
                    friend_num_map[friend_num_index]
                ]
                friend_name: str = friend_num_map[friend_num_index]
            except ValueError:
                print("\nPlease enter a valid number.")
            except KeyError:
                print("\nPlease enter a value within the given list.")

        return friend_name, friend_id

    def choose_group(self, friend_name: str) -> Tuple[str, int]:
        """
        Select the group under which the expense will be stored.

        Returns:
            Tuple[str, int]: group name and group id
        """
        common_groups: List[str] = list()
        for group in self.user_groups_members:
            if friend_name in self.user_groups_members[group]:
                common_groups.append(group)

        chosen_group: str = ""
        print("\n")
        while chosen_group not in common_groups:
            for index, group in enumerate(common_groups):
                print(f"{index} - {group}")

            try:
                chosen_group_index: int = int(
                    input(
                        (
                            "\nHere are your common groups. "
                            "Enter the number of the group "
                            "under which you want to list the expense - "
                        )
                    )
                )
                chosen_group = common_groups[chosen_group_index]
                group_id = self.user_groups[chosen_group]
            except ValueError:
                print("\nPlease enter a valid number.")
            except IndexError:
                print("\nPlease enter a value within the given list.")

        return chosen_group, group_id

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
        while not 0 < user_2_share < total_expense:
            try:
                user_2_share = round(
                    float(input("\nEnter the amount owed by your friend - ")),
                    2,
                )
                if not 0 < user_2_share < total_expense:
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
        while not 0 < user_2_share_percent < 100:
            try:
                user_2_share_percent = round(
                    float(
                        input("\nEnter the percentage owed by your friend - ")
                    ),
                    2,
                )
                if not 0 < user_2_share_percent < 100:
                    print("\nEnter a percentage between 0 and 100")
            except ValueError:
                print("\nPlease enter a valid percentage.")

        user_2_share: float = round(
            (total_expense * user_2_share_percent) / 100, 2
        )
        user_1_share: float = round(total_expense - user_2_share, 2)

        return str(user_1_share), str(user_2_share)


test_class = UploadExpense("src/data/clean/test_data_raw_clean.csv")
test_class.run_pipeline()
