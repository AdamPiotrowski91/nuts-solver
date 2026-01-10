from dataclasses import dataclass
import json
from pathlib import Path
from pprint import pp


@dataclass
class Nut:
    color: str | None

    def is_unknown(self) -> bool:
        return self.color is None

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False

        return bool(self.color and value.color and self.color == value.color)


@dataclass
class Pole:
    nuts: list[Nut]

    def is_empty(self) -> bool:
        return not self.nuts

    def count_colors(self) -> int:
        return len({n.color for n in self.nuts})

    def is_done(self) -> bool:
        return len(self.nuts) == 4 and self.count_colors() == 1

    def get_top_nut(self) -> Nut:
        assert not self.is_empty()

        return self.nuts[-1]

    def can_receive(self, payload: list[Nut]) -> bool:
        assert Pole(payload).count_colors() == 1

        return self.is_empty() or self.get_top_nut() == payload[0]

    def receive(self, payload: list[Nut], force: bool = False) -> None:
        assert force or self.can_receive(payload)

        self.nuts += payload

    def remove(self, payload: list[Nut]) -> None:
        assert payload == self.nuts[-len(payload) :]

        self.nuts = self.nuts[: 4 - len(payload)]

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

    def add_entry(
        self, payload: list[Nut], source: Pole, target: Pole
    ) -> BoardMoveLogEntry:
        self.entries.append(ret := BoardMoveLogEntry(payload, source, target))
        return ret

    def reverse(self):
        assert self.entries

        last = self.entries.pop()
        last.target.remove(last.payload)
        last.source.receive(last.payload, force=True)


@dataclass
class Board:
    poles: list[Pole]
    log: BoardMoveLog = None  # type: ignore # NOSONAR

    def __post_init__(self, *args, **kwargs):
        if not self.log:
            self.log = BoardMoveLog([])

    # generator
    def generate_valid_moves(self):
        for source_pole in self.poles:
            if checked := source_pole.check_payload():
                for target_pole in self.poles:
                    if source_pole is target_pole:
                        continue

                    if target_pole.can_receive(checked):
                        payload = source_pole.get_payload()
                        target_pole.receive(payload)
                        yield self.log.add_entry(payload, source_pole, target_pole)

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

    def display_board(self) -> None:
        pp(self.board)
