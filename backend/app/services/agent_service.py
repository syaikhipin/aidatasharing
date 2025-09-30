"""
Agent service for managing DSPy-based agents and dataset interactions.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.agents.base_agents import AgentOrchestrator, create_agent_orchestrator
from app.models.dataset import Dataset
from app.core.config import settings
from app.services.code_execution_service import CodeExecutionService

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing agents and their interactions with datasets."""

    def __init__(self, db: Session):
        self.db = db
        self.orchestrator = None
        self.code_execution_service = CodeExecutionService()
        self._initialize_orchestrator()

    def _initialize_orchestrator(self):
        """Initialize the agent orchestrator with LLM configuration."""
        try:
            # Configure LLM settings
            llm_config = {
                "provider": getattr(settings, "DEFAULT_LLM_PROVIDER", "openai"),
                "model": getattr(settings, "DEFAULT_LLM_MODEL", "gpt-3.5-turbo"),
                "api_key": getattr(settings, "OPENAI_API_KEY", None),
                "temperature": 0.1,
                "max_tokens": 2000
            }

            self.orchestrator = create_agent_orchestrator(llm_config)
            logger.info("Agent orchestrator initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize agent orchestrator: {str(e)}")
            self.orchestrator = None

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents with their descriptions."""
        return [
            {
                "name": "preprocessing_agent",
                "display_name": "Data Preprocessing",
                "description": "Cleans data using pandas and numpy. Fixes types, handles nulls, computes aggregates.",
                "icon": "🧹",
                "category": "Data Preparation"
            },
            {
                "name": "statistical_analytics_agent",
                "display_name": "Statistical Analysis",
                "description": "Performs regression, correlation, ANOVA, and other statistical tests with statsmodels.",
                "icon": "📊",
                "category": "Analysis"
            },
            {
                "name": "ml_agent",
                "display_name": "Machine Learning",
                "description": "Trains machine learning models like Random Forest, KMeans, Logistic Regression using scikit-learn.",
                "icon": "🤖",
                "category": "Machine Learning"
            },
            {
                "name": "data_viz_agent",
                "display_name": "Data Visualization",
                "description": "Generates visualizations using plotly. Includes smart chart format selection.",
                "icon": "📈",
                "category": "Visualization"
            }
        ]

    def chat_with_dataset(
        self,
        dataset_id: int,
        message: str,
        agent_name: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a chat message with dataset using agents.

        Args:
            dataset_id: ID of the dataset
            message: User's message/query
            agent_name: Optional specific agent (e.g., '@preprocessing_agent')
            user_id: Optional user ID for logging

        Returns:
            Dictionary containing agent response
        """
        try:
            if not self.orchestrator:
                raise Exception("Agent orchestrator not initialized")

            # Get dataset information
            dataset = self.db.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                raise Exception(f"Dataset {dataset_id} not found")

            # Prepare dataset information for agents
            dataset_info = self._prepare_dataset_info(dataset)

            # Route query to appropriate agent
            result = self.orchestrator.route_query(
                goal=message,
                dataset_info=dataset_info,
                agent_name=agent_name
            )

            # Execute code if agent generated code (especially for visualizations)
            execution_result = None
            plotly_figures = []
            matplotlib_figures = []

            if result.get("success") and result.get("code"):
                code = result.get("code", "")

                # Execute code with visualization capture
                execution_result = self.code_execution_service.execute_agent_code(
                    code=code,
                    dataset_info=self._prepare_dataset_info_dict(dataset)
                )

                if execution_result.get("success"):
                    # Format plotly figures for frontend
                    if execution_result.get("plotly_figures"):
                        plotly_figures = self.code_execution_service.format_plotly_figures_for_frontend(
                            execution_result["plotly_figures"]
                        )

                    # Format matplotlib figures for frontend
                    if execution_result.get("matplotlib_figures"):
                        matplotlib_figures = self.code_execution_service.format_matplotlib_figures_for_frontend(
                            execution_result["matplotlib_figures"]
                        )

            # Log the interaction
            self._log_agent_interaction(
                dataset_id=dataset_id,
                user_id=user_id,
                message=message,
                agent_name=result.get("agent"),
                response=result,
                success=result.get("success", False)
            )

            return {
                "success": result.get("success", False),
                "response": result.get("summary", ""),
                "code": result.get("code", ""),
                "agent": result.get("agent"),
                "planner": result.get("planner"),
                "timestamp": result.get("timestamp"),
                "error": result.get("error"),
                "execution_output": execution_result.get("output") if execution_result else None,
                "plotly_figures": plotly_figures,
                "matplotlib_figures": matplotlib_figures,
                "visualizations": plotly_figures + matplotlib_figures  # Combined for easy frontend access
            }

        except Exception as e:
            logger.error(f"Agent chat failed for dataset {dataset_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": f"Failed to process request: {str(e)}"
            }

    def _prepare_dataset_info(self, dataset: Dataset) -> str:
        """Prepare dataset information for agents."""
        try:
            dataset_info = {
                "name": dataset.name,
                "description": dataset.description or "No description provided",
                "file_type": dataset.file_type,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "row_count": dataset.row_count if hasattr(dataset, 'row_count') else None,
                "column_count": dataset.column_count if hasattr(dataset, 'column_count') else None
            }

            # Try to get columns from various sources
            columns = None

            # Try schema_metadata first
            if hasattr(dataset, 'schema_metadata') and dataset.schema_metadata:
                if isinstance(dataset.schema_metadata, dict):
                    columns = dataset.schema_metadata.get('columns')
                elif isinstance(dataset.schema_metadata, str):
                    try:
                        schema_meta = json.loads(dataset.schema_metadata)
                        columns = schema_meta.get('columns')
                    except:
                        pass

            # Try metadata next
            if not columns and hasattr(dataset, 'metadata') and dataset.metadata:
                if isinstance(dataset.metadata, dict):
                    columns = dataset.metadata.get('columns')
                elif isinstance(dataset.metadata, str):
                    try:
                        metadata = json.loads(dataset.metadata)
                        columns = metadata.get('columns')
                    except:
                        pass

            # Format as string for agents
            info_string = f"""Dataset: {dataset_info['name']}"""

            if dataset_info['description']:
                info_string += f"\nDescription: {dataset_info['description']}"

            if dataset_info['row_count']:
                info_string += f"\nRows: {dataset_info['row_count']}"

            if dataset_info['column_count']:
                info_string += f"\nColumn Count: {dataset_info['column_count']}"

            # Add column information if available
            if columns:
                if isinstance(columns, list):
                    # Make sure columns are lowercase for consistency
                    columns_lower = [str(col).lower() if not str(col).islower() else col for col in columns]
                    info_string += f"\nColumns (use exact names): {', '.join(columns_lower)}"
                elif isinstance(columns, dict):
                    info_string += "\nColumns with types:\n"
                    for col, dtype in columns.items():
                        col_lower = str(col).lower() if not str(col).islower() else col
                        info_string += f"  - {col_lower}: {dtype}\n"

            return info_string

        except Exception as e:
            logger.error(f"Error preparing dataset info: {str(e)}")
            return f"Dataset: {dataset.name}\nDescription: {dataset.description or 'No description'}"

    def _prepare_dataset_info_dict(self, dataset: Dataset) -> Dict[str, Any]:
        """Prepare dataset information as dictionary for code execution service."""
        try:
            dataset_info = {
                "name": dataset.name,
                "description": dataset.description or "No description provided",
                "file_type": dataset.file_type,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None
            }

            # Add metadata if available
            if hasattr(dataset, 'metadata') and dataset.metadata:
                if isinstance(dataset.metadata, dict):
                    dataset_info.update(dataset.metadata)
                elif isinstance(dataset.metadata, str):
                    try:
                        metadata = json.loads(dataset.metadata)
                        dataset_info.update(metadata)
                    except:
                        pass

            return dataset_info

        except Exception as e:
            logger.error(f"Error preparing dataset info dict: {str(e)}")
            return {
                "name": dataset.name,
                "description": dataset.description or "No description"
            }

    def _log_agent_interaction(
        self,
        dataset_id: int,
        user_id: Optional[int],
        message: str,
        agent_name: Optional[str],
        response: Dict[str, Any],
        success: bool
    ):
        """Log agent interaction for analytics."""
        try:
            # You can implement logging to database or external service here
            logger.info(f"Agent interaction: dataset={dataset_id}, agent={agent_name}, success={success}")

            # Example: Save to analytics table if it exists
            # analytics_record = {
            #     "dataset_id": dataset_id,
            #     "user_id": user_id,
            #     "agent_name": agent_name,
            #     "message": message,
            #     "response_summary": response.get("summary", ""),
            #     "success": success,
            #     "timestamp": datetime.now()
            # }

        except Exception as e:
            logger.error(f"Failed to log agent interaction: {str(e)}")

    def execute_code_safely(self, code: str, dataset_id: int) -> Dict[str, Any]:
        """
        Execute generated code safely in a controlled environment.

        Note: This is a placeholder for code execution functionality.
        In production, you would want to use a sandboxed environment.
        """
        try:
            # This would typically execute in a sandboxed Python environment
            # For now, we'll just return the code for display
            return {
                "success": True,
                "code": code,
                "result": "Code execution would happen in a sandboxed environment",
                "output": "Generated code is ready for execution"
            }

        except Exception as e:
            logger.error(f"Code execution failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "code": code
            }

    def get_agent_templates(self) -> List[Dict[str, Any]]:
        """Get predefined agent templates for custom agent creation."""
        return [
            {
                "name": "custom_analysis_agent",
                "display_name": "Custom Analysis",
                "description": "Create custom analysis workflows",
                "template": """
                Analyze the dataset based on specific requirements:
                1. Examine the data structure and quality
                2. Perform requested analysis
                3. Generate appropriate visualizations
                4. Provide actionable insights
                """,
                "category": "Custom"
            },
            {
                "name": "reporting_agent",
                "display_name": "Report Generation",
                "description": "Generate comprehensive data reports",
                "template": """
                Generate a comprehensive report including:
                1. Data overview and summary statistics
                2. Key insights and patterns
                3. Visualizations and charts
                4. Recommendations and conclusions
                """,
                "category": "Reporting"
            }
        ]

def create_agent_service(db: Session) -> AgentService:
    """Factory function to create agent service."""
    return AgentService(db)