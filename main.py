from datetime import datetime
from abc import ABC, abstractmethod


class Commit:
    def __init__(self, name: str, description: str, files_list: list[str]):
        self.name = name
        self.description = description
        self.created_at = datetime.now()
        self.files_list = files_list

    def get_name(self) -> str:
        return self.name

    def get_description(self) -> str:
        return self.description

    def get_created_at(self) -> datetime:
        return self.created_at

    def get_files_list(self) -> list[str]:
        return self.files_list

    def __str__(self):
        return f"Commit: {self.name}, Description: {self.description}, Created at: {self.created_at}"


class Branch(ABC):
    @abstractmethod
    def clone(self, last_commit: Commit = None) -> 'Branch':
        pass

    @abstractmethod
    def __str__(self):
        '''
        Dunder-метод для строчного представления объекта. Выведите красиво историю коммитов в ветке.
        P.S. Было неудобно работать с кастомным linked list внутри for, неправда ли? Так вот, переопределяя подобные методы можно упрощать себе жизнь, поговорим об этом позже.
        '''
        pass

    @abstractmethod
    def add_commit(self, name: str, description: str, file_list: list[str]):
        pass

    @abstractmethod
    def join(self, where_to_move_commits: 'Branch'):
        '''
        Производит слияние двух веток, если нет конфликтов (т.е. изменений одних и тех же файлов в разных коммитах)
        Коммиты не объединяются, а переносятся в хронологическом порядке в ветку where_to_move_commits.
        Если невозможно объединить - NotJoinableBranchesError
        '''
        pass

    @abstractmethod
    def undo(self):
        '''
        Отменяет последние действия.
        Добавили коммит №1, Добавили коммит №2. Выполнили undo(), коммит №2 из ветки пропал.
        '''
        pass

    @abstractmethod
    def redo(self):
        '''
        Откатывает отмененные действия.
        Добавили коммит №1, Добавили коммит №2. Выполнили undo(), коммит №2 из ветки пропал. Выполнили redo() - появился коммит №2
        Добавили коммит №1, Добавили коммит №2. Выполнили undo(). Добавили коммит №3. Выполнили redo() - ничего не изменилось
        '''
        pass

    @abstractmethod
    def get_commits_list(self) -> list[Commit]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class ConcreteBranch(Branch):
    def __init__(self, name: str):
        self.name = name
        self.commits = []
        self.undo_history = []  # История операций для undo
        self.redo_history = []  # История операций для redo

    def clone(self, last_commit: Commit = None) -> Branch:
        cloned_branch = ConcreteBranch(self.name)
        if last_commit:
            cloned_branch.commits = self.commits[:self.commits.index(last_commit) + 1]
        else:
            cloned_branch.commits = self.commits[:]
        return cloned_branch

    def __str__(self):
        output = f"Branch: {self.name}\n"
        for commit in self.commits:
            output += str(commit) + "\n"
        return output

    def add_commit(self, name: str, description: str, file_list: list[str]):
        new_commit = Commit(name, description, file_list)
        self.commits.append(new_commit)
        self.undo_history.append(("add_commit", new_commit))  # Добавляем операцию в историю для undo

    def join(self, where_to_move_commits: Branch):
        for commit in self.commits:
            where_to_move_commits.add_commit(commit.name, commit.description, commit.file_list)

    def undo(self):
        if self.undo_history:
            last_operation = self.undo_history.pop()
            operation_name = last_operation[0]
            if operation_name == "add_commit":
                commit = last_operation[1]
                self.commits.remove(commit)
                self.redo_history.append(("add_commit", commit))  # Добавляем операцию в историю для redo

    def redo(self):
        if self.redo_history:
            last_operation = self.redo_history.pop()
            operation_name = last_operation[0]
            if operation_name == "add_commit":
                commit = last_operation[1]
                self.commits.append(commit)
                self.undo_history.append(("add_commit", commit))  # Добавляем операцию в историю для undo

    def get_commits_list(self) -> list[Commit]:
        return self.commits

    def get_name(self) -> str:
        return self.name


class Repository(ABC):
    @abstractmethod
    def create_branch(self, new_branch_name: str, base_branch_name: str = None, last_commit: Commit = None):
        pass

    @abstractmethod
    def remove_branch(self, name: str):
        pass

    @abstractmethod
    def clone_branch(self, name: str, new_name: str, last_commit: Commit = None):
        pass

    @abstractmethod
    def add_branch(self, new_branch: Branch):
        pass

    @abstractmethod
    def get_branch_list(self) -> list[Branch]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def undo(self):
        '''
        Отменяет последние действия.
        Добавили ветку №1, Добавили ветку №2. Выполнили undo(), ветка №2 пропала.
        '''
        pass

    @abstractmethod
    def redo(self):
        '''
        Откатывает отмененные действия.
        Добавили ветку №1, Добавили ветку №2. Выполнили undo(), ветка №2 пропала. Выполнили redo() - появилась ветка №2
        Добавили ветку №1, Добавили ветку №2. Выполнили undo(). Добавили ветку №3. Выполнили redo() - ничего не изменилось
        '''
        pass


class ConcreteRepository(Repository):
    def __init__(self, name: str):
        self.name = name
        self.branches = {}
        self.history = []
        self.redo_history = []

    def create_branch(self, new_branch_name: str, base_branch_name: str = None, last_commit: Commit = None):
        if base_branch_name:
            base_branch = self.branches.get(base_branch_name)
            if base_branch:
                cloned_branch = base_branch.clone(last_commit)
                cloned_branch.name = new_branch_name
                self.branches[new_branch_name] = cloned_branch
                self.history.append(("create_branch", new_branch_name))
        else:
            new_branch = ConcreteBranch(new_branch_name)
            self.branches[new_branch_name] = new_branch
            self.history.append(("create_branch", new_branch_name))

    def remove_branch(self, name: str):
        if name in self.branches:
            del self.branches[name]
            self.history.append(("remove_branch", name))

    def clone_branch(self, name: str, new_name: str, last_commit: Commit = None):
        if name in self.branches:
            cloned_branch = self.branches[name].clone(last_commit)
            cloned_branch.name = new_name
            self.branches[new_name] = cloned_branch
            self.history.append(("clone_branch", name, new_name))

    def add_branch(self, new_branch: Branch):
        self.branches[new_branch.name] = new_branch
        self.history.append(("add_branch", new_branch.name))

    def get_branch_list(self) -> list[Branch]:
        return list(self.branches.values())

    def get_name(self) -> str:
        return self.name

    def undo(self):
        if self.history:
            last_operation = self.history.pop()
            operation_name = last_operation[0]
            if operation_name == "remove_branch":
                branch_name = last_operation[1]
                del self.branches[branch_name]
                self.redo_history.append(last_operation)
            elif operation_name == "clone_branch":
                _, cloned_branch_name, _ = last_operation

                del self.branches[cloned_branch_name]
                self.redo_history.append(last_operation)
            elif operation_name == "add_branch":
                branch_name = last_operation[1]
                del self.branches[branch_name]
                self.redo_history.append(last_operation)

    def redo(self):
        if self.redo_history:
            last_operation = self.redo_history.pop()
            operation_name = last_operation[0]
            if operation_name == "remove_branch":
                branch_name = last_operation[1]
                del self.branches[branch_name]
                self.history.append(last_operation)
            elif operation_name == "clone_branch":
                _, _, cloned_branch_name = last_operation
                self.history.append(last_operation)
            elif operation_name == "add_branch":
                branch_name = last_operation[1]
                self.branches[branch_name] = last_operation[2]
                self.history.append(last_operation)
