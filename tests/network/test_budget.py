"""Tests for bandwidth budget management."""

from faker import Faker

from yuna.network.budget import BandwidthBudget, BudgetUsage
from yuna.types.identifiers import EntityID

fake = Faker()


def test_budget_usage_dataclass() -> None:
    """Test BudgetUsage dataclass."""
    usage = BudgetUsage(
        bytes_used=500,
        bytes_budget=1000,
        bytes_remaining=500,
        is_over_budget=False,
        overage=0,
    )
    assert usage.bytes_used == 500
    assert usage.bytes_budget == 1000
    assert usage.bytes_remaining == 500
    assert usage.is_over_budget is False
    assert usage.overage == 0


def test_bandwidth_budget_init() -> None:
    """Test BandwidthBudget initializes correctly."""
    hard_limit = fake.pyint(min_value=1000, max_value=10000)
    soft_limit = fake.pyint(min_value=500, max_value=hard_limit)

    budget = BandwidthBudget(hard_limit=hard_limit, soft_limit=soft_limit)

    assert budget.hard_limit == hard_limit
    assert budget.soft_limit == soft_limit


def test_bandwidth_budget_init_defaults_soft_limit() -> None:
    """Test BandwidthBudget defaults soft_limit to hard_limit."""
    hard_limit = fake.pyint(min_value=1000, max_value=10000)
    budget = BandwidthBudget(hard_limit=hard_limit)

    assert budget.hard_limit == hard_limit
    assert budget.soft_limit == hard_limit


def test_allocate_budget() -> None:
    """Test allocate_budget sets up observer budget."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)

    assert budget.get_remaining(observer_id=observer_id) == 1000


def test_can_afford_with_budget() -> None:
    """Test can_afford returns True when budget available."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)

    assert budget.can_afford(observer_id=observer_id, bytes_needed=500) is True


def test_can_afford_exceeds_budget() -> None:
    """Test can_afford returns False when exceeds budget."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)

    assert budget.can_afford(observer_id=observer_id, bytes_needed=1500) is False


def test_can_afford_exact_budget() -> None:
    """Test can_afford returns True when exactly at budget."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)

    assert budget.can_afford(observer_id=observer_id, bytes_needed=1000) is True


def test_can_afford_no_allocation() -> None:
    """Test can_afford returns False when observer not allocated."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    assert budget.can_afford(observer_id=observer_id, bytes_needed=100) is False


def test_spend_budget() -> None:
    """Test spend reduces available budget."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=300)

    assert budget.get_remaining(observer_id=observer_id) == 700


def test_spend_multiple_times() -> None:
    """Test spend accumulates correctly."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=200)
    budget.spend(observer_id=observer_id, bytes_spent=300)

    assert budget.get_remaining(observer_id=observer_id) == 500


def test_spend_without_allocation() -> None:
    """Test spend works without allocation."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.spend(observer_id=observer_id, bytes_spent=100)

    usage = budget.get_usage(observer_id=observer_id)
    assert usage.bytes_used == 100
    assert usage.bytes_budget == 0


def test_get_remaining_with_budget() -> None:
    """Test get_remaining returns correct value."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=400)

    assert budget.get_remaining(observer_id=observer_id) == 600


def test_get_remaining_over_budget() -> None:
    """Test get_remaining returns zero when over budget."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=1200)

    assert budget.get_remaining(observer_id=observer_id) == 0


def test_get_remaining_no_allocation() -> None:
    """Test get_remaining returns zero when not allocated."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    assert budget.get_remaining(observer_id=observer_id) == 0


def test_get_usage_under_budget() -> None:
    """Test get_usage returns correct statistics under budget."""
    budget = BandwidthBudget(hard_limit=1000, soft_limit=800)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=600)

    usage = budget.get_usage(observer_id=observer_id)

    assert usage.bytes_used == 600
    assert usage.bytes_budget == 1000
    assert usage.bytes_remaining == 400
    assert usage.is_over_budget is False
    assert usage.overage == 0


def test_get_usage_over_budget() -> None:
    """Test get_usage returns correct statistics over budget."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=1200)

    usage = budget.get_usage(observer_id=observer_id)

    assert usage.bytes_used == 1200
    assert usage.bytes_budget == 1000
    assert usage.bytes_remaining == 0
    assert usage.is_over_budget is True
    assert usage.overage == 200


def test_get_usage_exact_budget() -> None:
    """Test get_usage at exact budget limit."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=1000)

    usage = budget.get_usage(observer_id=observer_id)

    assert usage.bytes_used == 1000
    assert usage.bytes_budget == 1000
    assert usage.bytes_remaining == 0
    assert usage.is_over_budget is False
    assert usage.overage == 0


def test_get_usage_no_allocation() -> None:
    """Test get_usage with no allocation."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    usage = budget.get_usage(observer_id=observer_id)

    assert usage.bytes_used == 0
    assert usage.bytes_budget == 0
    assert usage.bytes_remaining == 0
    assert usage.is_over_budget is False
    assert usage.overage == 0


