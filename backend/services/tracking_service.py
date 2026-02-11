import random
from typing import Dict, Optional

class TrackingService:
    """
    Service to fetch order tracking status from external providers.
    Currently implements a MOCK provider for demonstration.
    """
    
    def get_tracking_info(self, tracking_id: str, carrier: Optional[str] = None) -> Dict[str, str]:
        """
        Fetch tracking info for a given tracking ID.
        Returns a dictionary with status details.
        """
        if not tracking_id:
            return {}
            
        # MOCK IMPLEMENTATION
        # Simulate different states based on random or hash of ID
        
        mock_locations = ["Mumbai Hub", "Delhi Gateway", "Bangalore Center", "Local Delivery Facility"]
        mock_statuses = ["In Transit", "Out for Delivery", "Arrived at Facility", "Picked Up"]
        
        # Deterministic mock based on ID length to be consistent for same ID
        idx = len(tracking_id) % 4
        
        return {
            "tracking_id": tracking_id,
            "carrier": carrier or "Standard Shipping",
            "status": mock_statuses[idx],
            "location": mock_locations[idx],
            "eta": "2 days"
        }

# Singleton instance
tracking_service = TrackingService()
