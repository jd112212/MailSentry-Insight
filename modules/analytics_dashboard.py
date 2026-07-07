import os
import pandas as pd
import matplotlib
# Prevent GUI rendering errors by using the non-interactive Agg backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    """
    Aggregates metrics from local CSV files and renders static analytical charts (PNG) to output/.
    Also computes summaries to serve the web API.
    """
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.emails_path = os.path.join(self.output_dir, "processed_emails.csv")
        self.entities_path = os.path.join(self.output_dir, "extracted_entities.csv")

    def generate_metrics_and_charts(self) -> Dict[str, Any]:
        """
        Generates and saves three PNG charts:
        - category_distribution.png (Pie)
        - daily_volume.png (Line)
        - top_senders.png (Bar)
        Returns the data dictionary of aggregated metrics.
        """
        metrics = {
            "total_emails": 0,
            "lead_count": 0,
            "invoice_count": 0,
            "spam_rate": 0.0,
            "category_distribution": {},
            "daily_volume": {},
            "top_senders": {},
            "avg_body_length_per_category": {},
            "category_trend": {},
            "hourly_activity": {}
        }

        if not os.path.exists(self.emails_path):
            logger.warning(f"No processed emails CSV file at {self.emails_path}. Analytics generation skipped.")
            return metrics

        try:
            df = pd.read_csv(self.emails_path)
            if df.empty:
                logger.info("Emails CSV is empty. Returning default metrics.")
                return metrics

            metrics["total_emails"] = len(df)

            # Category count aggregation
            cat_counts = df["category"].value_counts()
            metrics["category_distribution"] = cat_counts.to_dict()
            metrics["lead_count"] = int(cat_counts.get("Sales Lead", 0))
            metrics["invoice_count"] = int(cat_counts.get("Invoice", 0))
            spam_count = int(cat_counts.get("Spam", 0))
            metrics["spam_rate"] = round((spam_count / len(df)) * 100, 1) if len(df) > 0 else 0.0

            # Top senders aggregation
            sender_counts = df["sender"].value_counts()
            metrics["top_senders"] = sender_counts.head(5).to_dict()

            # Daily email volume aggregation
            # Clean and parse date string to extract just the date YYYY-MM-DD
            df['parsed_date'] = pd.to_datetime(df['date'], errors='coerce', utc=True)
            df['date_only'] = df['parsed_date'].dt.strftime('%Y-%m-%d')
            df['date_only'] = df['date_only'].fillna("Unknown/Other")

            daily_counts = df['date_only'].value_counts().sort_index()
            metrics["daily_volume"] = daily_counts.to_dict()

            # Hourly activity aggregation (0-23)
            df['hour'] = df['parsed_date'].dt.hour.fillna(-1).astype(int)
            hour_counts = df[df['hour'] >= 0]['hour'].value_counts().sort_index()
            metrics["hourly_activity"] = {str(h): int(c) for h, c in hour_counts.items()}

            # Average body length per category
            if 'body_preview' in df.columns:
                avg_len = df.groupby('category')['body_preview'].apply(lambda x: int(x.str.len().mean()))
                metrics["avg_body_length_per_category"] = avg_len.to_dict()

            # Category trend over time (count per category per date)
            if 'category' in df.columns and 'date_only' in df.columns:
                trend_df = df.groupby(['date_only', 'category']).size().unstack(fill_value=0)
                metrics["category_trend"] = {col: trend_df[col].to_dict() for col in trend_df.columns}

            # Ensure the output directory exists
            os.makedirs(self.output_dir, exist_ok=True)

            # Palette for graphs
            colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

            # Chart 1: Category Distribution (Pie)
            plt.figure(figsize=(6, 5))
            if not cat_counts.empty:
                plt.pie(
                    cat_counts.values,
                    labels=cat_counts.index,
                    autopct='%1.1f%%',
                    startangle=140,
                    colors=colors[:len(cat_counts)]
                )
            plt.title("Email Category Distribution", fontsize=14, fontweight='bold', pad=15)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "category_distribution.png"), dpi=150)
            plt.close()

            # Chart 2: Emails Per Day (Line Graph)
            plt.figure(figsize=(8, 4))
            if not daily_counts.empty:
                plt.plot(
                    daily_counts.index,
                    daily_counts.values,
                    marker='o',
                    color='#3b82f6',
                    linewidth=2,
                    markersize=6
                )
            plt.title("Email Daily Volume", fontsize=14, fontweight='bold', pad=15)
            plt.xlabel("Date", fontsize=10)
            plt.ylabel("Count", fontsize=10)
            plt.xticks(rotation=30, ha='right')
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "daily_volume.png"), dpi=150)
            plt.close()

            # Chart 3: Top 5 Senders (Bar Chart)
            plt.figure(figsize=(8, 4))
            top_5 = sender_counts.head(5)
            if not top_5.empty:
                # Truncate sender names for display labels
                short_labels = [label[:20] + "..." if len(label) > 20 else label for label in top_5.index]
                plt.bar(short_labels, top_5.values, color='#8b5cf6', width=0.6)
            plt.title("Top 5 Senders", fontsize=14, fontweight='bold', pad=15)
            plt.xlabel("Sender", fontsize=10)
            plt.ylabel("Emails Count", fontsize=10)
            plt.xticks(rotation=15, ha='right')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "top_senders.png"), dpi=150)
            plt.close()

            # ----------------------------------------------------------------
            # Chart 4: Spam Rate Gauge
            # ----------------------------------------------------------------
            spam_rate = metrics["spam_rate"]
            fig, ax = plt.subplots(figsize=(5, 3), subplot_kw={'aspect': 'equal'})
            fig.patch.set_facecolor('#1a1f2e')
            ax.set_facecolor('#1a1f2e')

            # Draw gauge arc background (grey) and value arc (color)
            import numpy as np
            theta_start = 180  # degrees
            theta_end = 0
            total_angle = 180
            filled_angle = (spam_rate / 100) * total_angle

            # Determine color based on rate
            gauge_color = '#10b981' if spam_rate < 20 else ('#f59e0b' if spam_rate < 50 else '#ef4444')

            bg_angles = np.linspace(np.radians(0), np.radians(180), 200)
            ax.plot(np.cos(bg_angles), np.sin(bg_angles), color='#2d3748', linewidth=20, solid_capstyle='round')

            fill_angles = np.linspace(np.radians(180), np.radians(180 - filled_angle), 200)
            ax.plot(np.cos(fill_angles), np.sin(fill_angles), color=gauge_color, linewidth=20, solid_capstyle='round')

            ax.text(0, -0.1, f"{spam_rate}%", ha='center', va='center', fontsize=26,
                    fontweight='bold', color='white', fontfamily='DejaVu Sans')
            ax.text(0, -0.45, "Spam Rate", ha='center', va='center', fontsize=11,
                    color='#9ca3af', fontfamily='DejaVu Sans')

            ax.set_xlim(-1.4, 1.4)
            ax.set_ylim(-0.7, 1.2)
            ax.axis('off')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "spam_rate_gauge.png"), dpi=150, facecolor='#1a1f2e')
            plt.close()

            # ----------------------------------------------------------------
            # Chart 5: Average Email Body Length per Category (Bar)
            # ----------------------------------------------------------------
            avg_len_data = metrics["avg_body_length_per_category"]
            if avg_len_data:
                fig, ax = plt.subplots(figsize=(8, 4))
                fig.patch.set_facecolor('#1a1f2e')
                ax.set_facecolor('#1a1f2e')
                cats = list(avg_len_data.keys())
                lens = list(avg_len_data.values())
                bar_colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
                ax.bar(cats, lens, color=bar_colors[:len(cats)], width=0.5)
                ax.set_title("Avg Email Body Length per Category", fontsize=14,
                             fontweight='bold', pad=15, color='white')
                ax.set_xlabel("Category", fontsize=10, color='#9ca3af')
                ax.set_ylabel("Avg Characters", fontsize=10, color='#9ca3af')
                ax.tick_params(colors='#9ca3af', rotation=15)
                ax.spines[:].set_color('#2d3748')
                ax.grid(axis='y', linestyle='--', alpha=0.3, color='#4b5563')
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, "avg_body_length.png"), dpi=150, facecolor='#1a1f2e')
                plt.close()

            # ----------------------------------------------------------------
            # Chart 6: Category Trend Over Time (Multi-line)
            # ----------------------------------------------------------------
            trend_data = metrics["category_trend"]
            if trend_data:
                fig, ax = plt.subplots(figsize=(10, 4))
                fig.patch.set_facecolor('#1a1f2e')
                ax.set_facecolor('#1a1f2e')
                line_colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
                all_dates = sorted({d for cat_dict in trend_data.values() for d in cat_dict.keys()})
                for idx, (cat, date_counts) in enumerate(trend_data.items()):
                    values = [date_counts.get(d, 0) for d in all_dates]
                    ax.plot(all_dates, values, marker='o', label=cat,
                            color=line_colors[idx % len(line_colors)], linewidth=2, markersize=5)
                ax.set_title("Category Trend Over Time", fontsize=14, fontweight='bold', pad=15, color='white')
                ax.set_xlabel("Date", fontsize=10, color='#9ca3af')
                ax.set_ylabel("Email Count", fontsize=10, color='#9ca3af')
                ax.tick_params(colors='#9ca3af', rotation=30)
                ax.spines[:].set_color('#2d3748')
                ax.grid(linestyle='--', alpha=0.3, color='#4b5563')
                ax.legend(fontsize=9, labelcolor='#9ca3af', facecolor='#1a1f2e', edgecolor='#2d3748')
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, "category_trend.png"), dpi=150, facecolor='#1a1f2e')
                plt.close()

            # ----------------------------------------------------------------
            # Chart 7: Hourly Email Activity Heatmap
            # ----------------------------------------------------------------
            hourly_data = metrics["hourly_activity"]
            if hourly_data:
                import numpy as np
                fig, ax = plt.subplots(figsize=(10, 2.5))
                fig.patch.set_facecolor('#1a1f2e')
                ax.set_facecolor('#1a1f2e')

                hours = list(range(24))
                counts = [hourly_data.get(str(h), 0) for h in hours]
                # Reshape into 1×24 heatmap matrix
                data_matrix = np.array(counts).reshape(1, 24)

                im = ax.imshow(data_matrix, aspect='auto', cmap='Blues',
                               interpolation='nearest', vmin=0)
                ax.set_xticks(range(24))
                ax.set_xticklabels([f"{h:02d}:00" for h in hours], rotation=45,
                                   ha='right', fontsize=8, color='#9ca3af')
                ax.set_yticks([])
                ax.set_title("Hourly Email Activity Heatmap", fontsize=14,
                             fontweight='bold', pad=15, color='white')
                ax.spines[:].set_color('#2d3748')

                # Annotate count on each cell
                for h in range(24):
                    ax.text(h, 0, str(counts[h]), ha='center', va='center',
                            fontsize=8, color='white' if counts[h] > max(counts, default=1) * 0.5 else '#9ca3af')

                plt.colorbar(im, ax=ax, orientation='vertical', pad=0.02, shrink=0.8)
                plt.tight_layout()
                plt.savefig(os.path.join(self.output_dir, "hourly_heatmap.png"), dpi=150, facecolor='#1a1f2e')
                plt.close()

            logger.info("Successfully generated analytics graphs in output directory.")

        except Exception as e:
            logger.error(f"Failed to generate analytics dashboard metrics/graphs: {e}")

        return metrics
