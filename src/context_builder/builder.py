"""
Context Builder for SolidWorks MCP

Builds comprehensive context for AI prompts by extracting relevant
information from SolidWorks models and operations.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from ..solidworks_adapters.common.base_adapter import SolidWorksAdapter
from .knowledge_base import SolidWorksKnowledgeBase
from ..events.event_manager import EventManager

logger = logging.getLogger(__name__)


class SolidWorksContextBuilder:
    """Builds context for AI prompts from SolidWorks data"""

    def __init__(
        self, 
        knowledge_base: Optional[SolidWorksKnowledgeBase] = None,
        event_manager: Optional[EventManager] = None
    ):
        self.knowledge_base = knowledge_base or SolidWorksKnowledgeBase()
        self.event_manager = event_manager
        self.context_cache = {}

    async def build_context(
        self,
        adapter: Optional[SolidWorksAdapter],
        prompt_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """
        Build context for a specific prompt
        
        Args:
            adapter: SolidWorks adapter instance
            prompt_name: Name of the prompt
            arguments: Prompt arguments
            
        Returns:
            Context string for the AI
        """
        context_parts = []
        
        # Add prompt-specific header
        context_parts.append(self._get_prompt_header(prompt_name))
        
        # Add current model context if adapter available
        if adapter and adapter.connected:
            model_context = await self._build_model_context(adapter)
            if model_context:
                context_parts.append("## Current Model Context\n" + model_context)
        
        # Add relevant knowledge from database
        knowledge_context = await self._build_knowledge_context(prompt_name, arguments)
        if knowledge_context:
            context_parts.append("## Relevant Knowledge\n" + knowledge_context)
        
        # Add recent events if available
        if self.event_manager:
            events_context = self._build_events_context()
            if events_context:
                context_parts.append("## Recent Events\n" + events_context)
        
        # Add prompt-specific context
        specific_context = await self._build_specific_context(prompt_name, arguments, adapter)
        if specific_context:
            context_parts.append("## Specific Context\n" + specific_context)
        
        # Add user arguments
        context_parts.append("## User Request\n" + json.dumps(arguments, indent=2))
        
        # Combine all context parts
        full_context = "\n\n".join(context_parts)
        
        # Cache the context
        cache_key = f"{prompt_name}_{json.dumps(arguments, sort_keys=True)}"
        self.context_cache[cache_key] = {
            "context": full_context,
            "timestamp": datetime.now().isoformat()
        }
        
        return full_context

    async def _build_model_context(self, adapter: SolidWorksAdapter) -> str:
        """Build context from current model"""
        try:
            # Get model info
            model_info = await adapter.get_model_info()
            
            # Get features
            features = await adapter.get_features()
            feature_summary = self._summarize_features(features)
            
            # Get configurations
            configs = await adapter.get_configurations()
            
            # Get mass properties if available
            mass_props = {}
            try:
                mass_props = await adapter.get_mass_properties()
            except:
                pass
            
            context = f"""
Model: {model_info.get('title', 'Unknown')}
Type: {model_info.get('type', 'Unknown')}
Path: {model_info.get('path', 'Unknown')}

Features Summary:
{feature_summary}

Configurations: {', '.join([c.get('name', '') for c in configs])}
Active Configuration: {model_info.get('activeConfigurationName', 'Default')}
"""
            
            if mass_props:
                context += f"""
