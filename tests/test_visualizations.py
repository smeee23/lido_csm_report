import unittest
from unittest.mock import patch, MagicMock, call
import matplotlib.pyplot as plt
import seaborn as sns
from src.visualizations import (
    plot_histogram, 
    plot_line,
    get_average_ratings_for_dates,
    format_title,
    format_label,
    create_output_file
)

class TestPlottingFunctions(unittest.TestCase):
    
    def setUp(self):
        self.test_data = {
            "2024-12-31": {
                "Operator 1 - Lido Community Staking Module": {"rating": 5},
                "Operator 2 - Lido Community Staking Module": {"rating": 3},
                "Other Operator": {"rating": 4}
            }
        }
        self.variable = "rating"
        self.operator_ids = [1, 2]

    @patch('src.visualizations.create_output_file')
    @patch('src.visualizations.get_average_ratings_for_dates')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.legend')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.scatter')
    @patch('seaborn.histplot')
    @patch('matplotlib.pyplot.figure')
    def test_plot_histogram(
        self, mock_figure, mock_histplot, mock_scatter, 
        mock_title, mock_xlabel, mock_ylabel, mock_legend,
        mock_tight_layout, mock_savefig, mock_get_avg,
        mock_create_output
    ):
        # Setup mock returns
        mock_get_avg.return_value = ([5, 3], [4], None)
        mock_create_output.return_value = "test_output.png"

        # Call function
        plot_histogram(self.test_data, self.variable, self.operator_ids)

        # Verify calls
        mock_figure.assert_called_once_with(figsize=(10, 6))
        mock_histplot.assert_called_once_with([4], color="blue", label="CSM Operators")
        self.assertEqual(mock_scatter.call_count, 2)  # Once for each operator
        mock_savefig.assert_called_once_with("test_output.png", dpi=300, bbox_inches="tight")

    @patch('src.visualizations.create_output_file')
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.tight_layout')
    @patch('matplotlib.pyplot.grid')
    @patch('matplotlib.pyplot.legend')
    @patch('matplotlib.pyplot.ylabel')
    @patch('matplotlib.pyplot.xlabel')
    @patch('matplotlib.pyplot.title')
    @patch('matplotlib.pyplot.plot')
    @patch('matplotlib.pyplot.figure')
    def test_plot_line(
        self, mock_figure, mock_plot, mock_title, 
        mock_xlabel, mock_ylabel, mock_legend, mock_grid,
        mock_tight_layout, mock_savefig, mock_create_output
    ):
        # Setup mock return
        mock_create_output.return_value = "test_output.png"

        # Call function
        plot_line(self.test_data, self.variable, self.operator_ids)

        # Verify calls
        mock_figure.assert_called_once_with(figsize=(12, 6))
        self.assertTrue(mock_plot.called)  # Should be called at least once
        mock_title.assert_called_once()
        mock_xlabel.assert_called_once_with("Date")
        mock_ylabel.assert_called_once()
        mock_legend.assert_called_once_with(title="Operators")
        mock_grid.assert_called_once_with(True)
        mock_tight_layout.assert_called_once()
        mock_savefig.assert_called_once_with("test_output.png", dpi=300, bbox_inches="tight")

    def test_get_average_ratings_for_dates(self):
        highlighted, others, dates = get_average_ratings_for_dates(
            self.test_data, 
            self.variable, 
            self.operator_ids
        )
        self.assertEqual(highlighted, [5, 3])
        self.assertEqual(others, [4])
        self.assertEqual(dates, list(self.test_data.keys()))