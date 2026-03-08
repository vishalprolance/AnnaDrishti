"""
Property-based test for demand prediction bounds.

**Validates: Requirements 3.1**

Property 8: Demand Prediction Bounds
For any demand prediction, the predicted quantity must be non-negative and 
confidence score must be between 0 and 1.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
from hypothesis import given, strategies as st, assume
from hypothesis import settings

from backend.collective.models import (
    DemandPrediction,
    ReservationStatus,
)


# Hypothesis strategies for generating test data
@st.composite
def demand_prediction_strategy(draw):
    """Generate a valid DemandPrediction."""
    prediction_id = draw(st.uuids()).hex
    society_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))))
    crop_type = draw(st.sampled_from(["tomato", "onion", "potato", "carrot", "cabbage"]))
    
    # Generate non-negative predicted quantity (0 to 1000 kg)
    predicted_quantity_kg = draw(st.decimals(
        min_value=Decimal("0"), 
        max_value=Decimal("1000"), 
        places=2
    ))
    
    # Generate confidence score between 0.0 and 1.0
    confidence_score = draw(st.floats(min_value=0.0, max_value=1.0))
    
    prediction_date = datetime.now()
    delivery_date = date.today() + timedelta(days=draw(st.integers(min_value=1, max_value=30)))
    based_on_orders = draw(st.integers(min_value=0, max_value=100))
    status = draw(st.sampled_from(list(ReservationStatus)))
    
    return DemandPrediction(
        prediction_id=prediction_id,
        society_id=society_id,
        crop_type=crop_type,
        predicted_quantity_kg=predicted_quantity_kg,
        confidence_score=confidence_score,
        prediction_date=prediction_date,
        delivery_date=delivery_date,
        based_on_orders=based_on_orders,
        status=status,
    )


class TestDemandPredictionBounds:
    """
    Property-based tests for demand prediction bounds.
    
    **Validates: Requirements 3.1**
    """
    
    @given(demand_prediction_strategy())
    @settings(max_examples=100, deadline=None)
    def test_demand_prediction_bounds_property(self, prediction: DemandPrediction):
        """
        Property 8: Demand Prediction Bounds
        
        For any demand prediction, the predicted quantity must be non-negative 
        and confidence score must be between 0 and 1.
        
        **Validates: Requirements 3.1**
        """
        # Property 1: Predicted quantity must be non-negative
        assert prediction.predicted_quantity_kg >= 0, (
            f"Predicted quantity is negative: {prediction.predicted_quantity_kg}"
        )
        
        # Property 2: Confidence score must be between 0.0 and 1.0
        assert 0.0 <= prediction.confidence_score <= 1.0, (
            f"Confidence score out of bounds: {prediction.confidence_score}"
        )
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.decimals(min_value=Decimal("0"), max_value=Decimal("1000"), places=2),
        st.floats(min_value=0.0, max_value=1.0),
        st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_prediction_creation_with_valid_bounds(
        self, 
        society_id: str, 
        crop_type: str, 
        quantity: Decimal, 
        confidence: float,
        based_on_orders: int
    ):
        """
        Test that creating predictions with valid bounds succeeds.
        
        **Validates: Requirements 3.1**
        """
        prediction = DemandPrediction(
            prediction_id="test_pred",
            society_id=society_id,
            crop_type=crop_type,
            predicted_quantity_kg=quantity,
            confidence_score=confidence,
            prediction_date=datetime.now(),
            delivery_date=date.today() + timedelta(days=7),
            based_on_orders=based_on_orders,
            status=ReservationStatus.PREDICTED,
        )
        
        # Verify bounds are maintained
        assert prediction.predicted_quantity_kg >= 0
        assert 0.0 <= prediction.confidence_score <= 1.0
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.decimals(min_value=Decimal("-1000"), max_value=Decimal("-0.01"), places=2),
        st.floats(min_value=0.0, max_value=1.0),
    )
    @settings(max_examples=100, deadline=None)
    def test_negative_quantity_rejected(
        self, 
        society_id: str, 
        crop_type: str, 
        negative_quantity: Decimal,
        confidence: float
    ):
        """
        Test that negative predicted quantities are rejected.
        
        **Validates: Requirements 3.1**
        """
        with pytest.raises(ValueError, match="Predicted quantity cannot be negative"):
            DemandPrediction(
                prediction_id="test_pred",
                society_id=society_id,
                crop_type=crop_type,
                predicted_quantity_kg=negative_quantity,
                confidence_score=confidence,
                prediction_date=datetime.now(),
                delivery_date=date.today() + timedelta(days=7),
                based_on_orders=5,
                status=ReservationStatus.PREDICTED,
            )
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.decimals(min_value=Decimal("0"), max_value=Decimal("1000"), places=2),
        st.one_of(
            st.floats(min_value=-100.0, max_value=-0.01),
            st.floats(min_value=1.01, max_value=100.0)
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_invalid_confidence_score_rejected(
        self, 
        society_id: str, 
        crop_type: str, 
        quantity: Decimal,
        invalid_confidence: float
    ):
        """
        Test that confidence scores outside [0, 1] are rejected.
        
        **Validates: Requirements 3.1**
        """
        with pytest.raises(ValueError, match="Confidence score must be between 0 and 1"):
            DemandPrediction(
                prediction_id="test_pred",
                society_id=society_id,
                crop_type=crop_type,
                predicted_quantity_kg=quantity,
                confidence_score=invalid_confidence,
                prediction_date=datetime.now(),
                delivery_date=date.today() + timedelta(days=7),
                based_on_orders=5,
                status=ReservationStatus.PREDICTED,
            )
    
    @given(demand_prediction_strategy())
    @settings(max_examples=100, deadline=None)
    def test_zero_quantity_is_valid(self, prediction: DemandPrediction):
        """
        Test that zero predicted quantity is valid (edge case).
        
        A prediction of zero demand is valid and should not be rejected.
        
        **Validates: Requirements 3.1**
        """
        # Create a prediction with zero quantity
        zero_prediction = DemandPrediction(
            prediction_id=prediction.prediction_id,
            society_id=prediction.society_id,
            crop_type=prediction.crop_type,
            predicted_quantity_kg=Decimal("0"),
            confidence_score=prediction.confidence_score,
            prediction_date=prediction.prediction_date,
            delivery_date=prediction.delivery_date,
            based_on_orders=prediction.based_on_orders,
            status=prediction.status,
        )
        
        # Zero should be valid
        assert zero_prediction.predicted_quantity_kg == 0
        assert zero_prediction.predicted_quantity_kg >= 0
    
    @given(demand_prediction_strategy())
    @settings(max_examples=100, deadline=None)
    def test_boundary_confidence_scores_valid(self, prediction: DemandPrediction):
        """
        Test that boundary confidence scores (0.0 and 1.0) are valid.
        
        **Validates: Requirements 3.1**
        """
        # Test confidence = 0.0
        prediction_zero_confidence = DemandPrediction(
            prediction_id=prediction.prediction_id + "_0",
            society_id=prediction.society_id,
            crop_type=prediction.crop_type,
            predicted_quantity_kg=prediction.predicted_quantity_kg,
            confidence_score=0.0,
            prediction_date=prediction.prediction_date,
            delivery_date=prediction.delivery_date,
            based_on_orders=prediction.based_on_orders,
            status=prediction.status,
        )
        assert prediction_zero_confidence.confidence_score == 0.0
        
        # Test confidence = 1.0
        prediction_full_confidence = DemandPrediction(
            prediction_id=prediction.prediction_id + "_1",
            society_id=prediction.society_id,
            crop_type=prediction.crop_type,
            predicted_quantity_kg=prediction.predicted_quantity_kg,
            confidence_score=1.0,
            prediction_date=prediction.prediction_date,
            delivery_date=prediction.delivery_date,
            based_on_orders=prediction.based_on_orders,
            status=prediction.status,
        )
        assert prediction_full_confidence.confidence_score == 1.0
    
    @given(demand_prediction_strategy())
    @settings(max_examples=100, deadline=None)
    def test_prediction_serialization_preserves_bounds(self, prediction: DemandPrediction):
        """
        Test that serialization and deserialization preserve bounds.
        
        **Validates: Requirements 3.1**
        """
        # Serialize to dict
        prediction_dict = prediction.to_dict()
        
        # Deserialize from dict
        restored_prediction = DemandPrediction.from_dict(prediction_dict)
        
        # Verify bounds are still valid
        assert restored_prediction.predicted_quantity_kg >= 0
        assert 0.0 <= restored_prediction.confidence_score <= 1.0
        
        # Verify values match
        assert restored_prediction.predicted_quantity_kg == prediction.predicted_quantity_kg
        assert restored_prediction.confidence_score == prediction.confidence_score
    
    @given(
        st.lists(demand_prediction_strategy(), min_size=1, max_size=50)
    )
    @settings(max_examples=100, deadline=None)
    def test_multiple_predictions_all_satisfy_bounds(self, predictions: list):
        """
        Test that all predictions in a batch satisfy bounds.
        
        **Validates: Requirements 3.1**
        """
        for prediction in predictions:
            # Every prediction must satisfy bounds
            assert prediction.predicted_quantity_kg >= 0, (
                f"Prediction {prediction.prediction_id} has negative quantity"
            )
            assert 0.0 <= prediction.confidence_score <= 1.0, (
                f"Prediction {prediction.prediction_id} has invalid confidence score"
            )
    
    @given(
        st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"))),
        st.sampled_from(["tomato", "onion", "potato"]),
        st.lists(
            st.tuples(
                st.decimals(min_value=Decimal("0"), max_value=Decimal("500"), places=2),
                st.floats(min_value=0.0, max_value=1.0)
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100, deadline=None)
    def test_prediction_sequence_maintains_bounds(
        self, 
        society_id: str, 
        crop_type: str, 
        prediction_data: list
    ):
        """
        Test that a sequence of predictions for the same society all maintain bounds.
        
        This simulates updating predictions over time.
        
        **Validates: Requirements 3.1**
        """
        predictions = []
        
        for i, (quantity, confidence) in enumerate(prediction_data):
            prediction = DemandPrediction(
                prediction_id=f"pred_{i}",
                society_id=society_id,
                crop_type=crop_type,
                predicted_quantity_kg=quantity,
                confidence_score=confidence,
                prediction_date=datetime.now(),
                delivery_date=date.today() + timedelta(days=7 + i),
                based_on_orders=i,
                status=ReservationStatus.PREDICTED,
            )
            predictions.append(prediction)
            
            # Verify each prediction satisfies bounds
            assert prediction.predicted_quantity_kg >= 0
            assert 0.0 <= prediction.confidence_score <= 1.0
        
        # Verify all predictions in the sequence satisfy bounds
        for prediction in predictions:
            assert prediction.predicted_quantity_kg >= 0
            assert 0.0 <= prediction.confidence_score <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