Mass Properties:
- Mass: {mass_props.get('mass', 0):.3f} kg
- Volume: {mass_props.get('volume', 0):.6f} m³
- Surface Area: {mass_props.get('surface_area', 0):.4f} m²
"""
            
            # Add custom properties if available
            custom_props = model_info.get('customProperties', {})
            if custom_props:
                context += "\nCustom Properties:\n"
                for key, value in custom_props.items():
                    context += f"- {key}: {value}\n"
            
            return context.strip()
            
        except Exception as e:
            logger.error(f"Error building model context: {e}")
            return "Unable to retrieve current model context"

    async def _build_knowledge_context(
        self, 
        prompt_name: str, 
        arguments: Dict[str, Any]
    ) -> str:
        """Build context from knowledge base"""
        context_parts = []
        
        # Find similar operations
        if prompt_name in ["analyze_model", "optimize_design"]:
            query = f"{prompt_name} {json.dumps(arguments)}"
            similar_ops = await self.knowledge_base.find_similar_operations(query, n_results=3)
            
            if similar_ops:
                context_parts.append("### Similar Previous Operations:")
                for op in similar_ops:
                    context_parts.append(
                        f"- {op['operation']}: {op.get('result', {}).get('summary', 'Completed')}"
                    )
        
        # Find relevant design patterns
        if prompt_name == "optimize_design":
            goal = arguments.get("optimization_goal", "")
            patterns = await self.knowledge_base.find_design_patterns(goal, n_results=3)
            
            if patterns:
                context_parts.append("\n### Relevant Design Patterns:")
                for pattern in patterns:
                    context_parts.append(
                        f"- {pattern['name']}: {pattern['description']}"
                    )
        
        # Find error solutions if there were recent errors
        if self.event_manager:
            recent_errors = self.event_manager.get_event_history("error", limit=1)
            if recent_errors:
                error_msg = recent_errors[0]["data"].get("message", "")
                solutions = await self.knowledge_base.find_error_solutions(error_msg)
                
                if solutions:
                    context_parts.append("\n### Potential Solutions for Recent Errors:")
                    for solution in solutions:
                        context_parts.append(f"- {solution['solution']}")
        
        return "\n".join(context_parts)

    def _build_events_context(self) -> str:
        """Build context from recent events"""
        if not self.event_manager:
            return ""
        
        # Get recent events
        recent_events = self.event_manager.get_event_history(limit=10)
        
        if not recent_events:
            return ""
        
        context_parts = ["Recent actions and events:"]
        
        for event in recent_events[-5:]:  # Last 5 events
            event_type = event["type"]
            event_data = event["data"]
            timestamp = event["timestamp"]
            
            # Format event description
            if event_type == "dimension_changed":
                desc = f"Dimension {event_data.get('dimension')} changed from {event_data.get('old_value')} to {event_data.get('new_value')}"
            elif event_type == "feature_added":
                desc = f"Added feature: {event_data.get('name')} ({event_data.get('type')})"
            elif event_type == "rebuild_completed":
                desc = f"Model rebuilt successfully in {event_data.get('duration', 0):.2f}s"
            else:
                desc = f"{event_type}: {json.dumps(event_data)}"
            
            context_parts.append(f"- {desc}")
        
        # Add event statistics
        stats = self.event_manager.get_event_statistics()
        context_parts.append(f"\nEvent statistics: {stats['total_events']} total events")
        
        return "\n".join(context_parts)

    async def _build_specific_context(
        self, 
        prompt_name: str, 
        arguments: Dict[str, Any],
        adapter: Optional[SolidWorksAdapter]
    ) -> str:
        """Build prompt-specific context"""
        
        if prompt_name == "analyze_model":
            # Add analysis-specific context
            return await self._build_analysis_context(arguments, adapter)
        
        elif prompt_name == "optimize_design":
            # Add optimization-specific context
            return await self._build_optimization_context(arguments, adapter)
        
        elif prompt_name == "create_variants":
            # Add variant-specific context
            return await self._build_variants_context(arguments, adapter)
        
        return ""

    async def _build_analysis_context(
        self, 
        arguments: Dict[str, Any], 
        adapter: Optional[SolidWorksAdapter]
    ) -> str:
        """Build context for model analysis"""
        context_parts = []
        
        # Add file type specific guidance
        file_path = arguments.get("file_path", "")
        if file_path:
            ext = Path(file_path).suffix.lower()
            if ext == ".sldprt":
                context_parts.append("Analyzing a part file - focus on geometry, features, and manufacturability")
            elif ext == ".sldasm":
                context_parts.append("Analyzing an assembly - focus on component relationships, mates, and interference")
            elif ext == ".slddrw":
                context_parts.append("Analyzing a drawing - focus on views, dimensions, and annotations")
        
        # Add analysis checklist
        context_parts.append("\nAnalysis should cover:")
        context_parts.append("- Design intent and parametric relationships")
        context_parts.append("- Potential manufacturing issues")
        context_parts.append("- Best practices compliance")
        context_parts.append("- Performance considerations")
        context_parts.append("- Cost reduction opportunities")
        
        return "\n".join(context_parts)

    async def _build_optimization_context(
        self, 
        arguments: Dict[str, Any], 
        adapter: Optional[SolidWorksAdapter]
    ) -> str:
        """Build context for design optimization"""
        goal = arguments.get("optimization_goal", "general optimization")
        
        context = f"Optimization Goal: {goal}\n\n"
        
        # Add goal-specific guidance
        if "weight" in goal.lower():
            context += """Weight Optimization Strategies:
