"""
Analytics Service using Pandas and Matplotlib
Provides data aggregation, sales performance metrics, and chart generation.
"""

import io
import base64
import os
import matplotlib
# Use non-GUI Agg backend for thread-safe web server image rendering
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


class SalesAnalytics:
    """Performs data analysis using Pandas and generates charts using Matplotlib."""

    def __init__(self, sales_file: str, inventory_file: str):
        self.sales_file = sales_file
        self.inventory_file = inventory_file

    def get_sales_dataframe(self) -> pd.DataFrame:
        """Loads sales data from CSV into a Pandas DataFrame with proper type conversions."""
        if not os.path.exists(self.sales_file) or os.path.getsize(self.sales_file) == 0:
            return pd.DataFrame(columns=[
                "sale_id", "timestamp", "customer_name", "payment_method",
                "product_id", "product_name", "category", "unit_price",
                "quantity", "subtotal", "tax_amount", "total_amount"
            ])

        try:
            df = pd.read_csv(self.sales_file)
            if df.empty:
                return df

            # Cast data types
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).astype(int)
            df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
            df["subtotal"] = pd.to_numeric(df["subtotal"], errors="coerce").fillna(0.0)
            df["tax_amount"] = pd.to_numeric(df["tax_amount"], errors="coerce").fillna(0.0)
            df["total_amount"] = pd.to_numeric(df["total_amount"], errors="coerce").fillna(0.0)

            # Parse datetime
            df["timestamp_dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df["year_month"] = df["timestamp_dt"].dt.strftime("%Y-%m")
            df["date"] = df["timestamp_dt"].dt.strftime("%Y-%m-%d")

            return df
        except Exception as e:
            print(f"[Analytics Error] Failed reading sales data: {e}")
            return pd.DataFrame()

    def get_analysis_summary(self) -> dict:
        """
        Uses Pandas to calculate key statistical indicators and summary metrics.
        """
        df = self.get_sales_dataframe()
        if df.empty:
            return {
                "total_revenue": 0.0,
                "total_orders": 0,
                "total_units_sold": 0,
                "average_order_value": 0.0,
                "top_product": "N/A",
                "top_category": "N/A",
                "product_stats": [],
                "category_stats": [],
                "monthly_stats": []
            }

        # Unique orders aggregation
        order_grouped = df.groupby("sale_id")["total_amount"].sum()
        total_revenue = float(df["total_amount"].sum())
        total_orders = int(df["sale_id"].nunique())
        total_units = int(df["quantity"].sum())
        avg_order_value = float(order_grouped.mean()) if not order_grouped.empty else 0.0

        # Product-wise aggregation
        prod_agg = df.groupby(["product_id", "product_name", "category"]).agg(
            total_units=("quantity", "sum"),
            total_revenue=("total_amount", "sum")
        ).reset_index().sort_values(by="total_revenue", ascending=False)

        top_product = prod_agg.iloc[0]["product_name"] if not prod_agg.empty else "N/A"

        # Category-wise aggregation
        cat_agg = df.groupby("category").agg(
            total_units=("quantity", "sum"),
            total_revenue=("total_amount", "sum")
        ).reset_index().sort_values(by="total_revenue", ascending=False)

        top_category = cat_agg.iloc[0]["category"] if not cat_agg.empty else "N/A"

        # Monthly aggregation
        monthly_agg = df.dropna(subset=["year_month"]).groupby("year_month").agg(
            total_revenue=("total_amount", "sum"),
            total_units=("quantity", "sum"),
            order_count=("sale_id", "nunique")
        ).reset_index().sort_values(by="year_month")

        return {
            "total_revenue": round(total_revenue, 2),
            "total_orders": total_orders,
            "total_units_sold": total_units,
            "average_order_value": round(avg_order_value, 2),
            "top_product": top_product,
            "top_category": top_category,
            "product_stats": prod_agg.to_dict(orient="records"),
            "category_stats": cat_agg.to_dict(orient="records"),
            "monthly_stats": monthly_agg.to_dict(orient="records")
        }

    # ---------------- Matplotlib Chart Generation ----------------

    def _fig_to_base64(self, fig) -> str:
        """Converts a matplotlib figure to base64 encoded PNG image."""
        buffer = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        buffer.seek(0)
        img_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        plt.close(fig)
        return f"data:image/png;base64,{img_b64}"

    def generate_product_sales_chart(self) -> str:
        """
        Generates Product-wise sales graph using Matplotlib.
        Compares revenue and units sold across top products.
        """
        df = self.get_sales_dataframe()
        fig, ax = plt.subplots(figsize=(9, 4.8), facecolor="#0f172a")
        ax.set_facecolor("#1e293b")

        if df.empty:
            ax.text(0.5, 0.5, "No Sales Recorded Yet", color="#94a3b8", fontsize=14, ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return self._fig_to_base64(fig)

        # Aggregate top 8 products by revenue
        prod_data = df.groupby("product_name")["total_amount"].sum().reset_index()
        prod_data = prod_data.sort_values(by="total_amount", ascending=True).tail(8)

        # Color palette
        colors = plt.cm.viridis(np.linspace(0.4, 0.85, len(prod_data)))

        bars = ax.barh(prod_data["product_name"], prod_data["total_amount"], color=colors, height=0.6, edgecolor="#38bdf8", linewidth=0.8)

        # Annotations
        for bar in bars:
            width = bar.get_width()
            ax.text(width + (prod_data["total_amount"].max() * 0.02), bar.get_y() + bar.get_height()/2,
                    f"${width:,.2f}",
                    va='center', ha='left', color='#f8fafc', fontsize=9, fontweight='bold')

        ax.set_title("Product-Wise Revenue Distribution ($)", color="#f8fafc", fontsize=13, fontweight="bold", pad=12)
        ax.set_xlabel("Total Sales Revenue ($)", color="#94a3b8", fontsize=10, labelpad=8)
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        ax.grid(axis='x', color="#334155", linestyle="--", alpha=0.7)

        # Style borders
        for spine in ax.spines.values():
            spine.set_color("#334155")

        return self._fig_to_base64(fig)

    def generate_category_sales_chart(self) -> str:
        """
        Generates Category-wise sales graph using Matplotlib.
        Visualizes revenue contribution of each product category.
        """
        df = self.get_sales_dataframe()
        fig, ax = plt.subplots(figsize=(8, 4.8), facecolor="#0f172a")
        ax.set_facecolor("#1e293b")

        if df.empty:
            ax.text(0.5, 0.5, "No Category Sales Recorded Yet", color="#94a3b8", fontsize=14, ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return self._fig_to_base64(fig)

        cat_data = df.groupby("category")["total_amount"].sum().reset_index()
        cat_data = cat_data.sort_values(by="total_amount", ascending=False)

        # Aesthetic donut chart
        theme_colors = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6", "#14b8a6"]
        colors = theme_colors[:len(cat_data)]

        wedges, texts, autotexts = ax.pie(
            cat_data["total_amount"],
            labels=cat_data["category"],
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            pctdistance=0.75,
            textprops=dict(color="#f8fafc", fontsize=9, fontweight="bold"),
            wedgeprops=dict(width=0.45, edgecolor="#0f172a", linewidth=2)
        )

        for autotext in autotexts:
            autotext.set_color("#ffffff")
            autotext.set_fontsize(9)

        ax.set_title("Category-Wise Sales Contribution", color="#f8fafc", fontsize=13, fontweight="bold", pad=12)

        return self._fig_to_base64(fig)

    def generate_monthly_sales_chart(self) -> str:
        """
        Generates Monthly sales graph using Matplotlib.
        Displays monthly revenue trend over time.
        """
        df = self.get_sales_dataframe()
        fig, ax = plt.subplots(figsize=(9, 4.8), facecolor="#0f172a")
        ax.set_facecolor("#1e293b")

        if df.empty or df["year_month"].isna().all():
            ax.text(0.5, 0.5, "No Monthly Data Available Yet", color="#94a3b8", fontsize=14, ha="center", va="center")
            ax.set_xticks([])
            ax.set_yticks([])
            return self._fig_to_base64(fig)

        month_data = df.dropna(subset=["year_month"]).groupby("year_month")["total_amount"].sum().reset_index()
        month_data = month_data.sort_values(by="year_month")

        months = month_data["year_month"].astype(str).tolist()
        revenues = month_data["total_amount"].tolist()

        # Plot line + area
        ax.plot(months, revenues, marker="o", markersize=8, color="#38bdf8", linewidth=2.5, label="Monthly Revenue ($)")
        ax.fill_between(months, revenues, color="#38bdf8", alpha=0.2)

        # Add data point labels
        for x, y in zip(months, revenues):
            ax.annotate(f"${y:,.0f}", (x, y), textcoords="offset points", xytext=(0, 10),
                        ha="center", color="#f8fafc", fontsize=9, fontweight="bold")

        ax.set_title("Monthly Sales Revenue Trend", color="#f8fafc", fontsize=13, fontweight="bold", pad=12)
        ax.set_ylabel("Revenue ($)", color="#94a3b8", fontsize=10, labelpad=8)
        ax.tick_params(colors="#cbd5e1", labelsize=9)
        ax.grid(True, color="#334155", linestyle="--", alpha=0.7)

        for spine in ax.spines.values():
            spine.set_color("#334155")

        if len(months) > 1:
            ax.set_ylim(bottom=0, top=max(revenues) * 1.25)

        return self._fig_to_base64(fig)

    def generate_all_charts(self) -> dict:
        """Returns all three required Matplotlib graphs encoded as base64."""
        return {
            "product_chart": self.generate_product_sales_chart(),
            "category_chart": self.generate_category_sales_chart(),
            "monthly_chart": self.generate_monthly_sales_chart()
        }
