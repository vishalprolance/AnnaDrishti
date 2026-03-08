-- Collective Selling & Allocation Database Schema
-- PostgreSQL schema for relational data

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Societies table
CREATE TABLE IF NOT EXISTS societies (
    society_id VARCHAR(50) PRIMARY KEY,
    society_name VARCHAR(255) NOT NULL,
    location VARCHAR(255) NOT NULL,
    contact_details JSONB NOT NULL,
    delivery_address TEXT NOT NULL,
    delivery_frequency VARCHAR(20) NOT NULL CHECK (delivery_frequency IN ('once_weekly', 'twice_weekly', 'weekend_only')),
    preferred_day VARCHAR(20) NOT NULL,
    preferred_time_window VARCHAR(20) NOT NULL,
    crop_preferences JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_societies_location ON societies(location);
CREATE INDEX idx_societies_delivery_frequency ON societies(delivery_frequency);

-- Processing partners table
CREATE TABLE IF NOT EXISTS processing_partners (
    partner_id VARCHAR(50) PRIMARY KEY,
    partner_name VARCHAR(255) NOT NULL,
    contact_details JSONB NOT NULL,
    facility_location VARCHAR(255) NOT NULL,
    rates_by_crop JSONB NOT NULL,
    capacity_by_crop JSONB NOT NULL,
    quality_requirements JSONB DEFAULT '{}'::jsonb,
    pickup_schedule TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_processing_partners_location ON processing_partners(facility_location);

-- Demand predictions table
CREATE TABLE IF NOT EXISTS demand_predictions (
    prediction_id VARCHAR(50) PRIMARY KEY,
    society_id VARCHAR(50) NOT NULL REFERENCES societies(society_id) ON DELETE CASCADE,
    crop_type VARCHAR(50) NOT NULL,
    predicted_quantity_kg DECIMAL(10, 2) NOT NULL CHECK (predicted_quantity_kg >= 0),
    confidence_score DECIMAL(3, 2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    prediction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    delivery_date DATE NOT NULL,
    based_on_orders INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'predicted' CHECK (status IN ('predicted', 'confirmed', 'fulfilled', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_demand_predictions_society ON demand_predictions(society_id);
CREATE INDEX idx_demand_predictions_delivery_date ON demand_predictions(delivery_date);
CREATE INDEX idx_demand_predictions_status ON demand_predictions(status);
CREATE INDEX idx_demand_predictions_crop ON demand_predictions(crop_type);

-- Allocations table
CREATE TABLE IF NOT EXISTS allocations (
    allocation_id VARCHAR(50) PRIMARY KEY,
    fpo_id VARCHAR(50) NOT NULL,
    crop_type VARCHAR(50) NOT NULL,
    allocation_date DATE NOT NULL,
    total_quantity_kg DECIMAL(10, 2) NOT NULL CHECK (total_quantity_kg >= 0),
    blended_realization_per_kg DECIMAL(10, 2) NOT NULL CHECK (blended_realization_per_kg >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'executed', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_allocations_fpo ON allocations(fpo_id);
CREATE INDEX idx_allocations_date ON allocations(allocation_date);
CREATE INDEX idx_allocations_crop ON allocations(crop_type);
CREATE INDEX idx_allocations_status ON allocations(status);

-- Channel allocations table (one-to-many with allocations)
CREATE TABLE IF NOT EXISTS channel_allocations (
    id SERIAL PRIMARY KEY,
    allocation_id VARCHAR(50) NOT NULL REFERENCES allocations(allocation_id) ON DELETE CASCADE,
    channel_type VARCHAR(20) NOT NULL CHECK (channel_type IN ('society', 'processing', 'mandi')),
    channel_id VARCHAR(50) NOT NULL,
    channel_name VARCHAR(255) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL CHECK (quantity_kg >= 0),
    price_per_kg DECIMAL(10, 2) NOT NULL CHECK (price_per_kg >= 0),
    revenue DECIMAL(12, 2) NOT NULL CHECK (revenue >= 0),
    priority INTEGER NOT NULL CHECK (priority IN (1, 2, 3)),
    fulfillment_status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (fulfillment_status IN ('pending', 'in_transit', 'delivered', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_channel_allocations_allocation ON channel_allocations(allocation_id);
CREATE INDEX idx_channel_allocations_channel_type ON channel_allocations(channel_type);
CREATE INDEX idx_channel_allocations_channel_id ON channel_allocations(channel_id);
CREATE INDEX idx_channel_allocations_priority ON channel_allocations(priority);
CREATE INDEX idx_channel_allocations_status ON channel_allocations(fulfillment_status);

-- Order history table (for demand prediction)
CREATE TABLE IF NOT EXISTS order_history (
    order_id VARCHAR(50) PRIMARY KEY,
    society_id VARCHAR(50) NOT NULL REFERENCES societies(society_id) ON DELETE CASCADE,
    crop_type VARCHAR(50) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL CHECK (quantity_kg >= 0),
    order_date DATE NOT NULL,
    delivery_date DATE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_history_society ON order_history(society_id);
CREATE INDEX idx_order_history_crop ON order_history(crop_type);
CREATE INDEX idx_order_history_order_date ON order_history(order_date);

-- Delivery orders table
CREATE TABLE IF NOT EXISTS delivery_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    allocation_id VARCHAR(50) NOT NULL REFERENCES allocations(allocation_id) ON DELETE CASCADE,
    society_id VARCHAR(50) NOT NULL REFERENCES societies(society_id) ON DELETE CASCADE,
    crop_type VARCHAR(50) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL CHECK (quantity_kg >= 0),
    delivery_date DATE NOT NULL,
    delivery_time_window VARCHAR(20) NOT NULL,
    delivery_address TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_transit', 'delivered', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_delivery_orders_allocation ON delivery_orders(allocation_id);
CREATE INDEX idx_delivery_orders_society ON delivery_orders(society_id);
CREATE INDEX idx_delivery_orders_delivery_date ON delivery_orders(delivery_date);
CREATE INDEX idx_delivery_orders_status ON delivery_orders(status);

-- Pickup orders table
CREATE TABLE IF NOT EXISTS pickup_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    allocation_id VARCHAR(50) NOT NULL REFERENCES allocations(allocation_id) ON DELETE CASCADE,
    partner_id VARCHAR(50) NOT NULL REFERENCES processing_partners(partner_id) ON DELETE CASCADE,
    crop_type VARCHAR(50) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL CHECK (quantity_kg >= 0),
    pickup_date DATE NOT NULL,
    pickup_location VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_transit', 'delivered', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_pickup_orders_allocation ON pickup_orders(allocation_id);
CREATE INDEX idx_pickup_orders_partner ON pickup_orders(partner_id);
CREATE INDEX idx_pickup_orders_pickup_date ON pickup_orders(pickup_date);
CREATE INDEX idx_pickup_orders_status ON pickup_orders(status);

-- Mandi dispatch orders table
CREATE TABLE IF NOT EXISTS mandi_dispatch_orders (
    order_id VARCHAR(50) PRIMARY KEY,
    allocation_id VARCHAR(50) NOT NULL REFERENCES allocations(allocation_id) ON DELETE CASCADE,
    mandi_id VARCHAR(50) NOT NULL,
    mandi_name VARCHAR(255) NOT NULL,
    crop_type VARCHAR(50) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL CHECK (quantity_kg >= 0),
    dispatch_date DATE NOT NULL,
    destination VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_transit', 'delivered', 'completed')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mandi_dispatch_orders_allocation ON mandi_dispatch_orders(allocation_id);
CREATE INDEX idx_mandi_dispatch_orders_mandi ON mandi_dispatch_orders(mandi_id);
CREATE INDEX idx_mandi_dispatch_orders_dispatch_date ON mandi_dispatch_orders(dispatch_date);
CREATE INDEX idx_mandi_dispatch_orders_status ON mandi_dispatch_orders(status);

-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    log_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    changes JSONB,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_log_user ON audit_log(user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_societies_updated_at BEFORE UPDATE ON societies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_processing_partners_updated_at BEFORE UPDATE ON processing_partners
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_demand_predictions_updated_at BEFORE UPDATE ON demand_predictions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_allocations_updated_at BEFORE UPDATE ON allocations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_channel_allocations_updated_at BEFORE UPDATE ON channel_allocations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_delivery_orders_updated_at BEFORE UPDATE ON delivery_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pickup_orders_updated_at BEFORE UPDATE ON pickup_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_mandi_dispatch_orders_updated_at BEFORE UPDATE ON mandi_dispatch_orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE societies IS 'Residential societies that order produce on recurring schedules';
COMMENT ON TABLE processing_partners IS 'Processing partners with pre-agreed rates and capacity';
COMMENT ON TABLE demand_predictions IS 'Predicted demand for societies based on historical patterns';
COMMENT ON TABLE allocations IS 'Inventory allocations across channels';
COMMENT ON TABLE channel_allocations IS 'Individual channel allocations within an allocation';
COMMENT ON TABLE order_history IS 'Historical orders for demand prediction';
COMMENT ON TABLE delivery_orders IS 'Delivery orders for societies';
COMMENT ON TABLE pickup_orders IS 'Pickup orders for processing partners';
COMMENT ON TABLE mandi_dispatch_orders IS 'Dispatch orders for mandis';
COMMENT ON TABLE audit_log IS 'Audit trail for all changes';
