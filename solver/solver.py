from dataclasses import dataclass, field
import itertools as iter
import json
from pathlib import Path
from pprint import pp


@dataclass
class _Updater:
    solver: "Solver | None" = None

    def update(self) -> None:
        assert self.solver

        while True:
            self.solver.board.log.display_steps()
            data = input("Data: [p_idx n_idx value ...]: ")
            print()

            if not data:
                self.solver.display_board()
            else:
                break

        board = self.solver.board

        for p_idx, n_idx, value in iter.batched(data.split(" "), 3, strict=True):
            p_idx = int(p_idx)
            assert p_idx < len(board.poles)
            n_idx = int(n_idx)
            value = value.upper() if value != "X" else None

            pole = board.poles[p_idx]
            assert n_idx < len(pole.nuts)
            pole.nuts[n_idx].color = value


UPDATER = _Updater()


@dataclass
class Nut:
    _color: str | None
    required: bool = field(default=False, init=False, repr=False, hash=False)

    def __post_init__(self, *args, **kwargs):
        assert self._color is None or " " not in self._color

        if self._color == "X":
            self._color = None

    def get_id(self) -> str:
        return self._color or ""

    @property
    def color(self) -> str | None:
        while self.required and self._color is None:
            UPDATER.update()

        return self._color

    @color.setter
    def color(self, color: str | None) -> str | None:
        self._color = color
        return self.color

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False

        return bool(self.color and value.color and self.color == value.color)


@dataclass
class Pole:
    nuts: list[Nut]
    _index: int = field(init=False)

    def __post_init__(self, *args, **kwargs):
        self._mark_top_nut_as_required()

    def _mark_top_nut_as_required(self) -> None:
        if not self.is_empty():
            self.get_top_nut().required = True

    def get_id(self) -> str:
        return "_".join(n.get_id() for n in self.nuts)

    def is_empty(self) -> bool:
        return not self.nuts

    def count_colors(self) -> int:
        return len({n.color for n in self.nuts})

    def is_done(self) -> bool:
        return len(self.nuts) == 4 and self.count_colors() == 1

    def get_top_nut(self) -> Nut:
        assert not self.is_empty()

        return self.nuts[-1]

    def can_receive_payload(self, payload: list[Nut]) -> bool:
        assert Pole(payload).count_colors() == 1 and len(payload) <= 4

        return self.is_empty() or (
            len(self.nuts) + len(payload) <= 4 and self.get_top_nut() == payload[0]
        )

    def receive_payload(self, payload: list[Nut], force: bool = False) -> None:
        assert force or self.can_receive_payload(payload)

        for nut in payload:
            self.nuts.append(nut)

        self._mark_top_nut_as_required()

    def remove(self, payload: list[Nut]) -> None:
        assert payload == self.nuts[-len(payload) :]

        for _ in range(len(payload)):
            self.nuts.pop()

        self._mark_top_nut_as_required()

    def check_payload(self) -> list[Nut] | None:
        if self.is_empty() or self.is_done():
            return None

        nuts = []
        for n in reversed(self.nuts):
            if not nuts or n == nuts[-1]:
                nuts.append(n)

        return nuts

    def get_payload(self) -> list[Nut]:
        assert self.check_payload()

        nuts = []

        for n in reversed(self.nuts):
            if not nuts or n == nuts[-1]:
                nuts.append(self.nuts.pop())
            else:
                break

        self._mark_top_nut_as_required()

        return nuts

    @classmethod
    def create_from_raw_data(cls, data: list[str]) -> "Pole":
        return cls([Nut(color.upper()) for color in data])


@dataclass
class BoardMoveLogEntry:
    payload: list[Nut]
    source: Pole
    target: Pole


@dataclass
class BoardMoveLog:
    entries: list[BoardMoveLogEntry]

    def is_empty(self) -> bool:
        return not self.entries

    def add_entry(
        self, payload: list[Nut], source: Pole, target: Pole
    ) -> BoardMoveLogEntry:
        self.entries.append(ret := BoardMoveLogEntry(payload, source, target))
        return ret

    def pop_entry(self) -> BoardMoveLogEntry:
        assert self.entries
        return self.entries.pop()

    def display_steps(self) -> None:
        for entry in self.entries:
            print(
                f"Move[{entry.source._index} -> {entry.target._index}]",
                f"| Coords[{entry.source._index}][{len(entry.source.nuts)-1}]",
                f"| Pole<index={entry.source._index}, lvl={len(entry.source.nuts)-1}>",
                "->",
                f"Pole<index={entry.target._index}>",
            )


@dataclass
class Board:
    poles: list[Pole]
    log: BoardMoveLog = field(
        default=None, init=False, repr=False, hash=False
    )  # type: ignore # NOSONAR # will be populater in post_init

    def __post_init__(self, *args, **kwargs):
        self.log = BoardMoveLog([])
        for i, p in enumerate(self.poles):
            p._index = i

        assert isinstance(self.log, BoardMoveLog)

    def get_id(self) -> str:
        return "@".join(p.get_id() for p in self.poles)

    def is_solved(self) -> bool:
        return all(pole.is_empty() or pole.is_done() for pole in self.poles)

    # generator
    def generate_valid_moves(self):
        """
        Yields a tuple `(source_pole, target_pole)`
        """
        if self.is_solved():
            return

        for source_pole in self.poles:
            if checked_payload := source_pole.check_payload():
                for target_pole in self.poles:
                    if source_pole is target_pole:
                        continue

                    if target_pole.can_receive_payload(checked_payload):
                        move_has_value = not (
                            source_pole.count_colors() == 1 and target_pole.is_empty()
                        )

                        if move_has_value:
                            yield source_pole, target_pole

    def apply_move(self, source: Pole, target: Pole) -> None:
        payload = source.get_payload()

        target.receive_payload(payload)
        self.log.add_entry(payload, source, target)

    def reverse_move(self):
        last = self.log.pop_entry()

        last.target.remove(last.payload)
        last.source.receive_payload(last.payload, force=True)

    def to_raw_data(self):
        return [[nut._color or "X" for nut in pole.nuts] for pole in self.poles]

    @classmethod
    def create_from_json(cls, file_path: Path | str) -> "Board":
        with open(Path(file_path)) as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert all(isinstance(item, list) and len(item) <= 4 for item in data)

        return cls([Pole.create_from_raw_data(pole_raw) for pole_raw in data])


@dataclass
class Solver:
    board: Board

    def __post_init__(self, *args, **kwargs):
        assert UPDATER.solver is None
        UPDATER.solver = self

    def solve(self) -> BoardMoveLog | None:
        try:
            seen_states: set[str] = set()

            def layer():
                for source, target in self.board.generate_valid_moves():
                    self.board.apply_move(source, target)

                    if self.board.is_solved():
                        return

                    state = self.board.get_id()

                    if state not in seen_states:
                        seen_states.add(state)
                        layer()

                    if self.board.is_solved():
                        return

                    self.board.reverse_move()

            layer()
            return self.board.log if self.board.is_solved() else None
        except BaseException as err:
            try:
                while not self.board.log.is_empty():
                    self.board.reverse_move()

                with open(Path(__file__).parent / "_backup_.json", "w") as f:
                    json.dump(self.board.to_raw_data(), f)

            finally:
                raise err

    def display_board(self) -> None:
        pp(self.board)
