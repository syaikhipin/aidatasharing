"""
Code execution service that captures plotly visualizations and matplotlib charts.
Based on Auto-Analyst's format_response.py approach.
"""

import sys
import contextlib
from io import StringIO
import json
import re
import logging
import pandas as pd
import numpy as np
import base64
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

@contextlib.contextmanager
def stdoutIO(stdout=None):
    """Context manager to capture stdout."""
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

class CodeExecutionService:
    """Service for safely executing agent-generated code and capturing visualizations."""

    def __init__(self):
        self.json_outputs = []
        self.matplotlib_outputs = []

    def execute_agent_code(self, code: str, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent-generated code and capture plotly visualizations.

        Args:
            code: Python code to execute
            dataset_info: Information about the dataset

        Returns:
            Dictionary containing execution results, plotly figures, and output
        """
        try:
            # Reset outputs
            self.json_outputs = []
            self.matplotlib_outputs = []

            # Prepare execution context
            context = self._prepare_execution_context(dataset_info)

            # Modify code to capture plotly figures
            modified_code = self._modify_code_for_capture(code)

            # Execute the code
            output_text = ""
            with stdoutIO() as s:
                try:
                    exec(modified_code, context)
                    output_text = s.getvalue()
                except Exception as e:
                    output_text = f"Execution error: {str(e)}"
                    logger.error(f"Code execution error: {str(e)}")

            # Extract captured visualizations
            json_outputs = context.get('json_outputs', [])
            matplotlib_outputs = context.get('matplotlib_outputs', [])

            return {
                "success": True,
                "output": output_text,
                "plotly_figures": json_outputs,
                "matplotlib_figures": matplotlib_outputs,
                "code": code
            }

        except Exception as e:
            logger.error(f"Code execution service error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "output": "",
                "plotly_figures": [],
                "matplotlib_figures": [],
                "code": code
            }

    def _prepare_execution_context(self, dataset_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare the execution context with necessary imports and data."""
        # Import necessary libraries
        import plotly.express as px
        import plotly.graph_objects as go
        import plotly
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np

        # Create mock dataset if needed (for demonstration)
        df = self._create_mock_dataset(dataset_info)

        # Lists to store captured outputs
        json_outputs = []
        matplotlib_outputs = []

        # Custom matplotlib capture function
        def capture_matplotlib_chart():
            """Capture current matplotlib figure as base64 encoded image"""
            try:
                fig = plt.gcf()  # Get current figure
                if fig.get_axes():  # Check if figure has any plots
                    buffer = StringIO()
                    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight',
                               facecolor='white', edgecolor='none')
                    buffer.seek(0)
                    image_base64 = base64.b64encode(buffer.getvalue().encode()).decode()
                    plt.close(fig)  # Close the figure to free memory
                    return image_base64
            except Exception as e:
                logger.error(f"Error capturing matplotlib chart: {str(e)}")
            return None

        # Custom plt.show that captures the chart instead of displaying it
        def custom_plt_show():
            """Custom plt.show that captures the chart instead of displaying it"""
            img_base64 = capture_matplotlib_chart()
            if img_base64:
                matplotlib_outputs.append(img_base64)

        # Prepare execution context
        context = {
            'pd': pd,
            'np': np,
            'px': px,
            'go': go,
            'plt': plt,
            'plotly': plotly,
            'df': df,
            'json_outputs': json_outputs,
            'matplotlib_outputs': matplotlib_outputs,
        }

        # Override plt.show to capture charts
        context['plt'].show = custom_plt_show

        return context

    def _modify_code_for_capture(self, code: str) -> str:
        """Modify code to capture plotly figures when fig.show() is called."""
        # Replace fig.show() with code that captures the figure as JSON
        modified_code = re.sub(
            r'(\w*_?)fig(\w*)\.show\(\)',
            r'json_outputs.append(plotly.io.to_json(\1fig\2, pretty=True))',
            code
        )

        # Also handle fig.to_html() calls
        modified_code = re.sub(
            r'(\w*_?)fig(\w*)\.to_html\(.*?\)',
            r'json_outputs.append(plotly.io.to_json(\1fig\2, pretty=True))',
            modified_code
        )

        # Ensure plotly import is present
        if 'import plotly' not in modified_code and ('px.' in code or 'go.' in code):
            modified_code = "import plotly.io\nimport plotly.express as px\nimport plotly.graph_objects as go\n" + modified_code

        return modified_code

    def _create_mock_dataset(self, dataset_info: Dict[str, Any]) -> pd.DataFrame:
        """Create a mock dataset for demonstration purposes."""
        try:
            # Try to extract column information from dataset_info
            if isinstance(dataset_info, dict) and 'columns' in dataset_info:
                columns = dataset_info['columns']
                if isinstance(columns, list):
                    # Create sample data with these columns
                    data = {}
                    for col in columns[:10]:  # Limit to 10 columns
                        # Use exact column names (lowercase)
                        col_lower = str(col).lower() if not str(col).islower() else col

                        if any(word in col_lower for word in ['price', 'cost', 'amount', 'value', 'sales', 'salary']):
                            # Numeric column
                            data[col_lower] = np.random.uniform(10000, 100000, 100)
                        elif any(word in col_lower for word in ['age']):
                            # Age column
                            data[col_lower] = np.random.randint(22, 65, 100)
                        elif any(word in col_lower for word in ['date', 'time']):
                            # Date column
                            data[col_lower] = pd.date_range('2023-01-01', periods=100, freq='D')
                        elif any(word in col_lower for word in ['name', 'first', 'last']):
                            # Name column
                            names = [f"Person_{i}" for i in range(100)]
                            data[col_lower] = names
                        elif any(word in col_lower for word in ['category', 'type', 'region', 'segment', 'department', 'dept']):
                            # Categorical column
                            categories = ['Sales', 'Engineering', 'Marketing', 'HR', 'Finance']
                            data[col_lower] = np.random.choice(categories, 100)
                        else:
                            # Default numeric
                            data[col_lower] = np.random.uniform(1, 100, 100)

                    return pd.DataFrame(data)

            # Default fallback dataset
            return pd.DataFrame({
                'Category': np.random.choice(['A', 'B', 'C', 'D'], 100),
                'Values': np.random.uniform(10, 100, 100),
                'Price': np.random.uniform(20, 200, 100),
                'Sales': np.random.uniform(100, 1000, 100),
                'Date': pd.date_range('2023-01-01', periods=100, freq='D')
            })

        except Exception as e:
            logger.error(f"Error creating mock dataset: {str(e)}")
            # Very basic fallback
            return pd.DataFrame({
                'x': range(10),
                'y': np.random.uniform(0, 10, 10)
            })

    def format_plotly_figures_for_frontend(self, plotly_figures: List[str]) -> List[Dict[str, Any]]:
        """Format plotly figures for frontend display."""
        formatted_figures = []

        for fig_json in plotly_figures:
            try:
                # Parse the JSON
                fig_data = json.loads(fig_json)

                # Format for frontend
                formatted_figures.append({
                    "type": "plotly",
                    "data": fig_data.get("data", []),
                    "layout": fig_data.get("layout", {}),
                    "config": {"displayModeBar": True, "responsive": True}
                })

            except json.JSONDecodeError as e:
                logger.error(f"Error parsing plotly JSON: {str(e)}")
                continue

        return formatted_figures

    def format_matplotlib_figures_for_frontend(self, matplotlib_figures: List[str]) -> List[Dict[str, Any]]:
        """Format matplotlib figures for frontend display."""
        formatted_figures = []

        for img_base64 in matplotlib_figures:
            formatted_figures.append({
                "type": "matplotlib",
                "image": img_base64,
                "format": "png"
            })

        return formatted_figures