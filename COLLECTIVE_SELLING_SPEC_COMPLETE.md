# Collective Selling & Allocation Spec - Complete ✅

**Created**: March 8, 2026  
**Feature**: Collective Selling & Allocation  
**Location**: `.kiro/specs/collective-selling-allocation/`

---

## What Was Created

A complete specification for transforming Anna Drishti from individual farmer optimization to FPO-level collective selling operations.

### Files Created

1. **requirements.md** - EARS-compliant requirements document
   - 10 major requirements with detailed acceptance criteria
   - Covers: inventory management, society profiles, demand prediction, allocation engine, processing partners, realization calculation, execution tracking, dashboard, data integrity, and integrations

2. **design.md** - Architecture and design document
   - System architecture with component diagram
   - 8 data models (CollectiveInventory, FarmerContribution, SocietyProfile, DemandPrediction, Reservation, ProcessingPartner, Allocation, ChannelAllocation)
   - 4 core algorithms (inventory aggregation, demand prediction, priority-based allocation, blended realization)
   - 10 correctness properties for property-based testing
   - Technology stack and integration points

3. **tasks.md** - Implementation task list
   - 24 major tasks with 80+ subtasks
   - Organized incrementally: data models → inventory → demand → allocation → realization → dashboard
   - Property-based tests for all 10 correctness properties
   - Integration with existing Sell Agent and Process Agent

---

## Feature Overview

### The Problem

Ramesh had 300 kg of tomatoes but no time to call buyers, check mandis, compare transport costs, and negotiate. By the time he reached the mandi, prices had dropped.

Meanwhile, a gated community wanted consistent farm-fresh vegetables, but supply was unpredictable. One week too little, next week too much.

### The Solution

**Collective Selling**: Ramesh's 300 kg becomes part of "12.4 tonnes across 40 farmers." The system treats fragmented farm supply as one coordinated market-facing load.

**Priority-Based Allocation**:
1. **Priority 1**: Society demand (reserved, predictable, premium pricing)
2. **Priority 2**: Processing partners (surplus, value-added, stable rates)
3. **Priority 3**: Mandi/buyers (remaining, spot market, price discovery)

**Blended Realization**: Farmers earn more by selling across multiple channels instead of dumping everything at one mandi.

---

## Key Features

### 1. Collective Inventory Management
- Pool farmer produce into FPO-level inventory
- Track individual farmer contributions
- Real-time aggregation with DynamoDB atomic counters
- Maintain available, reserved, and allocated quantities

### 2. Society Demand Prediction & Reservation
- Society registration with delivery preferences (frequency, day, time)
- Demand prediction using exponential weighted moving average
- Automatic reservation before allocation begins
- Predictable supply for recurring customers

### 3. Priority-Based Allocation Engine
- Three-tier allocation: societies → processing → mandi
- Respects capacity constraints and quality requirements
- Timestamp-based ordering for fair allocation
- Flags unfulfilled reservations

### 4. Blended Realization Calculation
- Calculate average price across all channels
- Per-farmer income with channel breakdown
- Compare to best single-channel price
- Show improvement percentage

### 5. Processing Partner Management
- Pre-agreed rates by crop type
- Daily/weekly capacity limits
- Quality requirements and pickup schedules
- Automatic allocation to highest-paying partners

### 6. Dashboard Visualization
- Collective inventory view (real-time)
- Society delivery schedule (calendar)
- Allocation flow (Sankey diagram)
- Blended realization metrics
- Per-farmer contribution tracking
- Alerts for shortages and unfulfilled reservations

---

## Correctness Properties

The spec includes 10 correctness properties validated through property-based testing:

1. **Inventory Conservation**: available + reserved + allocated = total
2. **Contribution Aggregation**: total = sum of all contributions
3. **Priority Ordering**: societies before processing before mandi
4. **Reservation Fulfillment**: all reservations fulfilled if inventory sufficient
5. **No Over-Allocation**: allocated ≤ available inventory
6. **Blended Realization Accuracy**: blended rate = total revenue / total quantity
7. **Farmer Income Conservation**: sum of farmer incomes = total revenue
8. **Demand Prediction Bounds**: quantity ≥ 0, confidence ∈ [0, 1]
9. **Processing Capacity Constraint**: allocated ≤ partner capacity
10. **Reservation Timestamp Ordering**: earlier reservations fulfilled first

---

## Technology Stack

- **Backend**: Python 3.11, AWS Lambda, FastAPI
- **Database**: PostgreSQL (relational), DynamoDB (real-time inventory)
- **Frontend**: React 18, TypeScript, Recharts
- **Testing**: Hypothesis (property-based), pytest
- **Infrastructure**: AWS CDK

---

## Integration Points

### With Sell Agent
- Sell Agent routes farmer produce to Collective Inventory
- Sell Agent queries allocation data for mandi dispatch

### With Process Agent
- Process Agent uses allocation data for processing coordination
- Process Agent updates fulfillment status

### With Dashboard
- Real-time inventory updates via WebSocket
- Allocation visualization with Sankey diagrams
- Society management and demand prediction interfaces

---

## Scalability Targets

- **500 farmers** per FPO
- **50 societies** per FPO
- **10 processing partners** per FPO
- **100 concurrent** inventory updates
- **< 5 seconds** allocation time

---

## Implementation Roadmap

### Phase 1: Core Infrastructure (2 weeks)
- Data models and database schema
- Inventory aggregation
- Society management
- Processing partner management

### Phase 2: Allocation Engine (2 weeks)
- Demand prediction
- Reservation system
- Priority-based allocation
- Blended realization calculation

### Phase 3: Execution & Tracking (1 week)
- Order generation (delivery, pickup, dispatch)
- Fulfillment tracking
- Data integrity and validation

### Phase 4: Dashboard (2 weeks)
- Collective inventory view
- Society schedule
- Allocation flow visualization
- Realization metrics
- Per-farmer tracking

### Phase 5: Integration & Deployment (1 week)
- Sell Agent integration
- Process Agent integration
- API endpoints
- AWS infrastructure deployment

**Total Estimated Time**: 8 weeks

---

## Next Steps

1. **Review the spec** - Open `.kiro/specs/collective-selling-allocation/` and review all three files
2. **Prioritize tasks** - Decide which tasks are MVP vs nice-to-have
3. **Start implementation** - Begin with Task 1 (project structure and data models)
4. **Run tests incrementally** - Use checkpoints to validate progress
5. **Deploy to staging** - Test with realistic data before production

---

## Why This Matters

This isn't just another feature. This is a **fundamental transformation** of Anna Drishti:

**Before**: Individual farmer marketplace  
**After**: Operating system for collective selling

**Before**: Ramesh sells 300 kg to one buyer  
**After**: 40 farmers sell 12.4 tonnes across societies, processing, and mandis

**Before**: Panic selling at whatever price  
**After**: Strategic allocation with blended realization

**Before**: Unpredictable supply for societies  
**After**: Reserved, predictable, premium-priced supply

This is how small farmers stop behaving like isolated sellers and start operating like one organized supply engine.

---

## Questions?

- Review requirements: `.kiro/specs/collective-selling-allocation/requirements.md`
- Review design: `.kiro/specs/collective-selling-allocation/design.md`
- Review tasks: `.kiro/specs/collective-selling-allocation/tasks.md`

Ready to build the future of collective selling! 🚀
