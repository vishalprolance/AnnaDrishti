# Design Document: Collective Selling & Allocation

## Overview

The Collective Selling & Allocation system transforms Anna Drishti from individual farmer optimization to FPO-level collective operations. The system pools farmer produce into collective inventory, predicts society demand, and allocates inventory across three priority tiers: societies (Priority 1), processing partners (Priority 2), and mandi/buyers (Priority 3). This design enables small farmers to operate as one organized supply engine while maximizing blended realization.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Collective Selling System                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │  Inventory Pool  │◄─────┤  Farmer Input    │                │
│  │   Aggregator     │      │    Handler       │                │
│  └────────┬─────────┘      └──────────────────┘                │
│           │                                                       │
│           ▼                                                       │
│  ┌──────────────────┐      ┌──────────────────┐                │
│  │   Demand         │◄─────┤  Society         │                │
│  │   Predictor      │      │  Manager         │                │
│  └────────┬─────────┘      └──────────────────┘                │
│           │                                                       │
│           ▼                                                       │
│  ┌──────────────────┐                                           │
│  │   Allocation     │──────┐                                    │
│  │   Engine         │      │                                    │
│  └────────┬─────────┘      │                                    │
│           │                │                                    │
│           ├────────────────┼────────────────┐                  │
│           ▼                ▼                ▼                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Society     │  │  Processing  │  │  Mandi       │        │
│  │  Fulfillment │  │  Partner     │  │  Dispatch    │        │
│  ───┘  └──────────────┘        │
│           │                │                │                  │
│           └────────────────┴────────────────┘                  │
│                            │                                    │
│                            ▼                                    │
│                   ┌──────────────────┐                         │
│                   │  Realization     │                         │
│                   │  Calculator      │                         │
│                   └──────────────────┘                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Models

#### CollectiveInventory
```python
{
    "fpo_id": str,
    "crop_type": str,
    "total_quantity_kg": Decimal,
    "available_quantity_kg": Decimal,  # total - reserved - allocated
    "reserved_quantity_kg": Decimal,
    "allocated_quantity_kg": Decimal,
    "contributions": List[FarmerContribution],
    "last_updated": datetime
}
```

#### FarmerContribution
```python
{
    "contribution_id": str,
    "farmer_id": str,
    "farmer_name": str,
    "crop_type": str,
    "quantity_kg": Decimal,
    "quality_grade": str,  # A, B, C
    "timestamp": datetime,
    "allocated": bool
}
```

#### SocietyProfile
```python
{
    "society_id": str,
    "society_name": str,
    "location": str,
    "contact_details": dict,
    "delivery_address": str,
    "delivery_frequency": sonly"
    "preferred_day": str,
    "preferred_time_window": str,
    "crop_preferences": List[dict],  # [{crop_type, typical_quantity_kg}]
    "created_at": datetime
}
```

#### DemandPrediction
```python
{
    "prediction_id": str,
    "society_id": str,
    "crop_type": str,
    "predicted_quantity_kg": Decimal,
    "confidence_score": float,  # 0.0 to 1.0
    "prediction_date": datetime,
    "delivery_date": datetime,
    "based_on_orders": int,  # number of historical orders used
    "staticted", "confirmed", "fulfilled"
}
```

#### Reservation
```python
{
    "reservation_id": str,
    "society_id": str,
    "crop_type": str,
    "reserved_quantity_kg": Decimal,
    "reservation_timestamp": datetime,
    "delivery_date": datetime,
    "status": str  # "reserved", "confirmed", "fulfilled", "cancelled"
}
```

#### ProcessingPartner
```python
{
    "partner_id": str,
    "partner_name": str,
    "contact_details": dict,
    "facility_location": str,
    "rates_by_crop": dict,  # {crop_type: r_per_kg}
    "capacity_by_crop": dict,  # {crop_type: daily_capacity_kg}
    "quality_requirements": dict,
    "pickup_schedule": str,
    "created_at": datetime
}
```

#### Allocation
```python
{
    "allocation_id": str,
    "fpo_id": str,
    "crop_type": str,
    "allocation_date": datetime,
    "channel_allocations": List[ChannelAllocation],
    "total_quantity_kg": Decimal,
    "blended_realization_per_kg": Decimal,
    "status": str  # "pending", "executed", "completed"
}
```

#### ChannelAllocation
```python
{
    "channel_type": str,  # "society", "processing", "mandi"
    "channel_id": str,
    "channel_name": str,
    "quantity_kg": Decimal,
    "price_per_kg": Decimal,
    "revenue": Decimal,
    "priority": int,  # 1, 2, or 3
    "fulfillment_status": str  # "pending", "in_transit", "delivered"
}
```

