"""
WebSocket Command Handler Registry Pattern
This provides a clean, scalable way to handle different message types via WebSocket
"""
from typing import Dict, Any
import json
from abc import ABC, abstractmethod
from database import record_telemetry_data

class CommandHandler(ABC):
    """Abstract base class for command handlers"""   
    @abstractmethod
    async def handle(self, data: Dict[str, Any], websocket) -> Dict[str, Any]:
        """Handle the command and return response"""
        pass
    
    @abstractmethod
    def get_command_name(self) -> str:
        """Return the command name this handler responds to"""
        pass

class SetFlightModeHandler(CommandHandler):
    def get_command_name(self) -> str:
        return "set_flight_mode"
    
    async def handle(self, data: Dict[str, Any], websocket) -> Dict[str, Any]:
        mode = data.get("mode")
        print(f"Setting flight mode to: {mode}")
        # Pass flight mode to flight computer to set mode
        return {"status": "success", "mode": mode}

class SetFollowDistanceHandler(CommandHandler):
    def get_command_name(self) -> str:
        return "set_follow_distance"
    
    async def handle(self, data: Dict[str, Any], websocket) -> Dict[str, Any]:
        distance = data.get("distance")
        print(f"Setting follow distance to: {distance} meters")
        # Pass distance to flight computer to set follow distance
        return {"status": "success", "distance": distance}

class RecordDataHandler(CommandHandler):
    def get_command_name(self) -> str:
        return "record"
    
    async def handle(self, data: Dict[str, Any], websocket) -> Dict[str, Any]:
        try:
            result = record_telemetry_data(data)
            return {
                "status": "success", 
                "objectID": result['objectID'],
                "recorded_points": result['recorded_points']
            }
        except Exception as e:
            print(f"Error storing recording data: {e}")
            return {"status": "error", "error": str(e)}

class CommandRegistry:
    """Registry for WebSocket command handlers"""
    
    def __init__(self):
        self.handlers: Dict[str, CommandHandler] = {}
    
    def register_handler(self, handler: CommandHandler):
        """Register a command handler"""
        command_name = handler.get_command_name()
        self.handlers[command_name] = handler
        print(f"Registered handler for command: {command_name}")
    
    async def handle_message(self, message: str, websocket) -> Dict[str, Any]:
        """Handle incoming WebSocket message"""
        try:
            data = json.loads(message)
            command = data.get("command")          
            if not command:
                return {"error": "No command specified", "status": "error"}
            
            handler = self.handlers.get(command)
            if not handler:
                return {"error": f"Unknown command: {command}", "status": "error"}
            
            # Handle the command
            return await handler.handle(data.get("data", {}), websocket)       
            
        except json.JSONDecodeError:
            return {"error": "Invalid JSON", "status": "error"}
        except Exception as e:
            return {"error": str(e), "status": "error"}

# Usage in your server
def setup_command_registry() -> CommandRegistry:
    """Set up the command registry with all handlers"""
    registry = CommandRegistry()
    
    # Register all handlers
    registry.register_handler(SetFlightModeHandler())
    registry.register_handler(SetFollowDistanceHandler())
    registry.register_handler(RecordDataHandler())
    
    return registry