- Material removal in low-stress areas
- Topology optimization
- Lattice structures
- Thin-wall design
- Material substitution
"""
        elif "cost" in goal.lower():
            context += """Cost Optimization Strategies:
- Simplify geometry
- Reduce part count
- Standardize components
- Optimize for manufacturing processes
- Minimize material waste
"""
        elif "strength" in goal.lower():
            context += """Strength Optimization Strategies:
- Add reinforcement ribs
- Optimize wall thickness
- Improve stress distribution
- Eliminate stress concentrations
- Consider material properties
"""
        
        return context

    async def _build_variants_context(
        self, 
        arguments: Dict[str, Any], 
        adapter: Optional[SolidWorksAdapter]
    ) -> str:
        """Build context for creating design variants"""
        parameters = arguments.get("parameters", [])
        count = arguments.get("count", 5)
        
        context = f"Creating {count} design variants\n"
        context += f"Variable parameters: {', '.join(parameters)}\n\n"
        
        # Add parameter ranges if available from model
        if adapter and adapter.connected:
            features = await adapter.get_features()
            
            context += "Current parameter values:\n"
            for feature in features:
                for dim in feature.get("dimensions", []):
                    if dim["name"] in parameters:
                        context += f"- {dim['name']}: {dim['value']}\n"
        
        context += "\nVariant generation strategies:\n"
        context += "- Use Design of Experiments (DOE) approach\n"
        context += "- Consider parameter interactions\n"
        context += "- Maintain design constraints\n"
        context += "- Focus on meaningful variations\n"
        
        return context

    def _summarize_features(self, features: List[Dict[str, Any]]) -> str:
        """Summarize features for context"""
        if not features:
            return "No features found"
        
        # Count feature types
        feature_types = {}
        suppressed_count = 0
        
        for feature in features:
            ftype = feature.get("type", "Unknown")
            feature_types[ftype] = feature_types.get(ftype, 0) + 1
            
            if feature.get("suppressed", False):
                suppressed_count += 1
        
        summary_parts = [f"Total features: {len(features)}"]
        
        # Top feature types
        sorted_types = sorted(feature_types.items(), key=lambda x: x[1], reverse=True)
        summary_parts.append("Feature types:")
        for ftype, count in sorted_types[:5]:
            summary_parts.append(f"  - {ftype}: {count}")
        
        if suppressed_count > 0:
            summary_parts.append(f"Suppressed features: {suppressed_count}")
        
        return "\n".join(summary_parts)

    def _get_prompt_header(self, prompt_name: str) -> str:
        """Get header text for specific prompts"""
        headers = {
            "analyze_model": "# SolidWorks Model Analysis Request",
            "optimize_design": "# Design Optimization Request",
            "create_variants": "# Design Variant Generation Request",
        }
        
        return headers.get(prompt_name, f"# {prompt_name.replace('_', ' ').title()} Request")

    def get_cached_context(self, prompt_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        """Retrieve cached context if available and recent"""
        cache_key = f"{prompt_name}_{json.dumps(arguments, sort_keys=True)}"
        
        if cache_key in self.context_cache:
            cached = self.context_cache[cache_key]
            
            # Check if cache is recent (within 5 minutes)
            cached_time = datetime.fromisoformat(cached["timestamp"])
            if (datetime.now() - cached_time).seconds < 300:
                return cached["context"]
        
        return None

    def clear_cache(self):
        """Clear the context cache"""
        self.context_cache.clear()
        logger.info("Context cache cleared")