def test_is_over_soft_limit_under() -> None:
    """Test is_over_soft_limit returns False under limit."""
    budget = BandwidthBudget(hard_limit=1000, soft_limit=800)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=600)

    assert budget.is_over_soft_limit(observer_id=observer_id) is False


def test_is_over_soft_limit_over() -> None:
    """Test is_over_soft_limit returns True over limit."""
    budget = BandwidthBudget(hard_limit=1000, soft_limit=800)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=900)

    assert budget.is_over_soft_limit(observer_id=observer_id) is True


def test_is_over_soft_limit_exact() -> None:
    """Test is_over_soft_limit at exact limit."""
    budget = BandwidthBudget(hard_limit=1000, soft_limit=800)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=800)

    assert budget.is_over_soft_limit(observer_id=observer_id) is False


def test_is_over_hard_limit_under() -> None:
    """Test is_over_hard_limit returns False under limit."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=800)

    assert budget.is_over_hard_limit(observer_id=observer_id) is False


def test_is_over_hard_limit_over() -> None:
    """Test is_over_hard_limit returns True over limit."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=1200)

    assert budget.is_over_hard_limit(observer_id=observer_id) is True


def test_is_over_hard_limit_exact() -> None:
    """Test is_over_hard_limit at exact limit."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=1000)

    assert budget.is_over_hard_limit(observer_id=observer_id) is False


def test_reset() -> None:
    """Test reset clears spent for all observers."""
    budget = BandwidthBudget(hard_limit=1000)
    observer1 = EntityID(fake.uuid4())
    observer2 = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer1)
    budget.allocate_budget(observer_id=observer2)
    budget.spend(observer_id=observer1, bytes_spent=500)
    budget.spend(observer_id=observer2, bytes_spent=600)

    budget.reset()

    assert budget.get_remaining(observer_id=observer1) == 1000
    assert budget.get_remaining(observer_id=observer2) == 1000


def test_reset_observer() -> None:
    """Test reset_observer clears spent for specific observer."""
    budget = BandwidthBudget(hard_limit=1000)
    observer1 = EntityID(fake.uuid4())
    observer2 = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer1)
    budget.allocate_budget(observer_id=observer2)
    budget.spend(observer_id=observer1, bytes_spent=500)
    budget.spend(observer_id=observer2, bytes_spent=600)

    budget.reset_observer(observer_id=observer1)

    assert budget.get_remaining(observer_id=observer1) == 1000
    assert budget.get_remaining(observer_id=observer2) == 400


def test_reset_observer_no_spent() -> None:
    """Test reset_observer handles observer with no spending."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.reset_observer(observer_id=observer_id)

    assert budget.get_remaining(observer_id=observer_id) == 0


def test_remove_observer() -> None:
    """Test remove_observer removes observer tracking."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)
    budget.spend(observer_id=observer_id, bytes_spent=500)

    budget.remove_observer(observer_id=observer_id)

    assert budget.get_remaining(observer_id=observer_id) == 0
    assert budget.can_afford(observer_id=observer_id, bytes_needed=100) is False


def test_remove_observer_not_exists() -> None:
    """Test remove_observer handles non-existent observer."""
    budget = BandwidthBudget(hard_limit=1000)
    observer_id = EntityID(fake.uuid4())

    budget.remove_observer(observer_id=observer_id)

    assert budget.get_remaining(observer_id=observer_id) == 0


def test_budget_workflow() -> None:
    """Test complete budget workflow."""
    budget = BandwidthBudget(hard_limit=1000, soft_limit=800)
    observer_id = EntityID(fake.uuid4())

    budget.allocate_budget(observer_id=observer_id)

    assert budget.can_afford(observer_id=observer_id, bytes_needed=300) is True
    budget.spend(observer_id=observer_id, bytes_spent=300)

    assert budget.can_afford(observer_id=observer_id, bytes_needed=400) is True
    budget.spend(observer_id=observer_id, bytes_spent=400)

    assert budget.is_over_soft_limit(observer_id=observer_id) is False

    assert budget.can_afford(observer_id=observer_id, bytes_needed=200) is True
    budget.spend(observer_id=observer_id, bytes_spent=200)

    assert budget.is_over_soft_limit(observer_id=observer_id) is True
    assert budget.is_over_hard_limit(observer_id=observer_id) is False

    usage = budget.get_usage(observer_id=observer_id)
    assert usage.bytes_used == 900
    assert usage.bytes_remaining == 100

    budget.reset()

    usage = budget.get_usage(observer_id=observer_id)
    assert usage.bytes_used == 0
    assert usage.bytes_remaining == 1000
