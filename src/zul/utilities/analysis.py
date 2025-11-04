import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from scipy import stats
import json


class ChartGenerator:
    """
    Dynamic chart generator class that accepts JSON/dictionary parameters
    for flexible multi-dataset comparisons.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the ChartGenerator with configuration.

        Args:
            config: Dictionary containing default configuration
                   {
                       "style": "default",
                       "figsize": [12, 8],
                       "colors": ["blue", "red", "green", "orange", "purple"],
                       "alpha": 0.7
                   }


        Example:
        # Initialize chart generator
        chart_gen = ChartGenerator({
            "figsize": [14, 10],
            "colors": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"],
            "alpha": 0.8
        })

        # Example 1: Latency comparison between A, B, and C
        latency_config = {
            "chart_type": "dashboard",
            "data": {
                "System A (Current)": [45.2, 52.1, 48.7, 44.3, 51.2, 47.8, 49.1, 46.5],
                "System B (Optimized)": [38.7, 41.2, 39.8, 37.5, 42.1, 40.3, 38.9, 41.7],
                "System C (Experimental)": [35.1, 37.8, 36.2, 34.9, 38.5, 36.7, 35.8, 37.2]
            },
            "title": "Latency Performance Comparison: A vs B vs C",
            "xlabel": "Test Scenarios",
            "ylabel": "Latency (ms)",
            "metric_name": "Latency",
            "show_statistics": True
        }

        print("Creating 3-way latency comparison dashboard...")
        stats = chart_gen.create_comparison_chart(latency_config)
        chart_gen.show()
        chart_gen.save("3way_latency_comparison.png")
        chart_gen.clear()

        # Example 2: 5-way throughput comparison
        throughput_config = {
            "chart_type": "bar",
            "data": {
                "Algorithm A": [1200, 1150, 1180, 1220, 1190],
                "Algorithm B": [1350, 1320, 1380, 1340, 1360],
                "Algorithm C": [1420, 1450, 1410, 1480, 1440],
                "Algorithm D": [1380, 1400, 1360, 1420, 1390],
                "Algorithm E": [1500, 1520, 1480, 1540, 1510]
            },
            "labels": ["Test 1", "Test 2", "Test 3", "Test 4", "Test 5"],
            "title": "Throughput Comparison: 5 Algorithms",
            "xlabel": "Test Scenarios",
            "ylabel": "Throughput (requests/sec)",
            "show_difference": True,
            "show_statistics": True,
            "colors": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"]
        }

        print("Creating 5-way throughput comparison...")
        throughput_stats = chart_gen.create_comparison_chart(throughput_config)
        chart_gen.show()
        chart_gen.save("5way_throughput_comparison.png")
        chart_gen.clear()

        # Example 3: Memory usage comparison with box plots
        memory_config = {
            "chart_type": "box",
            "data": {
                "Version 1.0": [512, 520, 508, 525, 515, 518, 522, 510, 528, 516],
                "Version 2.0": [480, 485, 475, 490, 478, 482, 488, 476, 492, 480],
                "Version 2.1": [465, 470, 460, 475, 468, 472, 478, 463, 480, 467],
                "Version 3.0": [445, 450, 440, 455, 448, 452, 458, 443, 460, 447]
            },
            "title": "Memory Usage Comparison Across Versions",
            "ylabel": "Memory Usage (MB)",
            "show_statistics": True
        }

        print("Creating memory usage box plot comparison...")
        memory_stats = chart_gen.create_comparison_chart(memory_config)
        chart_gen.show()
        chart_gen.save("memory_usage_comparison.png")
        chart_gen.clear()

        # Example 4: Response time line chart with trend analysis
        response_time_config = {
            "chart_type": "line",
            "data": {
                "Database A": [25.5, 24.8, 26.2, 25.1, 24.9, 25.8, 26.0, 25.3, 24.7, 25.6],
                "Database B": [22.1, 21.8, 22.5, 21.9, 22.3, 22.0, 21.7, 22.4, 21.6, 22.2],
                "Database C": [28.9, 29.2, 28.5, 29.8, 28.7, 29.1, 28.3, 29.5, 28.8, 29.0]
            },
            "labels": ["Hour 1", "Hour 2", "Hour 3", "Hour 4", "Hour 5",
                        "Hour 6", "Hour 7", "Hour 8", "Hour 9", "Hour 10"],
            "title": "Database Response Time Over Time",
            "xlabel": "Time Period",
            "ylabel": "Response Time (ms)",
            "show_statistics": True,
            "additional_options": {
                "markers": True
            }
        }

        print("Creating response time line chart...")
        response_stats = chart_gen.create_comparison_chart(response_time_config)
        chart_gen.show()
        chart_gen.save("response_time_comparison.png")
        chart_gen.clear()

        # Example 5: Load testing histogram comparison
        load_test_config = {
            "chart_type": "histogram",
            "data": {
                "Baseline Load": np.random.normal(100, 15, 1000).tolist(),
                "2x Load": np.random.normal(85, 20, 1000).tolist(),
                "4x Load": np.random.normal(75, 25, 1000).tolist(),
                "8x Load": np.random.normal(65, 30, 1000).tolist()
            },
            "title": "Performance Distribution Under Different Loads",
            "xlabel": "Performance Score",
            "ylabel": "Frequency",
            "additional_options": {
                "bins": 30,
                "overlay": True,
                "density": True
            }
        }

        print("Creating load testing histogram comparison...")
        load_stats = chart_gen.create_comparison_chart(load_test_config)
        chart_gen.show()
        chart_gen.save("load_test_histogram.png")
        chart_gen.clear()

        # Print comprehensive statistics
        print("\n" + "="*80)
        print("COMPREHENSIVE ANALYSIS RESULTS")
        print("="*80)

        print("\n1. LATENCY COMPARISON (3 Systems):")
        if 'performance_comparisons' in stats:
            for comparison, data in stats['performance_comparisons'].items():
                improvement = data['improvement_percentage']
                status = "BETTER" if data['is_better'] else "WORSE"
                print(f"   {comparison}: {improvement:+.1f}% ({status})")

        print("\n2. THROUGHPUT COMPARISON (5 Algorithms):")
        for algo, algo_stats in throughput_stats.items():
            if algo != 'statistical_tests' and algo != 'performance_comparisons':
                print(f"   {algo}: {algo_stats['mean']:.0f} ± {algo_stats['std']:.0f} req/sec")

        print("\n3. STATISTICAL SIGNIFICANCE:")
        if 'statistical_tests' in stats:
            if 'anova' in stats['statistical_tests']:
                p_val = stats['statistical_tests']['anova']['p_value']
                sig = "SIGNIFICANT" if p_val < 0.05 else "NOT SIGNIFICANT"
                print(f"   ANOVA p-value: {p_val:.6f} ({sig})")

        # Example 6: Custom configuration from JSON file/string
        json_config = /"/"/"
        {
            "chart_type": "dashboard",
            "data": {
                "Production": [95.2, 94.8, 95.5, 94.9, 95.1],
                "Staging": [93.1, 92.8, 93.5, 92.9, 93.2],
                "Development": [88.5, 87.9, 89.1, 88.2, 88.8]
            },
            "title": "System Availability Comparison",
            "xlabel": "Monitoring Periods",
            "ylabel": "Availability (%)",
            "metric_name": "Availability",
            "colors": ["#27ae60", "#f39c12", "#e74c3c"],
            "show_statistics": true,
            "figsize": [15, 10]
        }
        /"/"/"

        print("\nCreating system availability comparison from JSON...")
        availability_config = json.loads(json_config)
        availability_stats = chart_gen.create_comparison_chart(availability_config)
        chart_gen.show()
        chart_gen.save("availability_comparison.png")
        chart_gen.clear()


        # Batch creation example
        batch_configs = [
            {
                "chart_type": "bar",
                "data": {
                    "Q1": [100, 110, 105],
                    "Q2": [120, 125, 115],
                    "Q3": [130, 135, 125],
                    "Q4": [140, 145, 135]
                },
                "labels": ["Product A", "Product B", "Product C"],
                "title": "Quarterly Sales Comparison",
                "ylabel": "Sales ($K)",
                "save_filename": "quarterly_sales.png"
            },
            {
                "chart_type": "line",
                "data": {
                    "Server 1": [85, 87, 83, 89, 86],
                    "Server 2": [92, 94, 90, 95, 93],
                    "Server 3": [78, 80, 76, 82, 79]
                },
                "title": "Server Performance Trends",
                "ylabel": "Performance Score",
                "save_filename": "server_performance.png"
            }
        ]

        chart_gen = ChartGenerator()
        batch_results = batch_create_charts(chart_gen, batch_configs)

        print("\nBatch processing completed!")
        print(f"Created {len(batch_results)} charts with statistical analysis.")


        """
        default_config = {
            "style": "default",
            "figsize": [12, 8],
            "colors": [
                "#3498db",
                "#e74c3c",
                "#2ecc71",
                "#f39c12",
                "#9b59b6",
                "#1abc9c",
                "#e67e22",
                "#34495e",
                "#e91e63",
                "#795548",
            ],
            "alpha": 0.7,
            "grid": True,
            "grid_alpha": 0.3,
        }

        self.config = {**default_config, **(config or {})}
        plt.style.use(self.config["style"])
        self.current_fig = None
        self.current_ax = None

    def create_comparison_chart(self, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a comparison chart based on JSON configuration.

        Args:
            chart_config: Dictionary containing all chart parameters
                {
                    "chart_type": "bar|line|box|histogram|scatter|dashboard",
                    "data": {
                        "dataset_name_1": [values],
                        "dataset_name_2": [values],
                        ...
                    },
                    "labels": ["label1", "label2", ...],  # Optional for categories/x-axis
                    "title": "Chart Title",
                    "xlabel": "X-axis Label",
                    "ylabel": "Y-axis Label",
                    "colors": ["color1", "color2", ...],  # Optional, uses default if not provided
                    "show_statistics": True,
                    "show_difference": True,
                    "additional_options": {
                        # Chart-specific options
                    }
                }

        Returns:
            Dictionary containing statistical analysis and results
        """
        chart_type = chart_config.get("chart_type", "bar").lower()

        if chart_type == "bar":
            return self._create_comparison_bar_chart(chart_config)
        elif chart_type == "line":
            return self._create_comparison_line_chart(chart_config)
        elif chart_type == "box":
            return self._create_comparison_box_chart(chart_config)
        elif chart_type == "histogram":
            return self._create_comparison_histogram(chart_config)
        # elif chart_type == "scatter":
        #     return self._create_comparison_scatter_chart(chart_config)
        elif chart_type == "dashboard":
            return self._create_comparison_dashboard(chart_config)
        else:
            raise ValueError(f"Unsupported chart type: {chart_type}")

    def _create_comparison_bar_chart(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create comparison bar chart from JSON config."""
        data = config["data"]
        datasets = list(data.keys())
        labels = config.get(
            "labels", [f"Item {i+1}" for i in range(len(data[datasets[0]]))]
        )

        title = config.get("title", "Bar Chart Comparison")
        xlabel = config.get("xlabel", "Categories")
        ylabel = config.get("ylabel", "Values")
        show_difference = config.get("show_difference", True)

        colors = config.get("colors", self.config["colors"][: len(datasets)])

        figsize = config.get("figsize", self.config["figsize"])
        self.current_fig, self.current_ax = plt.subplots(figsize=figsize)

        x = np.arange(len(labels))
        n_datasets = len(datasets)
        width = 0.8 / n_datasets

        bars = []
        stats_summary = {}

        # Create bars for each dataset
        for i, (dataset_name, dataset_values) in enumerate(data.items()):
            offset = (i - n_datasets / 2 + 0.5) * width
            bar = self.current_ax.bar(
                x + offset,
                dataset_values,
                width,
                label=dataset_name,
                color=colors[i],
                alpha=self.config["alpha"],
            )
            bars.append(bar)

            # Calculate statistics
            stats_summary[dataset_name] = {
                "mean": np.mean(dataset_values),
                "median": np.median(dataset_values),
                "std": np.std(dataset_values),
                "min": np.min(dataset_values),
                "max": np.max(dataset_values),
            }

            # Add value annotations
            for j, (bar_rect, value) in enumerate(zip(bar, dataset_values)):
                self.current_ax.annotate(
                    f"{value:.1f}",
                    xy=(
                        bar_rect.get_x() + bar_rect.get_width() / 2,
                        bar_rect.get_height(),
                    ),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                )

        # Show percentage differences if requested
        if show_difference and len(datasets) >= 2:
            baseline_data = list(data.values())[0]

            for i, label_idx in enumerate(labels):
                if i < len(baseline_data):
                    baseline_val = baseline_data[i]
                    y_pos = max([data[ds][i] for ds in datasets]) * 1.15

                    # Show differences relative to first dataset
                    diff_text = []
                    for j, (dataset_name, dataset_values) in enumerate(data.items()):
                        if j > 0 and i < len(dataset_values) and baseline_val != 0:
                            diff_pct = (
                                (dataset_values[i] - baseline_val) / baseline_val
                            ) * 100
                            diff_text.append(f"{dataset_name}: {diff_pct:+.1f}%")

                    if diff_text:
                        self.current_ax.text(
                            i,
                            y_pos,
                            "\n".join(diff_text),
                            ha="center",
                            va="bottom",
                            fontsize=7,
                            bbox=dict(
                                boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.8
                            ),
                        )

        self.current_ax.set_xlabel(xlabel)
        self.current_ax.set_ylabel(ylabel)
        self.current_ax.set_title(title)
        self.current_ax.set_xticks(x)
        self.current_ax.set_xticklabels(labels, rotation=45)
        self.current_ax.legend()

        if self.config["grid"]:
            self.current_ax.grid(True, alpha=self.config["grid_alpha"])

        plt.tight_layout()

        # Add statistical tests if more than one dataset
        if len(datasets) >= 2:
            stats_summary["statistical_tests"] = self._perform_statistical_tests(data)

        return stats_summary

    def _create_comparison_line_chart(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create comparison line chart from JSON config."""
        data = config["data"]
        datasets = list(data.keys())
        labels = config.get("labels", [f"{i+1}" for i in range(len(data[datasets[0]]))])

        title = config.get("title", "Line Chart Comparison")
        xlabel = config.get("xlabel", "X-axis")
        ylabel = config.get("ylabel", "Y-axis")
        show_statistics = config.get("show_statistics", True)
        markers = config.get("additional_options", {}).get("markers", True)

        colors = config.get("colors", self.config["colors"][: len(datasets)])

        figsize = config.get("figsize", self.config["figsize"])
        self.current_fig, self.current_ax = plt.subplots(figsize=figsize)

        stats_summary = {}
        marker_styles = ["o", "s", "^", "D", "v", "<", ">", "p", "*", "h"]

        # Plot lines for each dataset
        for i, (dataset_name, dataset_values) in enumerate(data.items()):
            marker = marker_styles[i % len(marker_styles)] if markers else None

            self.current_ax.plot(
                labels,
                dataset_values,
                label=dataset_name,
                color=colors[i],
                marker=marker,
                linewidth=2,
                markersize=6,
                alpha=self.config["alpha"],
            )

            # Calculate statistics
            stats_summary[dataset_name] = {
                "mean": np.mean(dataset_values),
                "median": np.median(dataset_values),
                "std": np.std(dataset_values),
                "trend": np.polyfit(range(len(dataset_values)), dataset_values, 1)[0],
            }

            # Add mean line if requested
            if show_statistics:
                mean_val = stats_summary[dataset_name]["mean"]
                self.current_ax.axhline(
                    y=mean_val,
                    color=colors[i],
                    linestyle="--",
                    alpha=0.6,
                    label=f"{dataset_name} Mean: {mean_val:.2f}",
                )

        self.current_ax.set_title(title)
        self.current_ax.set_xlabel(xlabel)
        self.current_ax.set_ylabel(ylabel)
        self.current_ax.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

        if self.config["grid"]:
            self.current_ax.grid(True, alpha=self.config["grid_alpha"])

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Statistical tests
        if len(datasets) >= 2:
            stats_summary["statistical_tests"] = self._perform_statistical_tests(data)

        return stats_summary

    def _create_comparison_box_chart(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create comparison box plot from JSON config."""
        data = config["data"]
        datasets = list(data.keys())

        title = config.get("title", "Box Plot Comparison")
        ylabel = config.get("ylabel", "Values")
        show_statistics = config.get("show_statistics", True)

        colors = config.get("colors", self.config["colors"][: len(datasets)])

        figsize = config.get("figsize", self.config["figsize"])
        self.current_fig, self.current_ax = plt.subplots(figsize=figsize)

        # Prepare data for box plot
        box_data = [data[dataset] for dataset in datasets]

        bp = self.current_ax.boxplot(box_data, labels=datasets, patch_artist=True)

        # Color the boxes
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)  # type: ignore
            patch.set_alpha(self.config["alpha"])

        self.current_ax.set_title(title)
        self.current_ax.set_ylabel(ylabel)

        if self.config["grid"]:
            self.current_ax.grid(True, alpha=self.config["grid_alpha"])

        plt.xticks(rotation=45)
        plt.tight_layout()

        # Calculate comprehensive statistics
        stats_summary = {}
        for dataset_name, dataset_values in data.items():
            stats_summary[dataset_name] = {
                "mean": np.mean(dataset_values),
                "median": np.median(dataset_values),
                "std": np.std(dataset_values),
                "q25": np.percentile(dataset_values, 25),
                "q75": np.percentile(dataset_values, 75),
                "iqr": np.percentile(dataset_values, 75)
                - np.percentile(dataset_values, 25),
                "min": np.min(dataset_values),
                "max": np.max(dataset_values),
            }

        # Add statistical tests
        if len(datasets) >= 2:
            stats_summary["statistical_tests"] = self._perform_statistical_tests(data)

            # Add statistics text if requested
            if show_statistics:
                stats_text = self._format_statistics_text(stats_summary)
                self.current_ax.text(
                    0.02,
                    0.98,
                    stats_text,
                    transform=self.current_ax.transAxes,
                    verticalalignment="top",
                    fontsize=9,
                    bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
                )

        return stats_summary

    def _create_comparison_histogram(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create comparison histogram from JSON config."""
        data = config["data"]
        datasets = list(data.keys())

        title = config.get("title", "Histogram Comparison")
        xlabel = config.get("xlabel", "Values")
        ylabel = config.get("ylabel", "Frequency")
        bins = config.get("additional_options", {}).get("bins", 20)
        overlay = config.get("additional_options", {}).get("overlay", True)
        density = config.get("additional_options", {}).get("density", True)

        colors = config.get("colors", self.config["colors"][: len(datasets)])

        figsize = config.get("figsize", self.config["figsize"])

        if overlay:
            self.current_fig, self.current_ax = plt.subplots(figsize=figsize)

            for i, (dataset_name, dataset_values) in enumerate(data.items()):
                self.current_ax.hist(
                    dataset_values,
                    bins=bins,
                    alpha=self.config["alpha"],
                    label=dataset_name,
                    color=colors[i],
                    density=density,
                )

            self.current_ax.set_title(title)
            self.current_ax.set_xlabel(xlabel)
            self.current_ax.set_ylabel("Density" if density else ylabel)
            self.current_ax.legend()

            if self.config["grid"]:
                self.current_ax.grid(True, alpha=self.config["grid_alpha"])
        else:
            n_datasets = len(datasets)
            self.current_fig, axes = plt.subplots(
                n_datasets, 1, figsize=(figsize[0], figsize[1] * n_datasets)
            )
            if n_datasets == 1:
                axes = [axes]

            for i, (dataset_name, dataset_values) in enumerate(data.items()):
                axes[i].hist(
                    dataset_values,
                    bins=bins,
                    color=colors[i],  # type: ignore
                    alpha=self.config["alpha"],
                    density=density,
                )
                axes[i].set_title(f"{title} - {dataset_name}")  # type: ignore
                axes[i].set_ylabel("Density" if density else ylabel)  # type: ignore
                if i == n_datasets - 1:
                    axes[i].set_xlabel(xlabel)  # type: ignore

                if self.config["grid"]:
                    axes[i].grid(True, alpha=self.config["grid_alpha"])  # type: ignore

        plt.tight_layout()

        # Calculate statistics
        stats_summary = {}
        for dataset_name, dataset_values in data.items():
            stats_summary[dataset_name] = {
                "mean": np.mean(dataset_values),
                "median": np.median(dataset_values),
                "std": np.std(dataset_values),
                "skewness": stats.skew(dataset_values),  # type: ignore
                "kurtosis": stats.kurtosis(dataset_values),  # type: ignore
            }

        if len(datasets) >= 2:
            stats_summary["statistical_tests"] = self._perform_statistical_tests(data)

        return stats_summary

    def _create_comparison_dashboard(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive comparison dashboard from JSON config."""
        data = config["data"]
        datasets = list(data.keys())
        n_datasets = len(datasets)

        title = config.get("title", "Comparison Dashboard")
        ylabel = config.get("ylabel", "Values")
        metric_name = config.get("metric_name", ylabel)

        colors = config.get("colors", self.config["colors"][:n_datasets])

        figsize = config.get("figsize", [16, 12])
        self.current_fig = plt.figure(figsize=figsize)

        # Create dynamic grid based on number of datasets
        if n_datasets <= 3:
            gs = self.current_fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
        else:
            gs = self.current_fig.add_gridspec(4, 2, hspace=0.3, wspace=0.3)

        # 1. Bar comparison
        ax1 = self.current_fig.add_subplot(gs[0, 0])
        x = range(min(len(data[ds]) for ds in datasets))
        width = 0.8 / n_datasets

        for i, (dataset_name, dataset_values) in enumerate(data.items()):
            offset = (i - n_datasets / 2 + 0.5) * width
            ax1.bar(
                [j + offset for j in x],
                dataset_values[: len(x)],
                width,
                label=dataset_name,
                alpha=self.config["alpha"],
                color=colors[i],
            )

        ax1.set_title(f"{metric_name} Comparison")
        ax1.set_ylabel(metric_name)
        ax1.legend()
        ax1.grid(True, alpha=self.config["grid_alpha"])

        # 2. Box plot comparison
        ax2 = self.current_fig.add_subplot(gs[0, 1])
        bp = ax2.boxplot(
            [data[ds] for ds in datasets], labels=datasets, patch_artist=True
        )

        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)  # type: ignore
            patch.set_alpha(self.config["alpha"])

        ax2.set_title(f"{metric_name} Distribution")
        ax2.set_ylabel(metric_name)
        ax2.grid(True, alpha=self.config["grid_alpha"])
        plt.setp(ax2.get_xticklabels(), rotation=45)

        # 3. Line chart
        ax3 = self.current_fig.add_subplot(gs[1, :])
        x_range = range(max(len(data[ds]) for ds in datasets))

        for i, (dataset_name, dataset_values) in enumerate(data.items()):
            # Pad shorter datasets with None
            # padded_values = dataset_values + [None] * (len(x_range) - len(dataset_values))
            ax3.plot(
                x_range[: len(dataset_values)],
                dataset_values,
                "o-",
                label=dataset_name,
                color=colors[i],
                linewidth=2,
                markersize=4,
            )
            ax3.axhline(
                y=np.mean(dataset_values), color=colors[i], linestyle="--", alpha=0.6
            )

        ax3.set_title(f"{metric_name} Trends")
        ax3.set_xlabel("Data Points")
        ax3.set_ylabel(metric_name)
        ax3.legend()
        ax3.grid(True, alpha=self.config["grid_alpha"])

        # 4. Histogram comparison
        ax4 = self.current_fig.add_subplot(gs[2, 0])
        for i, (dataset_name, dataset_values) in enumerate(data.items()):
            ax4.hist(
                dataset_values,
                bins=15,
                alpha=0.6,
                label=dataset_name,
                color=colors[i],
                density=True,
            )

        ax4.set_title(f"{metric_name} Distribution")
        ax4.set_xlabel(metric_name)
        ax4.set_ylabel("Density")
        ax4.legend()
        ax4.grid(True, alpha=self.config["grid_alpha"])

        # 5. Statistics summary
        if n_datasets <= 3:
            ax5 = self.current_fig.add_subplot(gs[2, 1])
        else:
            ax5 = self.current_fig.add_subplot(gs[3, :])
        ax5.axis("off")

        # Calculate comprehensive statistics
        stats_summary = {}
        for dataset_name, dataset_values in data.items():
            stats_summary[dataset_name] = {
                "mean": np.mean(dataset_values),
                "median": np.median(dataset_values),
                "std": np.std(dataset_values),
                "min": np.min(dataset_values),
                "max": np.max(dataset_values),
                "q25": np.percentile(dataset_values, 25),
                "q75": np.percentile(dataset_values, 75),
                "count": len(dataset_values),
            }

        # Statistical tests and performance comparisons
        if len(datasets) >= 2:
            stats_summary["statistical_tests"] = self._perform_statistical_tests(data)
            stats_summary["performance_comparisons"] = (
                self._calculate_performance_comparisons(data)
            )

        # Format statistics text
        stats_text = self._format_comprehensive_statistics_text(
            stats_summary, datasets, metric_name
        )

        ax5.text(
            0.05,
            0.95,
            stats_text,
            transform=ax5.transAxes,
            fontsize=9,
            verticalalignment="top",
            fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="lightgray", alpha=0.8),
        )

        self.current_fig.suptitle(title, fontsize=16, fontweight="bold")

        return stats_summary

    def _perform_statistical_tests(
        self, data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Perform comprehensive statistical tests on multiple datasets."""
        datasets = list(data.keys())
        results = {}

        if len(datasets) == 2:
            # Two-sample tests
            data_a, data_b = list(data.values())

            # t-test
            t_stat, p_value = stats.ttest_ind(data_a, data_b)  # type: ignore
            results["t_test"] = {
                "statistic": t_stat,
                "p_value": p_value,
                "significant": p_value < 0.05,  # type: ignore
            }

            # Mann-Whitney U test
            u_stat, u_p_value = stats.mannwhitneyu(data_a, data_b, alternative="two-sided")  # type: ignore
            results["mann_whitney"] = {
                "statistic": u_stat,
                "p_value": u_p_value,
                "significant": u_p_value < 0.05,
            }

            # Kolmogorov-Smirnov test
            ks_stat, ks_p_value = stats.ks_2samp(data_a, data_b)  # type: ignore
            results["kolmogorov_smirnov"] = {
                "statistic": ks_stat,
                "p_value": ks_p_value,
                "significant": ks_p_value < 0.05,  # type: ignore
            }

        elif len(datasets) > 2:
            # Multi-sample tests
            data_values = list(data.values())

            # One-way ANOVA
            f_stat, f_p_value = stats.f_oneway(*data_values)  # type: ignore
            results["anova"] = {
                "f_statistic": f_stat,
                "p_value": f_p_value,
                "significant": f_p_value < 0.05,
            }

            # Kruskal-Wallis test
            h_stat, h_p_value = stats.kruskal(*data_values)  # type: ignore
            results["kruskal_wallis"] = {
                "h_statistic": h_stat,
                "p_value": h_p_value,
                "significant": h_p_value < 0.05,
            }

        return results

    def _calculate_performance_comparisons(
        self, data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """Calculate performance improvements between datasets."""
        datasets = list(data.keys())
        baseline = datasets[0]
        baseline_mean = np.mean(data[baseline])

        comparisons = {}
        for i, dataset in enumerate(datasets[1:], 1):
            dataset_mean = np.mean(data[dataset])
            improvement_pct = ((baseline_mean - dataset_mean) / baseline_mean) * 100

            comparisons[f"{baseline}_vs_{dataset}"] = {
                "baseline_mean": baseline_mean,
                "comparison_mean": dataset_mean,
                "improvement_percentage": improvement_pct,
                "is_better": improvement_pct > 0,
            }

        return comparisons

    def _format_statistics_text(self, stats_summary: Dict[str, Any]) -> str:
        """Format statistics summary as readable text."""
        text_lines = ["Statistical Summary:\n"]

        for dataset_name, stats in stats_summary.items():
            if dataset_name != "statistical_tests":
                text_lines.append(f"{dataset_name}:")
                text_lines.append(f"  Mean: {stats['mean']:.2f}")
                text_lines.append(f"  Median: {stats['median']:.2f}")
                text_lines.append(f"  Std: {stats['std']:.2f}")
                text_lines.append("")

        if "statistical_tests" in stats_summary:
            text_lines.append("Statistical Tests:")
            tests = stats_summary["statistical_tests"]

            if "t_test" in tests:
                text_lines.append(f"t-test p-value: {tests['t_test']['p_value']:.4f}")
                text_lines.append(
                    f"Significant: {'Yes' if tests['t_test']['significant'] else 'No'}"
                )

            if "anova" in tests:
                text_lines.append(f"ANOVA p-value: {tests['anova']['p_value']:.4f}")
                text_lines.append(
                    f"Significant: {'Yes' if tests['anova']['significant'] else 'No'}"
                )

        return "\n".join(text_lines)

    def _format_comprehensive_statistics_text(
        self, stats_summary: Dict[str, Any], datasets: List[str], metric_name: str
    ) -> str:
        """Format comprehensive statistics for dashboard."""
        text_lines = [f"{metric_name} Analysis:\n"]

        # Dataset statistics
        for dataset_name in datasets:
            if dataset_name in stats_summary:
                stats = stats_summary[dataset_name]
                text_lines.append(f"{dataset_name}:")
                text_lines.append(f"  Mean: {stats['mean']:.2f}")
                text_lines.append(f"  Std: {stats['std']:.2f}")
                text_lines.append(f"  Range: {stats['min']:.1f} - {stats['max']:.1f}")
                text_lines.append("")

        # Performance comparisons
        if "performance_comparisons" in stats_summary:
            text_lines.append("Performance Comparisons:")
            for comparison_name, comparison_data in stats_summary[
                "performance_comparisons"
            ].items():
                improvement = comparison_data["improvement_percentage"]
                status = "Better" if comparison_data["is_better"] else "Worse"
                text_lines.append(f"{comparison_name}: {improvement:+.1f}% ({status})")
            text_lines.append("")

        # Statistical significance
        if "statistical_tests" in stats_summary:
            tests = stats_summary["statistical_tests"]
            text_lines.append("Statistical Tests:")

            if "t_test" in tests:
                sig = "Yes" if tests["t_test"]["significant"] else "No"
                text_lines.append(f"t-test significant: {sig}")
            elif "anova" in tests:
                sig = "Yes" if tests["anova"]["significant"] else "No"
                text_lines.append(f"ANOVA significant: {sig}")

        return "\n".join(text_lines)

    def show(self) -> None:
        """Display the current chart."""
        if self.current_fig:
            plt.show()

    def save(self, filename: str, dpi: int = 300, bbox_inches: str = "tight") -> None:
        """Save the current chart to file."""
        if self.current_fig:
            self.current_fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)

    def clear(self) -> None:
        """Clear the current chart."""
        if self.current_fig:
            plt.close(self.current_fig)
            self.current_fig = None
            self.current_ax = None


def create_chart_from_csv(
    chart_gen: ChartGenerator, csv_file: str, config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create charts from CSV data with JSON configuration.

    Args:
        chart_gen: ChartGenerator instance
        csv_file: Path to CSV file
        config: Chart configuration with additional CSV parsing options

    Returns:
        Statistical analysis results
    """

    # Read CSV
    df = pd.read_csv(csv_file)

    # Extract data based on configuration
    data_columns = config.get("data_columns", [])
    label_column = config.get("label_column", None)

    chart_config = config.copy()
    chart_config["data"] = {}

    # Build data dictionary from CSV columns
    for col in data_columns:
        if col in df.columns:
            chart_config["data"][col] = df[col].tolist()

    # Extract labels if specified
    if label_column and label_column in df.columns:
        chart_config["labels"] = df[label_column].tolist()

    # Create chart
    return chart_gen.create_comparison_chart(chart_config)


def batch_create_charts(
    chart_gen: ChartGenerator, configs: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Create multiple charts from a list of configurations.

    Args:
        chart_gen: ChartGenerator instance
        configs: List of chart configurations

    Returns:
        List of statistical results for each chart
    """
    results = []

    for i, config in enumerate(configs):
        print(f"Creating chart {i+1}/{len(configs)}: {config.get('title', 'Untitled')}")

        # Create chart
        stats = chart_gen.create_comparison_chart(config)
        results.append(stats)

        # Save if filename specified
        if "save_filename" in config:
            chart_gen.save(config["save_filename"])

        # Show if requested
        if config.get("show", True):
            chart_gen.show()

        chart_gen.clear()

    return results


# Example usage with JSON configuration
if __name__ == "__main__":
    # Initialize chart generator
    chart_gen = ChartGenerator(
        {
            "figsize": [14, 10],
            "colors": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"],
            "alpha": 0.8,
        }
    )

    # Example 1: Latency comparison between A, B, and C
    latency_config = {
        "chart_type": "dashboard",
        "data": {
            "System A (Current)": [45.2, 52.1, 48.7, 44.3, 51.2, 47.8, 49.1, 46.5],
            "System B (Optimized)": [38.7, 41.2, 39.8, 37.5, 42.1, 40.3, 38.9, 41.7],
            "System C (Experimental)": [35.1, 37.8, 36.2, 34.9, 38.5, 36.7, 35.8, 37.2],
        },
        "title": "Latency Performance Comparison: A vs B vs C",
        "xlabel": "Test Scenarios",
        "ylabel": "Latency (ms)",
        "metric_name": "Latency",
        "show_statistics": True,
    }

    print("Creating 3-way latency comparison dashboard...")
    stats = chart_gen.create_comparison_chart(latency_config)
    chart_gen.show()
    chart_gen.save("3way_latency_comparison.png")
    chart_gen.clear()

    # Example 2: 5-way throughput comparison
    throughput_config = {
        "chart_type": "bar",
        "data": {
            "Algorithm A": [1200, 1150, 1180, 1220, 1190],
            "Algorithm B": [1350, 1320, 1380, 1340, 1360],
            "Algorithm C": [1420, 1450, 1410, 1480, 1440],
            "Algorithm D": [1380, 1400, 1360, 1420, 1390],
            "Algorithm E": [1500, 1520, 1480, 1540, 1510],
        },
        "labels": ["Test 1", "Test 2", "Test 3", "Test 4", "Test 5"],
        "title": "Throughput Comparison: 5 Algorithms",
        "xlabel": "Test Scenarios",
        "ylabel": "Throughput (requests/sec)",
        "show_difference": True,
        "show_statistics": True,
        "colors": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6"],
    }

    print("Creating 5-way throughput comparison...")
    throughput_stats = chart_gen.create_comparison_chart(throughput_config)
    chart_gen.show()
    chart_gen.save("5way_throughput_comparison.png")
    chart_gen.clear()

    # Example 3: Memory usage comparison with box plots
    memory_config = {
        "chart_type": "box",
        "data": {
            "Version 1.0": [512, 520, 508, 525, 515, 518, 522, 510, 528, 516],
            "Version 2.0": [480, 485, 475, 490, 478, 482, 488, 476, 492, 480],
            "Version 2.1": [465, 470, 460, 475, 468, 472, 478, 463, 480, 467],
            "Version 3.0": [445, 450, 440, 455, 448, 452, 458, 443, 460, 447],
        },
        "title": "Memory Usage Comparison Across Versions",
        "ylabel": "Memory Usage (MB)",
        "show_statistics": True,
    }

    print("Creating memory usage box plot comparison...")
    memory_stats = chart_gen.create_comparison_chart(memory_config)
    chart_gen.show()
    chart_gen.save("memory_usage_comparison.png")
    chart_gen.clear()

    # Example 4: Response time line chart with trend analysis
    response_time_config = {
        "chart_type": "line",
        "data": {
            "Database A": [25.5, 24.8, 26.2, 25.1, 24.9, 25.8, 26.0, 25.3, 24.7, 25.6],
            "Database B": [22.1, 21.8, 22.5, 21.9, 22.3, 22.0, 21.7, 22.4, 21.6, 22.2],
            "Database C": [28.9, 29.2, 28.5, 29.8, 28.7, 29.1, 28.3, 29.5, 28.8, 29.0],
        },
        "labels": [
            "Hour 1",
            "Hour 2",
            "Hour 3",
            "Hour 4",
            "Hour 5",
            "Hour 6",
            "Hour 7",
            "Hour 8",
            "Hour 9",
            "Hour 10",
        ],
        "title": "Database Response Time Over Time",
        "xlabel": "Time Period",
        "ylabel": "Response Time (ms)",
        "show_statistics": True,
        "additional_options": {"markers": True},
    }

    print("Creating response time line chart...")
    response_stats = chart_gen.create_comparison_chart(response_time_config)
    chart_gen.show()
    chart_gen.save("response_time_comparison.png")
    chart_gen.clear()

    # Example 5: Load testing histogram comparison
    load_test_config = {
        "chart_type": "histogram",
        "data": {
            "Baseline Load": np.random.normal(100, 15, 1000).tolist(),
            "2x Load": np.random.normal(85, 20, 1000).tolist(),
            "4x Load": np.random.normal(75, 25, 1000).tolist(),
            "8x Load": np.random.normal(65, 30, 1000).tolist(),
        },
        "title": "Performance Distribution Under Different Loads",
        "xlabel": "Performance Score",
        "ylabel": "Frequency",
        "additional_options": {"bins": 30, "overlay": True, "density": True},
    }

    print("Creating load testing histogram comparison...")
    load_stats = chart_gen.create_comparison_chart(load_test_config)
    chart_gen.show()
    chart_gen.save("load_test_histogram.png")
    chart_gen.clear()

    # Print comprehensive statistics
    print("\n" + "=" * 80)
    print("COMPREHENSIVE ANALYSIS RESULTS")
    print("=" * 80)

    print("\n1. LATENCY COMPARISON (3 Systems):")
    if "performance_comparisons" in stats:
        for comparison, data in stats["performance_comparisons"].items():
            improvement = data["improvement_percentage"]
            status = "BETTER" if data["is_better"] else "WORSE"
            print(f"   {comparison}: {improvement:+.1f}% ({status})")

    print("\n2. THROUGHPUT COMPARISON (5 Algorithms):")
    for algo, algo_stats in throughput_stats.items():
        if algo != "statistical_tests" and algo != "performance_comparisons":
            print(
                f"   {algo}: {algo_stats['mean']:.0f} ± {algo_stats['std']:.0f} req/sec"
            )

    print("\n3. STATISTICAL SIGNIFICANCE:")
    if "statistical_tests" in stats:
        if "anova" in stats["statistical_tests"]:
            p_val = stats["statistical_tests"]["anova"]["p_value"]
            sig = "SIGNIFICANT" if p_val < 0.05 else "NOT SIGNIFICANT"
            print(f"   ANOVA p-value: {p_val:.6f} ({sig})")

    # Example 6: Custom configuration from JSON file/string
    json_config = """
    {
        "chart_type": "dashboard",
        "data": {
            "Production": [95.2, 94.8, 95.5, 94.9, 95.1],
            "Staging": [93.1, 92.8, 93.5, 92.9, 93.2],
            "Development": [88.5, 87.9, 89.1, 88.2, 88.8]
        },
        "title": "System Availability Comparison",
        "xlabel": "Monitoring Periods",
        "ylabel": "Availability (%)",
        "metric_name": "Availability",
        "colors": ["#27ae60", "#f39c12", "#e74c3c"],
        "show_statistics": true,
        "figsize": [15, 10]
    }
    """

    print("\nCreating system availability comparison from JSON...")
    availability_config = json.loads(json_config)
    availability_stats = chart_gen.create_comparison_chart(availability_config)
    chart_gen.show()
    chart_gen.save("availability_comparison.png")
    chart_gen.clear()

    # Batch creation example
    batch_configs = [
        {
            "chart_type": "bar",
            "data": {
                "Q1": [100, 110, 105],
                "Q2": [120, 125, 115],
                "Q3": [130, 135, 125],
                "Q4": [140, 145, 135],
            },
            "labels": ["Product A", "Product B", "Product C"],
            "title": "Quarterly Sales Comparison",
            "ylabel": "Sales ($K)",
            "save_filename": "quarterly_sales.png",
        },
        {
            "chart_type": "line",
            "data": {
                "Server 1": [85, 87, 83, 89, 86],
                "Server 2": [92, 94, 90, 95, 93],
                "Server 3": [78, 80, 76, 82, 79],
            },
            "title": "Server Performance Trends",
            "ylabel": "Performance Score",
            "save_filename": "server_performance.png",
        },
    ]

    chart_gen = ChartGenerator()
    batch_results = batch_create_charts(chart_gen, batch_configs)

    print("\nBatch processing completed!")
    print(f"Created {len(batch_results)} charts with statistical analysis.")
