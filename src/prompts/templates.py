"""
Prompt Templates for SolidWorks MCP

Pre-defined prompt templates for common SolidWorks operations.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Structure for prompt templates"""
    name: str
    description: str
    template: str
    required_context: List[str]
    optional_context: List[str]


class SolidWorksPromptTemplates:
    """Collection of prompt templates for SolidWorks operations"""

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize all prompt templates"""
        return {
            "analyze_model": PromptTemplate(
                name="analyze_model",
                description="Comprehensive model analysis",
                template="""
Analyze the following SolidWorks model and provide insights:

{context}

Please provide:
1. **Design Overview**: Brief description of the model's purpose and structure
2. **Key Features**: Important geometric features and their relationships
3. **Parametric Analysis**: How the model uses parameters and design intent
4. **Potential Issues**: Any design flaws, manufacturability concerns, or best practice violations
5. **Optimization Opportunities**: Suggestions for improvement
6. **Manufacturing Considerations**: How this design would be manufactured

Focus on practical, actionable insights that would help improve the design.
""",
                required_context=["model_info", "features"],
                optional_context=["mass_properties", "custom_properties", "configurations"]
            ),
            
            "optimize_design": PromptTemplate(
                name="optimize_design",
                description="Design optimization suggestions",
                template="""
Provide optimization recommendations for the current design:

{context}

Optimization Requirements:
- Primary Goal: {optimization_goal}
- Maintain functionality and design intent
- Consider manufacturing constraints
- Preserve critical dimensions

Please provide:
1. **Current State Analysis**: Assessment of the current design relative to the goal
2. **Specific Recommendations**: Numbered list of actionable changes
3. **Expected Improvements**: Quantified benefits where possible
4. **Implementation Steps**: How to apply each recommendation
5. **Trade-offs**: Any compromises or considerations

Prioritize recommendations by impact and ease of implementation.
""",
                required_context=["model_info", "optimization_goal"],
                optional_context=["features", "mass_properties", "similar_operations"]
            ),
            
            "create_variants": PromptTemplate(
                name="create_variants",
                description="Generate design variants",
                template="""
Generate design variants based on the following requirements:

{context}

Variant Generation Requirements:
- Parameters to vary: {parameters}
- Number of variants: {count}
- Maintain design constraints and functionality

For each variant, provide:
1. **Variant Name**: Descriptive identifier
2. **Parameter Values**: Specific values for each parameter
3. **Design Rationale**: Why this combination was chosen
4. **Expected Characteristics**: Key properties of this variant
5. **Use Case**: Best application for this variant

Ensure variants cover a meaningful design space while remaining practical.
""",
                required_context=["parameters", "count"],
                optional_context=["model_info", "features", "constraints"]
            ),
            
            "debug_error": PromptTemplate(
                name="debug_error",
                description="Debug SolidWorks errors",
                template="""
Help debug the following SolidWorks error:

{context}

Error Details:
{error_message}

Please provide:
1. **Error Analysis**: What this error means
2. **Root Cause**: Likely cause of the error
3. **Solution Steps**: Numbered steps to resolve the issue
4. **Prevention**: How to avoid this error in the future
5. **Alternative Approaches**: Other ways to achieve the goal

Focus on practical solutions that can be implemented immediately.
""",
                required_context=["error_message"],
                optional_context=["operation_context", "model_info", "recent_events"]
            ),
            
            "design_review": PromptTemplate(
                name="design_review",
                description="Comprehensive design review",
                template="""
Conduct a design review for the following SolidWorks model:

{context}

Review Criteria:
- Design intent and parametric robustness
- Manufacturing feasibility
- Assembly considerations
- Drawing completeness
- Best practices compliance
- Cost implications

Provide a structured review covering:
1. **Strengths**: What's done well
2. **Issues**: Problems that need addressing (severity: high/medium/low)
3. **Recommendations**: Specific improvements
4. **Compliance Check**: Standards and best practices
5. **Overall Assessment**: Summary and readiness evaluation

Be thorough but prioritize actionable feedback.
""",
                required_context=["model_info"],
                optional_context=["features", "configurations", "custom_properties", "mass_properties"]
            ),
            
            "generate_macro": PromptTemplate(
                name="generate_macro",
                description="Generate VBA macro code",
                template="""
Generate a VBA macro for SolidWorks to accomplish the following:

{context}

Macro Requirements:
- Task: {task_description}
- Target: {target_type} (part/assembly/drawing)
- Error handling: Include proper error handling
- User feedback: Provide status messages

Generate:
1. **Macro Code**: Complete VBA code with comments
2. **Usage Instructions**: How to install and run the macro
3. **Parameters**: Any variables that users might want to modify
4. **Limitations**: What the macro can and cannot do
5. **Extension Ideas**: How the macro could be enhanced

Ensure the code follows VBA best practices and SolidWorks API conventions.
""",
                required_context=["task_description", "target_type"],
                optional_context=["specific_requirements", "example_code"]
            ),
            
            "parametric_update": PromptTemplate(
                name="parametric_update",
                description="Guide parametric model updates",
                template="""
Guide the parametric update process for the following changes:

{context}

Update Requirements:
- Desired changes: {changes}
- Maintain design intent
- Preserve downstream features
- Update related drawings

Provide:
1. **Impact Analysis**: What will be affected by these changes
2. **Update Sequence**: Ordered steps to make the changes safely
3. **Parameter Relationships**: How parameters interact
4. **Validation Steps**: How to verify the updates
5. **Rollback Plan**: How to revert if needed

Focus on maintaining model integrity throughout the update process.
""",
                required_context=["changes"],
                optional_context=["model_info", "features", "configurations"]
            ),
            
            "bom_analysis": PromptTemplate(
                name="bom_analysis",
                description="Bill of Materials analysis",
                template="""
Analyze the Bill of Materials for the following assembly:

{context}

Analysis Requirements:
- Component count and types
- Material usage
- Standard vs custom parts
- Cost implications
- Supply chain considerations

Provide:
1. **BOM Summary**: Overview of components and quantities
2. **Optimization Opportunities**: Part consolidation, standardization
3. **Cost Drivers**: Most expensive components or materials
4. **Risk Analysis**: Single sources, long lead times
5. **Recommendations**: Specific improvements to reduce cost/complexity

Include both immediate and long-term optimization strategies.
""",
                required_context=["assembly_info"],
                optional_context=["components", "custom_properties", "materials"]
            )
        }

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a specific prompt template"""
        return self.templates.get(name)

    def list_templates(self) -> List[str]:
        """List all available template names"""
        return list(self.templates.keys())

    def format_template(
        self, 
        template_name: str, 
        context: str, 
        **kwargs
    ) -> str:
        """
        Format a template with context and parameters
        
        Args:
            template_name: Name of the template
            context: Context string
            **kwargs: Additional parameters for the template
            
        Returns:
            Formatted prompt string
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
        
        # Format the template
        prompt = template.template.format(context=context, **kwargs)
        
        return prompt

    def get_required_context(self, template_name: str) -> List[str]:
        """Get required context items for a template"""
        template = self.get_template(template_name)
        if template:
            return template.required_context
        return []

    def validate_context(
        self, 
        template_name: str, 
        provided_context: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that required context is provided
        
        Returns:
            Tuple of (is_valid, missing_items)
        """
        template = self.get_template(template_name)
        if not template:
            return False, ["Template not found"]
        
        missing = []
        for required in template.required_context:
            if required not in provided_context:
                missing.append(required)
        
        return len(missing) == 0, missing