### Core Algorithms

#### 1. Inventory Aggregation Algorithm

```python
def aggregate_farmer_contribution(contribution: FarmerContribution) -> CollectiveInventory:
    """
    Aggregate farmer cto collective inventory.
    
    Invariants:
    - total_quantity = sum(all contributions)
    - available_quantity = total - reserved - allocated
    - available_quantity >= 0
    """
    inventory = get_or_create_inventory(contribution.fpo_id, contribution.crop_type)
    
    # Add contribution
    inventory.contributions.append(contribution)
    inventory.total_quantity_kg += contribution.quantity_kg
    inventory.available_quantity_kg += contribution.quantity_kg
 w()
    
    # Validate invariants
    assert inventory.total_quantity_kg == sum(c.quantity_kg for c in inventory.contributions)
    assert inventory.available_quantity_kg >= 0
    
    return inventory
```

#### 2. Demand Prediction Algorithm

```python
def predict_society_demand(society_id: str, crop_type: str, delivery_date: date) -> DemandPrediction:
    """
    Predict society demand based on historical patterns.
    
    Uses exponential weighted moving average with recent orders weighted higher.
    """
    historical_orders = get_historical_orders(society_id, crop_type, lookback_days=90)
    
    if len(historical_orders) < 3:
        # Insufficient data, use society's typical quantity
        society = get_society_profile(society_id)
        typical_qty = get_typical_quantity(society, crop_type)
        return DemandPrediction(
            predicted_quantity_kg=typical_qty,
            confidence_score=0.5,
            based_on_orders=0
        )
    
    # Exponential weighted moving average
    weighs = [0.5, 0.3, 0.2]  # Recent orders weighted higher
    recent_orders = historical_orders[-3:]
    predicted_qty = sum(order.quantity_kg * weight for order, weight in zip(recent_orders, weights))
    
    # Confidence based on consistency
    std_dev = calculate_std_dev([o.quantity_kg for o in recent_orders])
    confidence = max(0.5, 1.0 - (std_dev / predicted_qty))
    
    return DemandPrediction(
        predicted_quantity_kg=predicted_qty,
        confidence_score=confidence,
        based_on_orders=len(historical_orders)
    )
```

#### 3. Priority-Based Allocation Algorithm

```python
def allocate_inventory(fpo_id: str, crop_type: str, allocation_date: date) -> Allocation:
    """
    Allocate inventory across channels by priority.
    
    Priority 1: Society reservations
ssing partners
    Priority 3: Mandi/buyers
    
    Invariants:
    - Sum of allocated quantities <= available inventory
    - Society reservations fulfilled first
    - No double allocation
    """
    inventory = get_collective_inventory(fpo_id, crop_type)
    available = inventory.available_quantity_kg
    channel_allocations = []
    
    # Priority 1: Society Reservations
    reservations = get_active_reservations(fpo_id, crop_type, allocation_date)
    for r: r.reservation_timestamp):
        allocated_qty = min(reservation.reserved_quantity_kg, available)
        
        if allocated_qty > 0:
            channel_allocations.append(ChannelAllocation(
                channel_type="society",
                channel_id=reservation.society_id,
                quantity_kg=allocated_qty,
                price_per_kg=get_society_price(crop_type),
                priority=1
            ))
            available -= allocated_qty
            
            if allocated_qty < reservation.reserved_quantity_kg:
                # Flag unfulfilled reservation
                flag_shortage(reservation, allocated_qty)
    
    # Priority 2: Processing Partners
    if available > 0:
        partners = get_processing_partners(fpo_id, crop_type)
        for partner in sorted(partners, key=lambda p: p.rates_by_crop[crop_type], reverse=True):
            capacity = partner.capacity_by_crop.get(crop_type, 0)
            allocated_qty = min(capacity, available)
            
            if allocated_qty > 0:
                channel_allocations.append(ChannelAllocation(
                    channel_type="processing",
                    channel_id=partner.partner_id,
                    quantity_kg=allocated_qty,
                    price_per_kg=partner.rates_by_crop[crop_type],
                    priority=2
                ))
                available -= allocated_qty
    
    # Priority 3: Mandi/Buyers
    if available > 0:
        best_mandi = get_best_mandi_price(crop_type, allocation_date)
        channel_allocations.append(ChannelAllocation(
            channel_type="mandi",
            channel_id=best_mandi.mandi_id,
            quantity_kg=available,
            price_per_kg=best_mandi.price_per_kg,
            priority=3
        ))
        available = 0
    
    # Calculate blended realization
    total_revenue = sum(ca.quantity_kg * ca.price_per_kg for ca in channel_allocations)
    total_quantity = sum(ca.quantity_kg for ca in channel_allocations)
    if total_quantity > 0 else 0
    
    # Update inventory
    inventory.allocated_quantity_kg += total_quantity
    inventory.available_quantity_kg = available
    
    return Allocation(
        fpo_id=fpo_id,
        crop_type=crop_type,
        allocation_date=allocation_date,
        channel_allocations=channel_allocations,
        total_quantity_kg=total_quantity,
        blended_realization_per_kg=blended_rate,
        status="pending"
    )
```

