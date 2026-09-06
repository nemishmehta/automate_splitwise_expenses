This project is an implementation of uploading expenses on Splitwise. It is a CLI utility. It uses Splitwise's API key to identify all groups I have created on Splitwise and upload expenses to one of them. The expenses can be split equally, per exact amount, per percentage.

Here are the things that are currently under need for improvement:
1. Splitwise has introduced pricing for its API. So, I would like to migrate away to an open-source expense app.
2. In the current code implementation, expenses can only be split between two people. I would like to change that and allow the expenses to be split between more people.
3. A lot of the times I use percentages to split the expense between me and one other person. Currently, I need to provide the percentage for each expense even though the percentage split is the same. I would like to have an approach where a default could be set at the start of the session and used for the expenses that follow. You can come up with better approaches as well.
4. The current tool is fully CLI based. I would also like to have an option to use a UI that does something similar.
5. I am also curious to understand what other optimizations can be implemented in this project.