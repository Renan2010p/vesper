"""A small, dependency-free Entity-Component-System.

The design goal is clarity and moddability rather than raw performance:

* components are plain objects (usually dataclasses);
* an entity is just a bag of components plus tags;
* systems are ordered by ``priority`` and may implement ``update`` and/or
  ``draw``;
* everything is addressed by component *type*, so adding a new component or
  system never requires editing existing ones.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Iterator, List, Type, TypeVar

C = TypeVar("C")


class Component:
    """Base class for all components.  Optional but handy for isinstance."""

    __slots__ = ()


class Entity:
    __slots__ = ("id", "world", "components", "tags", "alive")

    def __init__(self, eid: int, world: "World") -> None:
        self.id = eid
        self.world = world
        self.components: Dict[type, Component] = {}
        self.tags: set = set()
        self.alive = True

    # -- components -------------------------------------------------------
    def add(self, *comps: Component) -> "Entity":
        for comp in comps:
            self.components[type(comp)] = comp
        return self

    def remove(self, *types: Type[Component]) -> "Entity":
        for t in types:
            self.components.pop(t, None)
        return self

    def get(self, cls: Type[C]) -> C | None:
        return self.components.get(cls)  # type: ignore[return-value]

    def has(self, *classes: Type[Component]) -> bool:
        comps = self.components
        return all(c in comps for c in classes)

    def one(self, *classes: Type[Component]) -> Component | None:
        for c in classes:
            comp = self.components.get(c)
            if comp is not None:
                return comp
        return None

    # -- tags -------------------------------------------------------------
    def tag(self, *names: str) -> "Entity":
        self.tags.update(names)
        return self

    def has_tag(self, name: str) -> bool:
        return name in self.tags

    def destroy(self) -> None:
        self.world.destroy(self)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        names = ",".join(sorted(c.__name__ for c in self.components))
        return f"<Entity {self.id} [{names}] #tags={sorted(self.tags)}>"


class System:
    """Base class for systems.  Override what you need."""

    priority: int = 0

    def start(self, world: "World") -> None:  # pragma: no cover - optional hook
        pass

    def update(self, world: "World", dt: float) -> None:
        pass

    def draw(self, world: "World", surface, camera) -> None:  # pragma: no cover
        pass


class World:
    """Owns entities, systems and shared services."""

    def __init__(self, events=None) -> None:
        self.entities: Dict[int, Entity] = {}
        self.services: Dict[str, Any] = {}
        self.systems: List[System] = []
        self._next_id = 1
        self._to_remove: List[int] = []
        self.events = events

    # -- entity lifecycle -------------------------------------------------
    def create(self, *comps: Component, tags: Iterable[str] = ()) -> Entity:
        ent = Entity(self._next_id, self)
        self._next_id += 1
        ent.tags.update(tags)
        ent.add(*comps)
        self.entities[ent.id] = ent
        return ent

    def destroy(self, ent: Entity) -> None:
        if ent.alive:
            self._to_remove.append(ent.id)

    def clear(self) -> None:
        self.entities.clear()
        self._to_remove.clear()
        self._next_id = 1

    def flush(self) -> None:
        for eid in self._to_remove:
            ent = self.entities.pop(eid, None)
            if ent is not None:
                ent.alive = False
        self._to_remove.clear()

    # -- queries ----------------------------------------------------------
    def query(self, *comps: Type[Component], tag: str | None = None) -> Iterator[Entity]:
        for ent in list(self.entities.values()):
            if not ent.alive:
                continue
            if tag is not None and tag not in ent.tags:
                continue
            if ent.has(*comps):
                yield ent

    def first(self, *comps: Type[Component], tag: str | None = None) -> Entity | None:
        for ent in self.query(*comps, tag=tag):
            return ent
        return None

    def by_tag(self, tag: str) -> List[Entity]:
        return [e for e in self.entities.values() if e.alive and tag in e.tags]

    # -- systems ----------------------------------------------------------
    def add_system(self, system: System) -> System:
        self.systems.append(system)
        self.systems.sort(key=lambda s: s.priority)
        return system

    def add_systems(self, *systems: System) -> None:
        for s in systems:
            self.add_system(s)

    def start(self) -> None:
        for system in self.systems:
            system.start(self)

    def update(self, dt: float) -> None:
        for system in self.systems:
            system.update(self, dt)
        self.flush()
        if self.events is not None:
            self.events.flush()

    def draw(self, surface, camera) -> None:
        for system in self.systems:
            system.draw(self, surface, camera)