#### 4. Blended Realization Calculation

```python
def calculate_farmer_income(farmer_id: str, allocation: Allocation) -> dict:
    """
    Calculate individual farmer income from collective allocation.
    
    Income = (farmer_contribution / total_inventory) * total_revenue
    """
    # Get farmer's contribution
    inventory = get_collective_inventory(allocation.fpo_id, allocation.crop_type)
    farmer_contribution = sum(
        c.quantity_kg for c in inventory.contributions 
        if c.farmer_id == farmer_id
    )
    
    # Calculate share of revenue
    total_quantity = allocation.total_quantity_kg
    total_revenue = sum(
        ca.quantity_kg * ca.price_per_kg 
        for ca in allocation.channel_allocations
    )
    
    farmer_revenue = (farmer_contribution / total_quantity) * total_revenue
    farmer_rate = farmer_revenue / farmer_contribution if farmer_contribution > 0 else 0
    
    # Calculate channel breakdown
    channel_breakdown = []
    for ca in allocation.channel_allocations:
        farmer_qty_in_channel = (farmer_contribution / ty) * ca.quantity_kg
        channel_revenue = farmer_qty_in_channel * ca.price_per_kg
        channel_breakdown.append({
            "channel": ca.channel_type,
            "quantity_kg": farmer_qty_in_channel,
            "revenue": channel_revenue,
            "rate_per_kg": ca.price_per_kg
        })
    
    # Compare to best single-channel
    best_single_channel = max(allocation.channel_allocations, key=lambda ca: ca.price_per_kg)
    sinper_kg
    improvement = farmer_revenue - single_channel_revenue
    
    return {
        "farmer_id": farmer_id,
        "contribution_kg": farmer_contribution,
        "blended_rate_per_kg": farmer_rate,
        "total_revenue": farmer_revenue,
        "channel_breakdown": channel_breakdown,
        "vs_best_single_channel": {
            "single_channel_revenue": single_channel_revenue,
            "improvement": improvement,
le_channel_revenue > 0 else 0
        }
    }
```

## Correctness Properties

### Property 1: Inventory Conservation
**For any collective inventory, the sum of available, reserved, and allocated quantities must equal the total quantity.**

```python
def test_inventory_conservation(inventory: CollectiveInventory):
    assert inventory.available_quantity_kg + inventory.reserved_quantity_kg + inventory.allocated_quantity_kg == inventory.total_quantity_kg
```

### Property 2: Contribution Aggregation
**For any collective inventory, the total quantity must equal the sum of all farmer contributions.**

```python
def test_contribution_aggregation(inventory: CollectiveInventory):
    total_contributions = sum(c.quantity_kg for c in inventory.contributions)
    assert inventory.total_quantity_kg == total_contributions
```

### Property 3: Priority Ordering
**For any allocation, society allocarity 3).**

```python
def test_priority_ordering(allocation: Allocation):
    priorities = [ca.priority for ca in allocation.channel_allocations]
    # Check that priorities are in ascending order (1, 2, 3)
    for i in range(len(priorities) - 1):
        assert priorities[i] <= priorities[i + 1]
```

### Property 4: Reservation Fulfillment
**For any allocation, if available inventory >= total reservations, then all reservations must be fully allocated.**

```python
def test_reservation_fulfillment(allocation: Allocation, reservations: List[Reservation], available_inventory: Decimal):
    total_reserved = sum(r.reserved_quantity_kg for r in reservations)
    
    if available_inventory >= total_reserved:
        society_allocations = [ca for ca in allocation.channel_allocations if ca.channel_type == "society"]
        total_society_allocated = sum(ca.quantity_kg for ca in society_allocations)
        assert total_society_allocated == total_reserved
```

### Property 5: No Over-Allocation
**For any allocation, the sum of allocated quantities across all channels must not exceed available inventory.**

