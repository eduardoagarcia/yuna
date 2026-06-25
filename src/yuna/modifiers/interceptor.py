"""Stat interceptor protocol for value rerouting."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from yuna.modifiers.context import ModifierContext
    from yuna.types.identifiers import EntityID


class StatInterceptor(Protocol):
    """Protocol for intercepting stat values before application.

    Games implement this to intercept final calculated values and reroute
    them to alternative destinations. Interceptors receive the final stacked
    value and can modify/redirect it before clamping and application.

    Common Patterns:
    - Shield absorption: Intercept health damage, apply to shield first
    - Battery pooling: Intercept battery drain, drain auxiliary pack first
    - Stat stealing: Intercept damage dealt, heal self by percentage
    - Overflow: Intercept healing, convert excess to temporary shield
    """

    def __call__(
        self,
        entity_id: EntityID,
        stat: str,
        value: float,
        context: ModifierContext,
    ) -> float:
        """Intercept final stat value before clamping/application.

        Args:
            entity_id: Entity being modified
            stat: Stat name being intercepted
            value: Final calculated value (post-stacking, pre-clamping)
            context: ModifierContext with world access for component reads/writes

        Returns:
            Modified value (can be same, nullified, amplified, or rerouted)
        """
        ...  # pragma: no cover
