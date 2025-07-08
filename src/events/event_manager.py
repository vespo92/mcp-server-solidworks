"""
Event Manager for SolidWorks

Captures and processes SolidWorks events to provide real-time context
and enable reactive automation.
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from collections import deque
import json

logger = logging.getLogger(__name__)


class EventManager:
    """Manages SolidWorks event capture and processing"""

    def __init__(self, max_history: int = 1000):
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.event_history = deque(maxlen=max_history)
        self.active_listeners = {}
        self._running = False
        self._event_queue = asyncio.Queue()

    async def start(self):
        """Start the event processing loop"""
        self._running = True
        asyncio.create_task(self._process_events())
        logger.info("Event manager started")

    async def stop(self):
        """Stop the event processing loop"""
        self._running = False
        logger.info("Event manager stopped")

    async def cleanup(self):
        """Clean up resources"""
        await self.stop()
        self.event_handlers.clear()
        self.active_listeners.clear()

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an event handler
        
        Args:
            event_type: Type of event to handle
            handler: Async callable to handle the event
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event type: {event_type}")

    def unregister_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)

    async def emit_event(self, event_type: str, data: Dict[str, Any]):
        """
        Emit an event
        
        Args:
            event_type: Type of event
            data: Event data
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "id": f"{event_type}_{datetime.now().timestamp()}"
        }
        
        # Add to queue for processing
        await self._event_queue.put(event)
        
        # Add to history
        self.event_history.append(event)
        
        logger.debug(f"Event emitted: {event_type}")

    async def _process_events(self):
        """Process events from the queue"""
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                event_type = event["type"]
                
                # Call all registered handlers for this event type
                if event_type in self.event_handlers:
                    for handler in self.event_handlers[event_type]:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(f"Error in event handler: {e}")
                
                # Call wildcard handlers
                if "*" in self.event_handlers:
                    for handler in self.event_handlers["*"]:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.error(f"Error in wildcard handler: {e}")
                            
            except asyncio.TimeoutError:
                # No events to process, continue
                continue
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    def get_event_history(
        self, 
        event_type: Optional[str] = None, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get event history
        
        Args:
            event_type: Filter by event type (optional)
            limit: Maximum number of events to return
            
        Returns:
            List of events
        """
        if event_type:
            filtered = [e for e in self.event_history if e["type"] == event_type]
            return list(filtered)[-limit:]
        else:
            return list(self.event_history)[-limit:]

    def get_event_statistics(self) -> Dict[str, Any]:
        """Get statistics about captured events"""
        stats = {
            "total_events": len(self.event_history),
            "event_types": {},
            "events_per_minute": 0,
            "most_recent_event": None
        }
        
        # Count event types
        for event in self.event_history:
            event_type = event["type"]
            stats["event_types"][event_type] = stats["event_types"].get(event_type, 0) + 1
        
        # Calculate events per minute
        if self.event_history:
            oldest = datetime.fromisoformat(self.event_history[0]["timestamp"])
            newest = datetime.fromisoformat(self.event_history[-1]["timestamp"])
            duration_minutes = (newest - oldest).total_seconds() / 60
            
            if duration_minutes > 0:
                stats["events_per_minute"] = len(self.event_history) / duration_minutes
            
            stats["most_recent_event"] = self.event_history[-1]
        
        return stats

    async def wait_for_event(
        self, 
        event_type: str, 
        timeout: Optional[float] = None,
        condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Wait for a specific event to occur
        
        Args:
            event_type: Type of event to wait for
            timeout: Maximum time to wait (seconds)
            condition: Optional condition function to filter events
            
        Returns:
            Event data or None if timeout
        """
        future = asyncio.Future()
        
        async def handler(event):
            if event["type"] == event_type:
                if condition is None or condition(event):
                    future.set_result(event)
        
        self.register_handler(event_type, handler)
        
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return None
        finally:
            self.unregister_handler(event_type, handler)

    def export_events(self, output_path: str):
        """Export event history to a file"""
        events = list(self.event_history)
        
        with open(output_path, 'w') as f:
            json.dump(events, f, indent=2)
        
        logger.info(f"Exported {len(events)} events to {output_path}")


class SolidWorksEventListener:
    """Listens for SolidWorks application events"""

    def __init__(self, event_manager: EventManager):
        self.event_manager = event_manager
        self.connected = False

    async def connect(self, sw_app):
        """Connect to SolidWorks event stream"""
        # This would typically use COM events or similar mechanism
        # For now, we'll simulate with common events
        self.connected = True
        logger.info("Connected to SolidWorks event stream")

    async def disconnect(self):
        """Disconnect from SolidWorks events"""
        self.connected = False
        logger.info("Disconnected from SolidWorks event stream")

    async def simulate_events(self):
        """Simulate SolidWorks events for testing"""
        event_types = [
            ("model_opened", {"file": "test.sldprt", "type": "part"}),
            ("feature_added", {"name": "Extrude1", "type": "extrusion"}),
            ("dimension_changed", {"feature": "Extrude1", "dimension": "D1", "old_value": 10, "new_value": 15}),
            ("rebuild_started", {"model": "test.sldprt"}),
            ("rebuild_completed", {"model": "test.sldprt", "success": True, "duration": 1.2}),
            ("configuration_activated", {"name": "Config2"}),
            ("file_saved", {"path": "C:/Models/test.sldprt"}),
        ]
        
        for event_type, data in event_types:
            await self.event_manager.emit_event(event_type, data)
            await asyncio.sleep(0.5)  # Simulate time between events


# Common event types for SolidWorks
class SolidWorksEventTypes:
    """Standard SolidWorks event types"""
    
    # Document events
    MODEL_OPENED = "model_opened"
    MODEL_CLOSED = "model_closed"
    MODEL_SAVED = "model_saved"
    MODEL_ACTIVATED = "model_activated"
    
    # Feature events
    FEATURE_ADDED = "feature_added"
    FEATURE_DELETED = "feature_deleted"
    FEATURE_MODIFIED = "feature_modified"
    FEATURE_SUPPRESSED = "feature_suppressed"
    FEATURE_UNSUPPRESSED = "feature_unsuppressed"
    
    # Dimension events
    DIMENSION_CHANGED = "dimension_changed"
    
    # Rebuild events
    REBUILD_STARTED = "rebuild_started"
    REBUILD_COMPLETED = "rebuild_completed"
    REBUILD_FAILED = "rebuild_failed"
    
    # Configuration events
    CONFIGURATION_ACTIVATED = "configuration_activated"
    CONFIGURATION_ADDED = "configuration_added"
    CONFIGURATION_DELETED = "configuration_deleted"
    
    # Design table events
    DESIGN_TABLE_UPDATED = "design_table_updated"
    
    # Selection events
    SELECTION_CHANGED = "selection_changed"
    
    # View events
    VIEW_ROTATED = "view_rotated"
    VIEW_ZOOMED = "view_zoomed"
    VIEW_PANNED = "view_panned"
    
    # Macro events
    MACRO_STARTED = "macro_started"
    MACRO_COMPLETED = "macro_completed"
    MACRO_FAILED = "macro_failed"