```python
def test_no_over_allocation(allocation: Allocation, available_inventory: Decimal):
    total_allocated = sum(ca.quantity_kg for ca in allocation.channel_allocations)
    assert total_allocated <= available_inventory
```

### Property 6: Blended Realization Accuracy
**For any allocation, the blended realization must equal total revenue divided by total quantity.**

```python
def test_blended_realization_accuracation: Allocation):
    total_revenue = sum(ca.quantity_kg * ca.price_per_kg for ca in allocation.channel_allocations)
    total_quantity = sum(ca.quantity_kg for ca in allocation.channel_allocations)
    
    if total_quantity > 0:
        expected_blended_rate = total_revenue / total_quantity
        assert abs(allocation.blended_realization_per_kg - expected_blended_rate) < Decimal("0.01")
```

### Property 7: Farmer Income Conservation
venue from the allocation.**

```python
def test_farmer_income_conservation(allocation: Allocation, farmer_ids: List[str]):
    total_revenue = sum(ca.quantity_kg * ca.price_per_kg for ca in allocation.channel_allocations)
    
    farmer_incomes = [calculate_farmer_income(fid, allocation) for fid in farmer_ids]
    sum_farmer_revenues = sum(fi["total_revenue"] for fi in farmer_incomes)
    
    assert abs(sum_farmer_revenues - total_revenue) < Decimal("0.01")
```

### Property 8: Demand Prediction Bounds
**For any demand prediction, the predicted quantity must be non-negative and confidence score must be between 0 and 1.**

```python
def test_demand_prediction_bounds(prediction: DemandPrediction):
    assert prediction.predicted_quantity_kg >= 0
    assert 0.0 <= prediction.confidence_score <= 1.0
```

### Property 9: Processing Capacity Constraint
**For any allocation to processing partners, the allocated quantity must not exceed the partner's capacity.**

```python
def test_processing_capacity_conn: Allocation, partners: List[ProcessingPartner]):
    for ca in allocation.channel_allocations:
        if ca.channel_type == "processing":
            partner = next(p for p in partners if p.partner_id == ca.channel_id)
            capacity = partner.capacity_by_crop.get(allocation.crop_type, 0)
            assert ca.quantity_kg <= capacity
```

### Property 10: Reservation Timestamp Ordering
**For any set of reservations with ire later ones.**

```python
def test_reservation_timestamp_ordering(allocation: Allocation, reservations: List[Reservation]):
    society_allocations = sorted(
        [ca for ca in allocation.channel_allocations if ca.channel_type == "society"],
        key=lambda ca: next(r.reservation_timestamp for r in reservations if r.society_id == ca.channel_id)
    )
    
    # Check that allocations are in timestamp order
    for i in range(len(society_allocations) - 1):
        ts1 = next(r.reservation r in reservations if r.society_id == society_allocations[i].channel_id)
        ts2 = next(r.reservation_timestamp for r in reservations if r.society_id == society_allocations[i+1].channel_id)
        assert ts1 <= ts2
```

## Technology Stack

- **Backend**: Python 3.11, AWS Lambda
- **Database**: PostgreSQL (relational data), DynamoDB (real-time inventory)
- **API**: FastAPI (REST endpoints)
- **Frontend**: React 18, TypeScript, Recharts (visualization)
- **Testing**: Hypothesis (property-
- **Infrastructure**: AWS CDK

## Integration Points

### With Sell Agent
- Sell Agent routes farmer produce to Collective Inventory Aggregator
- Sell Agent queries allocation data for mandi dispatch

### With Process Agent
- Process Agent uses allocation data for processing partner coordination
- Process Agent updates fulfillment status for processing allocations

### With Dashboard
- Dashboard displays collective inventory, allocation flow, and realization metrics
- Dashboard provides society management and demand prediction interfaces

## Performance Considerations

- **Inventory Aggregation**: O(1) per contribution using DynamoDB atomic counters
- **Allocation Algorithm**: O(n log n) where n = number of reservations + partners
- **Demand Prediction**: O(k) where k = number of historical orders (limited to 90 days)
- **Realization Calculation**: O(m) where m = number of farmers

## Security Considerations

- Society profiles contain sensitive contact information - encrypt at rest
- Farmer contribution data must be auditable - maintain immutable logs
- Allocation decisions must be transparent - provide audit trail
- API endpoints require FPO coordinator authentication

## Scalability Targets

- Support 500 farmers per FPO
- Support 50 societies per FPO
- Support 10 processing partners per FPO
- Handle 100 concurrent inventory updates
- Complete allocation in < 5 seconds for typical FPO

